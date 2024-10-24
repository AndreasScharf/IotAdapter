import json
import sys

# Check if the script received the new value as an argument
if len(sys.argv) != 2:
    print("Usage: python3 update_json.py <new_value>")
    sys.exit(1)

# Get the new value from the command-line argument
new_value = sys.argv[1]

# Path to the JSON file
json_file_path = '/home/pi/Documents/IotAdapter/config.json'

# Load the JSON data from the file
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Traverse the JSON to find the correct object and modify it
for item in data['data']:
    if item.get('name') == 'MAD':
        item['value'] = new_value  # Set the new value

# Save the modified JSON back to the file
with open(json_file_path, 'w') as file:
    json.dump(data, file, indent=4)

print(f"JSON updated successfully! 'MAD' value is now: {new_value}")
