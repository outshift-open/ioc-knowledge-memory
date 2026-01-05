import json
import os
from cryptography.fernet import Fernet

# Generate a new encryption key
key = Fernet.generate_key()

# Create config.json with the DEK
config = {
    "DEK": key.decode()
}

# The config.json should be placed in src/server/config.json
# because main.py runs in that directory
config_path = "src/server/config.json"

# Check if config.json already exists
if os.path.exists(config_path):
    print(f"Config file already exists at {config_path}. Skipping creation.")
    with open(config_path, "r") as f:
        existing_config = json.load(f)
    print(f"Existing DEK: {existing_config.get('DEK')}")
else:
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(config_path), exist_ok=True)

    # Write the config file
    with open(config_path, "w") as f:
        json.dump(config, f)

    print(f"Data Encryption Key (DEK) generated and saved to {config_path}")
    print(f"DEK: {key.decode()}")
