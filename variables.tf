variable "instance_name" {
  default = "Coding-challenge-instance"
}

variable "instance_type" {
  default =  "t3.micro"
}
variable "key_name" {
  default = "coding-challenge-instance-key"
}

variable "fetch_key" {
  description = "Specific EC2 metadata key to fetch. Leave empty for all metadata."
  type        = string
  default     = ""
}