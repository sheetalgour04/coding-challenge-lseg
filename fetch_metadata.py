#!/usr/bin/env python3
import requests
import json
import sys
import logging

BASE_URL = "http://169.254.169.254/latest"

def get_token():
    """Fetch IMDSv2 token"""
    try:
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
        resp = requests.get(url, headers=headers, timeout=2)
        resp.raise_for_status()
    except Exception as e:
        return f"Error: {e}"

    text = resp.text.strip()

    # If response has multiple lines → iterate
    if "\n" in text or text.endswith("/"):
        data = {}
        for item in text.splitlines():
            item = item.strip()
            if item.endswith("/"):  # directory → recurse
                key = item.rstrip("/")
                data[key] = fetch_metadata(f"{path}{item}", token)
            else:  # leaf node
                data[item] = fetch_metadata(f"{path}{item}", token)
        return data
    else:
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
            if k == search_key:
                return v
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
    """Recursively fetch metadata keys/values"""
    url = f"{BASE_URL}/{url}"
    headers = {"X-aws-ec2-metadata-token": token} if token else {}

    try:
        resp = requests.get(url, headers=headers, timeout=2)
        resp.raise_for_status()
    except Exception as e:
        return f"Error: {e}"

    
    text = resp.text.strip()
    
    return text


if __name__ == "__main__":
    token = get_token()

    # Fetch full metadata & identity doc
    metadata = fetch_metadata("", token)
    identity_doc = fetch_identity(token)
    combined_json = {
        "meta-data": metadata,
        "dynamic": identity_doc
        }

    # Check if user provided a key to search
    if len(sys.argv) > 1 and sys.argv[1] != "":
      #  fetch_key = sys.argv[1].replace(".", "/")
        fetch_key = sys.argv[1]
        fetch_key = fetch_key.split('.')
        last_key = fetch_key[-1]
        
        if len(fetch_key) > 1:
            
            dynamic_fetch_url = '/dynamic/instance-identity/document' if fetch_key[0] == "dynamic" else "" 

            fetch_key = '/'.join(fetch_key)
            if dynamic_fetch_url != "":
              value = fetch_url(dynamic_fetch_url)
            else:
              value = fetch_url(fetch_key)
            output = {fetch_key: value}
            print("NOTE: If the intended result is not published better try only single key instead of full path")
        else:
            value = find_key_in_json(combined_json, last_key)
            output = {last_key: value}
        #last_key = fetch_key[-1]
        logging.info(f"Searching for key: {fetch_key} in combined JSON")
        

        # Always use find_key_in_json for any key
#        value = find_key_in_json(combined_json, last_key)
        if value is None:
            logging.warning(f"Key '{fetch_key}' not found in metadata or dynamic document")
    else:
        logging.info("No specific key provided. Fetching full metadata")
        output = combined_json

    # Save JSON to file
    output_file = "/tmp/instance_metadata.json"
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
        logging.info(f"Metadata saved to {output_file}")

    # Print to stdout as well
    print(json.dumps(output, indent=2))