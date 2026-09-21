import requests

url = "https://web.triniumtech.com/fpas/tnet/web/api/login"

response = requests.post(
    url,
    auth=("API24097", "Trucknet@ap1")
)

print(response.status_code)
print(response.text)

# ---------- NUEVO: transactions ----------
token = response.json()["token"]

url_tx = "https://web.triniumtech.com/fpas/tnet/web/api/transactions"

response_tx = requests.get(
    url_tx,
    headers={"Authorization": f"Bearer {token}"}
)

print(response_tx.status_code)
print(response_tx.text[:2000])