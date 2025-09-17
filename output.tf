output "instance_public_ip" {
  value = aws_instance.test_instance.public_ip
}

# output "instance_hostname_from_script" {
#   value = jsondecode(data.local_file.hostname.content)["hostname"]
# }

output "instance_metadata" {
  description = "AWS EC2 metadata content"
  value       = "The output is saved in instance_data.json file in same directory"
}
