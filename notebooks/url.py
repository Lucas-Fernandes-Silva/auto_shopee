import requests

API_KEY = "AIzaSyCReSBWT3XKO8M0g6C1NtJcQFtuRnApYQA"
CX = "532347d8c03cc4861"
query = "gato siamês"

url = "https://www.googleapis.com/customsearch/v1"
params = {
    "q": query,
    "cx": CX,
    "key": API_KEY,
    "searchType": "image",
    "num": 3
}

res = requests.get(url, params=params)

data = res.json()
print(data.keys())
for item in data.get("items", []):
    print(item["link"])
