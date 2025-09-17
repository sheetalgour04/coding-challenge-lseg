# Generate a key pair
resource "tls_private_key" "my_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# It will create a local pem file for SSH
resource "local_file" "private_key_file" {
  content         = tls_private_key.my_key.private_key_pem
  filename        = "${path.module}/my-ec2-key.pem"
  file_permission = "0600"
}

# Generate a aws key-pair for EC2 instance SSH access
resource "aws_key_pair" "my_key" {
  key_name   = var.key_name
  public_key = tls_private_key.my_key.public_key_openssh
}