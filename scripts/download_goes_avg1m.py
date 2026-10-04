import re, pathlib, requests

BASE = ("https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/"
        "goes/goes19/l2/data/xrsf-l2-avg1m_science")
OUT = pathlib.Path("data/raw/goes/avg1m")
OUT.mkdir(parents=True, exist_ok=True)

for month in ["07", "08", "09"]:
    url = f"{BASE}/2026/{month}/"
    html = requests.get(url, timeout=60).text
    for name in sorted(set(re.findall(r'href="([^"]+\.nc)"', html))):
        dest = OUT / name
        if dest.exists():
            continue
        r = requests.get(url + name, timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)
        print("saved", name)