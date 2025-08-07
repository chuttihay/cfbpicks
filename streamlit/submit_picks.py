import streamlit as st
import sqlite3
from PIL import Image

# Database path
DB_PATH = "cfbpickem.db"

# Page setup
st.set_page_config(page_title="Submit Your Picks", layout="centered")
st.image(Image.open("streamlit/white.png"), use_container_width=True)
st.title("🏈 College Football Pick'em Submission Form")
st.header("Rules")
st.subheader("Cycle Through Tabs to Check Side-Pot Games & Buy-In/Payouts")

# Tab layout
main_tab, rat_tab, conf_tab, payout_tab = st.tabs(["Main Game", "Rat King", "Conference Champ", "Payouts"])

if "show_form" not in st.session_state:
    st.session_state.show_form = False

with main_tab:
    if not st.session_state.show_form:
        st.markdown("""
    - Each player selects a group of teams before the season starts. **You only pick once for the whole season.**
    - The games only last for the regular season.
    - If you want to change your picks before the season starts, just resubmit using the same email. It will overwrite your previous picks.
    - You earn points whenever one of your selected teams loses a game.  
    - The number of points earned per loss is based on the team's tier:  
      - Tier 1 = 6pts   - Preseason rank 1-10
      - Tier 2 = 4pts   - Preseason rank 11-25
      - Tier 3 = 3pts   - Preseason rank 26-50  
      - Tier 4 = 2pts   - Preseason rank 51-75
      - Tier 5 = 1pt    - Preseason rank 76+ 
    - The player with the **least points** at the end of the season wins.
        """)

with rat_tab:
    st.header("Rat King Rules")
    st.markdown("""
    - We all know watching Kennesaw State vs Lousiana Monroe isn't the best way to spend your Saturday.  
    So we want to reward the **Rat King** for having the best average Tier 5 records.  
    - It's about as simple as that, your picks with a preseason ranking of 76+ do matter and can still earn you some cash no matter how pitiful your top 4 tiers' teams play.  
    - So pick carefully and good luck!
    """)

with conf_tab:
    st.header("Conference Champ Rules")
    st.markdown("""
    - This side-pot is for all of the ball knowers out there that dont want to get shafted for a stupid out-of-conference loss, week 0.
    - We'll simply take the sum of all of your picks conference wins - all of your picks conference losses.
    - The player with the largest margin of conference wins will take the **Conference Champ** title. 
    """)

with payout_tab:
    st.header("Buy-In & Payouts")
    st.markdown("""
    **Buy-in is $35. Venmo Tanner with your DISPLAY NAME in the caption!!!**
    - For the tiebreaker, we will just go to total wins. If two players have the **same exact selections**, they will split the pot.
    - Failure to submit payment before the season starts will result in removal from the pickem.
    - Pot Split:
    """)

    st.table({
        "Game": ["Main Game", "Rat King", "Conference Champ"],
        "Prize Split": ["70%", "10%", "20%"]
    })

    st.image("streamlit/venmo.jpeg", use_container_width=True)
    st.markdown("""
    <div style="text-align: center;">
        <a href="https://venmo.com/code?user_id=1944273914167296153" target="_blank">Venmo Payment Link</a>
    </div>
    """, unsafe_allow_html=True)

# Always show button at bottom
if not st.session_state.show_form:
    if st.button("Take me to submission", key="go_to_submission"):
        st.session_state.show_form = True
        st.rerun()
    st.stop()

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

    tiers = {1: [], 2: [], 3: [], 4: [], 6: []}
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
    email = email.lower().strip()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM players WHERE email = ?", (email,))
        row = cursor.fetchone()

        if row:
            player_id = row[0]
            cursor.execute("UPDATE players SET name = ? WHERE id = ?", (name, player_id))
            cursor.execute("DELETE FROM player_picks WHERE player_id = ?", (player_id,))
        else:
            cursor.execute("INSERT INTO players (name, email) VALUES (?, ?)", (name, email))
            player_id = cursor.lastrowid

        for team_id in all_team_ids:
            cursor.execute("INSERT INTO player_picks (player_id, team_id) VALUES (?, ?)", (player_id, team_id))
        conn.commit()

player_tiers = {
    1: {"label": "Tier 1 (Top 10 teams)", "max": 1},
    2: {"label": "Tier 2 (Rank 11–25)", "max": 2},
    3: {"label": "Tier 3 (Rank 26–50)", "max": 3},
    4: {"label": "Tier 4 (Rank 51–75)", "max": 4},
    5: {"label": "Tier 5 (Rank 76+)", "max": 5},
}

name = st.text_input("Display Name")
email = st.text_input("Email")
db_tiers = get_teams_by_tier()
selected_teams = {}
all_selected_ids = []

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

# Separate display labels and team ID mapping
    label_to_id = {label: team_id for label, team_id in options}
    labels = list(label_to_id.keys())

    selected_labels = st.multiselect(
        f"{label} — Select {max_allowed} teams",
        options=labels,
        key=f"tier{player_tier}"
    )

    selected_teams[player_tier] = selected_labels
    all_selected_ids.extend([label_to_id[label] for label in selected_labels])


if st.button("Submit Picks", key="submit_button"):
    if not name.strip() or not email.strip():
        st.error("Please enter both your name and email before submitting.")
        st.stop()

    valid = True
    for tier, picks in selected_teams.items():
        expected = player_tiers[tier]["max"]
        if len(picks) != expected:
            st.error(f"You must select exactly {expected} teams in {player_tiers[tier]['label']}.")
            valid = False

    if valid:
        save_picks(name, email, all_selected_ids)
        st.success("✅ Your picks have been submitted!")
