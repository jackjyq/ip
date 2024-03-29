import os

import requests

if __name__ == "__main__":
    print("downloading...")
    resp = requests.get(
        "https://github.com/lionsoul2014/ip2region/raw/master/data/ip2region.xdb"
    )
    resp.raise_for_status()

    folder = "./src/ip/data/ip2region"
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "ip2region.xdb"), "wb") as f:
        f.write(resp.content)
    print(f"download to {folder}")
