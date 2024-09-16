import requests

with open("proxies.txt", "r") as f:
    proxies = [line.strip() for line in f if line.strip()]

sites_to_check = [
    "https://app.aurory.io"
]

for counter, site in enumerate(sites_to_check):
    if counter >= len(proxies):
        print("Not enough proxies for the number of sites.")
        break

    proxy = proxies[counter]
    proxy_dict = {"http": proxy, "https": proxy}

    try:
        print(f"Using the proxy: {proxy}")
        res = requests.get(site, proxies=proxy_dict)
        print(f"Status code for {site}: {res.status_code}")
    except requests.RequestException as e:
        print(f"Failed to fetch {site} with proxy {proxy}: {e}")
