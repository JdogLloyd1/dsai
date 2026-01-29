# 03_mbta_api_test.py
# Test the MBTA API
# Jonathan Lloyd 

# Load environment variables from .env file
import os  # for reading environment variables
import requests  # for making HTTP requests
from dotenv import load_dotenv  # for loading variables from .env

load_dotenv(".env")

MBTA_API_KEY = os.getenv("MBTA_API_KEY")

# Execute query and save response as object
response = requests.get(
    "https://api-v3.mbta.com/vehicles",
    headers={"x-api-key": MBTA_API_KEY},
    params={"filter[route]": "Red"},
)

# View response status code (200 = success)
print("Status code: ", response.status_code, "\n")

# Extract the response as JSON and print
print("Response: ", response.json())


# Clear environment (optional in short scripts, but shown for parity
# with the R example that clears its workspace)
globals().clear()