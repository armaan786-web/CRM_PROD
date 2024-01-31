# from django.test import TestCase

# number = 9973884727
# last_three_digits = str(number)[-3:]
# print("hello", last_three_digits)

#

# Create your tests here.


import requests

url = "https://back.theskytrails.com/skyTrails/international/getAll"

response = requests.get(url)

if response.status_code == 200:
    # The API call was successful, and you can access the data using response.json()
    data = response.json()
    print(data)
else:
    # The API call failed, and you can print the status code and any error message
    print(f"Error: {response.status_code}, {response.text}")
