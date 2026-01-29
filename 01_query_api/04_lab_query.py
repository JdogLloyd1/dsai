# 04_lab_query.py
# Query the MBTA API for Lab 1
# Design a query returning 10-20 rows and document the results
# Jonathan Lloyd 

# Load environment variables from .env file
import os  # for reading environment variables
import requests  # for making HTTP requests
from dotenv import load_dotenv  # for loading variables from .env

load_dotenv(".env")

MBTA_API_KEY = os.getenv("MBTA_API_KEY")

# Query Plan #########################################################
# ADD PLAN HERE


# Query Implementation #################################################
response = requests.get(
    "https://api-v3.mbta.com/vehicles",
    headers={"x-api-key": MBTA_API_KEY},
    # ADD PARAMETERS HERE
    # params={"filter[route]": "Red"},
)


# Inspect Response #####################################################
print("Status code: ", response.status_code, "\n")
print("Response: ", response.json())


# Document Results #####################################################
print("Number of records: ", len(response.json()["data"]))
print("Key fields: ", response.json()["data"][0].keys())
print("Data structure: ", response.json()["data"][0])


# Clear Environment #####################################################
globals().clear()