# Terraform EC2 with Dynamic Key Pair

This project demonstrates how to:

* Create an **AWS EC2 instance** using Terraform
* Fetch metadata or execute scripts on the instance
* Run a Python script to query **EC2 instance metadata and dynamic instance identity document (IMDSv2)**

---

### 📌 Note on Terraform Modules
I have **not used the `terraform` block with modules** in this implementation.  
This is intentional because the task needed to be **self-contained and easily executable** without requiring external module dependencies.  

- Keeps the setup simple and portable for quick testing.  
- Avoids version mismatch or remote module availability issues.  

👉 In a production-grade setup, I would normally use modules for **reusability, maintainability, and consistency** across environments.  

---

## Prerequisites

* [Terraform](https://www.terraform.io/downloads)
* [AWS CLI](https://aws.amazon.com/cli/)
* AWS account with proper IAM permissions

---

## Steps to Run

### 1. Initialize Terraform

```bash
terraform init
```

### 2. Plan the Infrastructure

```bash
terraform plan
```

Check what Terraform will create before applying.

### 3. Apply Terraform

```bash
terraform apply
```

* Terraform will create:
  * TLS private key
  * AWS key pair
  * EC2 instance
  * Local file with PEM key
  * Null resources which will execute the python script to fetch metadata based on `TFVAR = fetch_key`

`Note: To fetch new content, update the TF variable fetch_key in the command-line and re-apply.`

```bash

# default value is "" for fetch_key
terraform apply -var=fetch_key=

# pass single key in fetch_key to fetch the data for that particular key-value
terraform apply -var=fetch_key='network'

# pass fullpath in fetch_key to fetch all data till that path
terraform apply -var=fetch_key='meta-data.block-device-mapping.ami'
```

### 4. See the content of JSON file generated

```bash
cat instance_data.json
```

### 5. Destroy Infrastructure

```bash
terraform destroy
```

* Cleans up all resources created by Terraform.
* Remove sensitive files if necessary.

---

## Alternate way to execute the Python script

### 1. SSH into the Instance

```bash
ssh -i my-ec2-key.pem ubuntu@<instance-public-ip>
```

### 2. Run the Python Metadata Script

The Python script `fetch_metadata.py` does the following:

* Fetches **IMDSv2 token** from the instance metadata service.
* Recursively retrieves all **EC2 metadata** (`meta-data`) and the **dynamic instance identity document** (`dynamic`).
* Allows fetching a **specific key** using command-line arguments.
* Saves the output to `/tmp/instance_metadata.json` and prints it to stdout.

#### Example Usage:

```bash
cd /tmp

# Fetch full metadata and identity document
python3 fetch_metadata.py

# Fetch a specific key (e.g., instance-id)
python3 fetch_metadata.py instance-id

# Fetch a key from dynamic identity document
python3 fetch_metadata.py dynamic.accountId

# Fetch a key by giving full path
python3 fetch_metadata.py
```

---

## Notes

* The **PEM private key** is saved locally as `my-ec2-key.pem`.
* Ensure your **security group allows SSH (port 22)** from your machine.
* Use **null_resource** and `remote-exec` to run scripts automatically on the EC2 instance.
* Terraform state files (`*.tfstate`) should **not be committed** to Git. Use `.gitignore`.

---

## References

* [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
* [TLS Provider](https://registry.terraform.io/providers/hashicorp/tls/latest/docs)
* [AWS EC2 Key Pairs](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-key-pairs.html)
* [EC2 Instance Metadata Service (IMDSv2)](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-service.html)
