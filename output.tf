output "instance_public_ip" {
  value = aws_instance.test_instance.public_ip
}

output "instance_metadata" {
  description = "AWS EC2 metadata content"
  value       = "The output is saved in instance_data.json file in same directory"
}
