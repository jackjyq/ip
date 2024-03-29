import requests

if __name__ == "__main__":
    resp = requests.get(
        "https://github.com/lionsoul2014/ip2region/raw/master/data/ip2region.xdb"
    )
    resp.raise_for_status()

    with open("./src/ip/data/ip2region/ip2region.xdb", "wb") as f:
        f.write(resp.content)
    print(f"download to ./src/ip/data/ip2region/ip2region.xdb")
