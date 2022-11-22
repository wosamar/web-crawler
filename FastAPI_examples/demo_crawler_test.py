import requests
from pprint import pprint

# url = "http://127.0.0.1:8000/items/posts"

# body = {
#     'title': '很棒的房間',
#     'size': '1000',
#     'floor': '13',
#     'area': '大安'
# }
# r = requests.post(url=url, json=body)
# print(r.text)
# pprint(r.json())

url = "http://127.0.0.1:5049/ID"
r = requests.post(url=url)
print(r.text)