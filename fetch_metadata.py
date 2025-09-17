#!/usr/bin/env python3
import requests
import json
import sys
import logging

# ---------------- HELP & USAGE STRINGS ----------------

HELP_TEXT = """
Usage:
  python3 fetch_metadata.py [key]

Options:
  Fetch all metadata and dynamic identity document
  Fetch a specific metadata key (e.g., instance-id)
  Fetch a key from dynamic identity document (e.g., dynamic.accountId)
  Fetch using full path (e.g., meta-data.placement.availability-zone)

Examples:
  # Fetch all metadata
  python3 fetch_metadata.py

  # Fetch instance ID
  python3 fetch_metadata.py instance-id

  # Fetch accountId from dynamic document
  python3 fetch_metadata.py accountId

  # Fetch using full path
  python3 fetch_metadata.py meta-data.public-ipv4
"""

def print_help():
    print(HELP_TEXT)
    sys.exit(0)

# ------------------------------------------------------

# Base URL for AWS Instance Metadata Service (IMDSv2)
BASE_URL = "http://169.254.169.254/latest"

def get_token():
    """Fetch IMDSv2 token"""
    try:
        # Request a session token with TTL of 6 hours (21600 seconds)
        resp = requests.put(
            f"{BASE_URL}/api/token",
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
            timeout=2,
        )
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"Failed to get token: {e}")
        return None


def fetch_metadata(path="", token=None):
    """Recursively fetch metadata keys/values"""
    url = f"{BASE_URL}/meta-data/{path}"
    headers = {"X-aws-ec2-metadata-token": token} if token else {}

    try:
        # Call IMDS for metadata
        resp = requests.get(url, headers=headers, timeout=2)
        resp.raise_for_status()
    except Exception as e:
        return f"Error: {e}"

    text = resp.text.strip()

    # If response contains multiple lines, treat it as a directory
    if "\n" in text or text.endswith("/"):
        data = {}
        for item in text.splitlines():
            item = item.strip()
            if item.endswith("/"):  # Directory → recurse further
                key = item.rstrip("/")
                data[key] = fetch_metadata(f"{path}{item}", token)
            else:  # Leaf node → fetch actual value
                data[item] = fetch_metadata(f"{path}{item}", token)
        return data
    else:
        # Single value → return directly
        return text


def fetch_identity(token=None):
    """Fetch dynamic instance identity document"""
    url = f"{BASE_URL}/dynamic/instance-identity/document"
    headers = {"X-aws-ec2-metadata-token": token} if token else {}
    try:
        resp = requests.get(url, headers=headers, timeout=2)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def find_key_in_json(json_obj, search_key):
    """
    Recursively search for a key in a JSON object.
    Returns the value if found, else None.
    """
    if isinstance(json_obj, dict):
        for k, v in json_obj.items():
            if k == search_key:  # Found the key
                return v
            # Recurse into nested structures
            result = find_key_in_json(v, search_key)
            if result is not None:
                return result
    elif isinstance(json_obj, list):
        for item in json_obj:
            result = find_key_in_json(item, search_key)
            if result is not None:
                return result
    return None


def fetch_url(url="", token=None):
    """Fetch any metadata/dynamic value using full path"""
    url = f"{BASE_URL}/{url}"
    headers = {"X-aws-ec2-metadata-token": token} if token else {}

    try:
        resp = requests.get(url, headers=headers, timeout=2)
        resp.raise_for_status()
    except Exception as e:
        return f"Error: {e}"

    # Return raw text result
    text = resp.text.strip()
    return text


if __name__ == "__main__":
    token = get_token()

    # Fetch both metadata and dynamic identity doc
    metadata = fetch_metadata("", token)
    identity_doc = fetch_identity(token)
    combined_json = {
        "meta-data": metadata,
        "dynamic": identity_doc
    }

    # If a specific key was provided as argument
    if len(sys.argv) > 1 and sys.argv[1] != "":

        fetch_key = sys.argv[1]
        fetch_key = fetch_key.split('.')  # Allow dot-notation keys
        last_key = fetch_key[-1]
        
        if len(fetch_key) > 1:
            # If user specifies "dynamic.*", fetch from identity document
            dynamic_fetch_url = '/dynamic/instance-identity/document' if fetch_key[0] == "dynamic" else "" 

            fetch_key = '/'.join(fetch_key)  # Build path string
            if dynamic_fetch_url != "":
                value = fetch_url(dynamic_fetch_url)
            else:
                value = fetch_url(fetch_key)
            output = {fetch_key: value}
            print("NOTE: If the intended result is not published, try only single key instead of full path")
        else:
            # Single key lookup across metadata + dynamic JSON
            value = find_key_in_json(combined_json, last_key)
            output = {last_key: value}

        logging.info(f"Searching for key: {fetch_key} in combined JSON")

        # If key not found, log warning
        if value is None:
            logging.warning(f"Key '{fetch_key}' not found in metadata or dynamic document")
    else:
        # If no argument, return full metadata JSON
        logging.info("No specific key provided. Fetching full metadata")
        output = combined_json

    # Save JSON output to file
    output_file = "/tmp/instance_metadata.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
        logging.info(f"Metadata saved to {output_file}")

    # Print output to console
    print(json.dumps(output, indent=2))