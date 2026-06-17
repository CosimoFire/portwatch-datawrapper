import requests

DW_TOKEN = "imoQdzeGyCs4RSIKClfksVlyoL7B1HTLItDdT1vXqNSB87C5JR84TvLdsO0rhZeI"

r = requests.get(
    "https://api.datawrapper.de/v3/me",
    headers={"Authorization": f"Bearer {DW_TOKEN}"}
)
print(r.status_code)
print(r.json())
