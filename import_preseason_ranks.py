import csv
import sqlite3

def calculate_tier(rank):
    if not rank:
        return None
    rank = int(rank)
    if rank <= 10:
        return 6
    elif rank <= 25:
        return 4
    elif rank <= 50:
        return 3
    elif rank <= 75:
        return 2
    else:
        return 1

def update_preseason_ranks(csv_path, db_path="cfbpickem.db"):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            team = row["team"].strip()
            rank_str = row["rank"].strip()
            rank = int(rank_str) if rank_str else None
            tier = calculate_tier(rank) if rank else None

            c.execute("""
                UPDATE teams
                SET preseason_rank = ?, tier = ?
                WHERE name = ?
            """, (rank, tier, team))


    conn.commit()
    conn.close()
    print("✅ Preseason rankings and tiers updated in SQLite.")

if __name__ == "__main__":
    update_preseason_ranks("preseason_ranks.csv")
