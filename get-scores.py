import os
import requests
import csv
import re
from datetime import datetime
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Team

# Constants
API_KEY = os.environ.get("CFBD_API_KEY", "").strip()
if not API_KEY:
    raise RuntimeError("Please set CFBD_API_KEY in your environment")

HEADERS = {
    "Accept": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

YEAR = 2024  # You can change this or make it dynamic

def fetch_all_records(year: int):
    url = "https://api.collegefootballdata.com/records"
    params = {"year": year}
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    return resp.json()

def fetch_preseason_rankings(year: int):
    url = "https://api.collegefootballdata.com/rankings"
    params = {"year": year}
    resp = requests.get(url, headers=HEADERS, params=params)
    resp.raise_for_status()
    data = resp.json()

    for week in data: 
        if week["week"] == 0:
            for poll in week["polls"]:
                if poll["poll"] == "AP Top 25":
                    return {entry["school"]: entry["rank"] for entry in poll["ranks"]}
    return {}

def write_to_csv(teams, timestamp_str):
    file_name = f"record{timestamp_str}.csv"
    with open(file_name, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["team", "wins", "losses", "ties", "conferenceWins", "conferenceLosses"])
        for team in teams:
            writer.writerow([
                team["team"],
                team["total"]["wins"],
                team["total"]["losses"],
                team["total"].get("ties", 0),
                team["conferenceGames"]["wins"],
                team["conferenceGames"]["losses"]
            ])

def update_database(session: Session, teams: list, preseason_rankings: dict):
    for r in sorted(teams, key=lambda x: x["team"]):
        name = r["team"]
        wins = r["total"]["wins"]
        losses = r["total"]["losses"]
        ties = r["total"].get("ties", 0)
        conf_wins = r["conferenceGames"]["wins"]
        conf_losses = r["conferenceGames"]["losses"]
        preseason_rank = preseason_rankings.get(name)
        tier = get_tier(preseason_rank)

        team = session.query(Team).filter_by(name=name).first()
        if not team:
            team = Team(
                name=name,
                wins=wins,
                losses=losses,
                ties=ties,
                conf_wins=conf_wins,
                conf_losses=conf_losses,
                preseason_rank=preseason_rank,
                tier=tier
            )
            session.add(team)
        else:
            team.wins = wins
            team.losses = losses
            team.ties = ties
            team.conf_wins = conf_wins
            team.conf_losses = conf_losses
            team.preseason_rank = preseason_rank
            team.tier = tier
    session.commit()

def get_tier(preseason_rank):
    if preseason_rank is None:
        return None
    if preseason_rank <= 10:
        return 1
    elif preseason_rank <= 25:
        return 2
    elif preseason_rank <= 50:
        return 3
    elif preseason_rank <= 75:
        return 4
    else:
        return 5


def main():
    now = datetime.now()
    timestamp_str = now.strftime("_%m_%d_%H_%M")

    print(f"Fetching FBS records for {YEAR}...\n")
    all_records = fetch_all_records(YEAR)
    fbs_records = [r for r in all_records if r.get("classification") == "fbs"]
    preseason_rankings = fetch_preseason_rankings(YEAR)

    print(f"Found {len(fbs_records)} FBS team records.\n")

    # Write backup CSV
    write_to_csv(fbs_records, timestamp_str)

    # Print records
    for r in sorted(fbs_records, key=lambda x: x["team"]):
        team = r["team"]
        w, l, t = r["total"]["wins"], r["total"]["losses"], r["total"].get("ties", 0)
        cw, cl = r["conferenceGames"]["wins"], r["conferenceGames"]["losses"]
        print(f"{team}: {w}-{l}-{t}  (Conf: {cw}-{cl})")

    # Update database
    with SessionLocal() as session:
        update_database(session, fbs_records, preseason_rankings)

if __name__ == "__main__":
    main()
