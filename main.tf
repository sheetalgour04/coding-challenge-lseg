# Fetch latest Ubuntu AMI
data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

# Generate a key pair
resource "tls_private_key" "my_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_file" "private_key_file" {
  content         = tls_private_key.my_key.private_key_pem
  filename        = "${path.module}/my-ec2-key.pem"
  file_permission = "0600"
}

resource "aws_key_pair" "my_key" {
  key_name   = var.key_name
  public_key = tls_private_key.my_key.public_key_openssh
}

# Security group allowing all traffic (can restrict later)
resource "aws_security_group" "allow_ssh" {
  name        = "allow-ssh"
  description = "Allow SSH inbound traffic"

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Create EC2 instance
resource "aws_instance" "test_instance" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.my_key.key_name
  vpc_security_group_ids = [aws_security_group.allow_ssh.id]

  tags = {
    Name = var.instance_name
  }
}

# Upload Python script to EC2
resource "null_resource" "upload_python_script" {
  depends_on = [aws_instance.test_instance]

  provisioner "file" {
    source      = "fetch_metadata.py"
    destination = "/tmp/fetch_metadata.py"

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = local_file.private_key_file.content
      host        = aws_instance.test_instance.public_ip
    }
  }
}

# Install Python and dependencies
resource "null_resource" "install_requirements" {
  depends_on = [null_resource.upload_python_script]

  provisioner "remote-exec" {
    inline = [
      "sudo apt-get update -y",
      "sudo apt-get install -y python3-pip python3-requests",
      "chmod +x /tmp/fetch_metadata.py"
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = local_file.private_key_file.content
      host        = aws_instance.test_instance.public_ip
    }
  }
  
}

# Fetch metadata from EC2
resource "null_resource" "fetch_metadata" {
  depends_on = [null_resource.install_requirements]

  triggers = {
    fetch_key = var.fetch_key
  }

  provisioner "remote-exec" {
    inline = [
      "python3 /tmp/fetch_metadata.py ${var.fetch_key} > /tmp/instance_data.json"
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = local_file.private_key_file.content
      host        = aws_instance.test_instance.public_ip
    }
  }

  provisioner "local-exec" {
    command = "scp -o StrictHostKeyChecking=no -i ${local_file.private_key_file.filename} ubuntu@${aws_instance.test_instance.public_ip}:/tmp/instance_data.json ./instance_data.json"
  }
}
