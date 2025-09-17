variable "instance_name" {
  description = "Name of the EC2 instance"
  type        = string
  default     = "Coding-challenge-instance"
}

variable "instance_type" {
  description = "Type of EC2 intstance"
  type        = string
  default     = "t3.micro"
}
variable "key_name" {
  description = "Key-pair name"
  type        = string
  default     = "coding-challenge-instance-key"
}

variable "fetch_key" {
  description = "Specific EC2 metadata key to fetch. Leave empty for all metadata."
  type        = string
  default     = ""
}