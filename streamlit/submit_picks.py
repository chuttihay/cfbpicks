import streamlit as st
import sqlite3
from PIL import Image

# Database path
DB_PATH = "../cfbpickem.db"

# Page setup
st.image(Image.open("white.png"), use_container_width=True)
st.set_page_config(page_title="Submit Your Picks", layout="centered")
st.title("🏈 College Football Pick'em Submission Form")

# Connect to SQLite
def get_connection():
    return sqlite3.connect(DB_PATH)

# Get teams organized by database tier
def get_teams_by_tier():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, tier, preseason_rank 
            FROM teams 
            WHERE tier IS NOT NULL 
            ORDER BY preseason_rank ASC
        """)
        teams = cursor.fetchall()

    tiers = {1: [], 2: [], 3: [], 4: [], 6: []}  # DB tier values
    for team_id, name, tier, rank in teams:
        player_tier = (
            1 if tier == 6 else
            2 if tier == 4 else
            3 if tier == 3 else
            4 if tier == 2 else
            5 if tier == 1 else
            None
        )
        if player_tier:
            label = f"#{rank} {name} (Pts/Loss: {tier})" if rank else f"{name} (Pts/Loss: {tier})"
            tiers[tier].append((label, team_id))
    return tiers

# Save to database
def save_picks(name, email, all_team_ids):
    email = email.lower().strip()  # normalize email

    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if player exists by email (email is unique in DB)
        cursor.execute("SELECT id, name FROM players WHERE email = ?", (email,))
        row = cursor.fetchone()

        if row:
            player_id = row[0]
            cursor.execute("UPDATE players SET name = ? WHERE id = ?", (name, player_id))
            cursor.execute("DELETE FROM player_picks WHERE player_id = ?", (player_id,))
        else:
            cursor.execute("INSERT INTO players (name, email) VALUES (?, ?)", (name, email))
            player_id = cursor.lastrowid

        # Insert new picks
        for team_id in all_team_ids:
            cursor.execute("INSERT INTO player_picks (player_id, team_id) VALUES (?, ?)", (player_id, team_id))

        conn.commit()


# Tier structure
player_tiers = {
    1: {"label": "Tier 1 (Top 10 teams)", "max": 1},
    2: {"label": "Tier 2 (Rank 11–25)", "max": 2},
    3: {"label": "Tier 3 (Rank 26–50)", "max": 3},
    4: {"label": "Tier 4 (Rank 51–75)", "max": 4},
    5: {"label": "Tier 5 (Rank 76+)", "max": 5},
}

# Form UI
name = st.text_input("Display Name")
email = st.text_input("Email")

db_tiers = get_teams_by_tier()

selected_teams = {}
all_selected_ids = []

# Team selections per tier
for player_tier in range(1, 6):
    db_tier = (
        6 if player_tier == 1 else
        4 if player_tier == 2 else
        3 if player_tier == 3 else
        2 if player_tier == 4 else
        1
    )

    options = db_tiers.get(db_tier, [])
    label = player_tiers[player_tier]["label"]
    max_allowed = player_tiers[player_tier]["max"]

    selected = st.multiselect(
        f"{label} — Select {max_allowed} teams",
        options=options,
        key=f"tier{player_tier}"
    )

    selected_teams[player_tier] = selected
    all_selected_ids.extend([team_id for _, team_id in selected])

# Submit button
if st.button("Submit Picks"):
    if not name.strip() or not email.strip():
        st.error("Please enter both your name and email before submitting.")
        st.stop()

    # Check pick count
    valid = True
    for tier, picks in selected_teams.items():
        expected = player_tiers[tier]["max"]
        if len(picks) != expected:
            st.error(f"You must select exactly {expected} teams in {player_tiers[tier]['label']}.")
            valid = False

    if valid:
        save_picks(name, email, all_selected_ids)
        st.success("✅ Your picks have been submitted!")
