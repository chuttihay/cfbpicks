import os
import requests

API_KEY = os.environ.get("CFBD_API_KEY", "").strip()
if not API_KEY:
    raise RuntimeError("Please set CFBD_API_KEY in your environment")

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

def fetch_all_records(year: int):
    url = "https://api.collegefootballdata.com/records"
    params = {"year": year}
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()

def main():
    year = 2024
    records = fetch_all_records(year)

    # Filter only FBS
    fbs = [r for r in records if r.get("classification") == "fbs"]

    print(f"Found {len(fbs)} FBS team records for {year}\n")
    for r in sorted(fbs, key=lambda x: x["team"]):
        team = r["team"]
        w, l, t = r["total"]["wins"], r["total"]["losses"], r["total"].get("ties", 0)
        cw, cl = r["conferenceGames"]["wins"], r["conferenceGames"]["losses"]
        print(f"{team}: {w}-{l}-{t}  (Conf: {cw}-{cl})")

if __name__ == "__main__":
    main()
