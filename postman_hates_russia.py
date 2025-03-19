import requests

url = "http://127.0.0.1:8000/"

jwt_token = ""

data = {
  "first_name": "",
  "last_name": "",
  "image": ""
}

file_path = ""

files = {
    "image": ("", open(file_path, "rb"), "image/jpeg"),
}

headers = {
    "Authorization": f"Bearer {jwt_token}"
}

response = requests.put(url, data=data, files=files, headers=headers)

for file in files.values():
    file[1].close()

print("Status Code:", response.status_code)
print("Response JSON:", response.json)