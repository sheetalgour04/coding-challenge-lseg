
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
