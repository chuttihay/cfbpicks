import streamlit as st
import sqlite3
from PIL import Image
import pandas as pd
import altair as alt

DB_PATH = "cfbpickem.db"
ADMIN_PASSWORD = st.secrets["admin"]["password"]

# Helper
def get_db_connection():
    return sqlite3.connect(DB_PATH)

def check_admin_password():
    return st.session_state.get("authenticated", False)

def login():
    password = st.text_input("Enter admin password", type="password")
    if st.button("Login"):
        if password == ADMIN_PASSWORD:
            st.session_state["authenticated"] = True
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Incorrect password")

# App config
st.set_page_config(page_title="Admin Panel", layout="centered")
st.title("🔧 Admin Panel - College Pick'em")

# Admin login
if not check_admin_password():
    login()
    st.stop()

# Tabs for admin tasks
tab1, tab2, tab3, tab4 = st.tabs(["Update Team Stats", "Manage Picks", "Manage Players", "Users"])

# --- Tab 1: Update Team Stats ---
with tab1:
    st.subheader("📊 Edit Team Stats")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM teams ORDER BY name")
        teams = cursor.fetchall()

    team_names = {name: id for id, name in teams}
    selected_team = st.selectbox("Select a team", list(team_names.keys()))

    if selected_team:
        team_id = team_names[selected_team]

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT wins, losses, ties, conf_wins, conf_losses, tier, preseason_rank
                FROM teams WHERE id = ?
            """, (team_id,))
            row = cursor.fetchone()

        wins = st.number_input("Wins", min_value=0, value=row[0])
        losses = st.number_input("Losses", min_value=0, value=row[1])
        ties = st.number_input("Ties", min_value=0, value=row[2])
        conf_wins = st.number_input("Conf Wins", min_value=0, value=row[3])
        conf_losses = st.number_input("Conf Losses", min_value=0, value=row[4])
        tier = st.number_input("Tier (1-6)", min_value=1, max_value=6, value=row[5])
        preseason_rank = st.number_input("Preseason Rank", min_value=1, value=row[6])

        if st.button("Update Team Stats"):
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE teams SET wins=?, losses=?, ties=?, conf_wins=?, conf_losses=?, tier=?, preseason_rank=?
                    WHERE id = ?
                """, (wins, losses, ties, conf_wins, conf_losses, tier, preseason_rank, team_id))
                conn.commit()
                st.success(f"{selected_team} stats updated!")

# --- Tab 2: Manage Picks ---
with tab2:
    st.subheader("📝 Edit Player Picks")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM players ORDER BY name")
        players = cursor.fetchall()

    player_names = {name: id for id, name in players}
    selected_player = st.selectbox("Select Player", list(player_names.keys()))

    if selected_player:
        player_id = player_names[selected_player]

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.name FROM player_picks p
                JOIN teams t ON p.team_id = t.id
                WHERE p.player_id = ?
            """, (player_id,))
            picks = [row[0] for row in cursor.fetchall()]

        st.write("Current Picks:", ", ".join(picks))

        add_team = st.selectbox("Add a Team", [t for t in team_names.keys() if t not in picks])
        if st.button("Add Pick"):
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO player_picks (player_id, team_id) VALUES (?, ?)",
                               (player_id, team_names[add_team]))
                conn.commit()
                st.success(f"Added {add_team} to {selected_player}'s picks!")

        remove_team = st.selectbox("Remove a Team", picks)
        if st.button("Remove Pick"):
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM player_picks WHERE player_id = ? AND team_id = ?
                """, (player_id, team_names[remove_team]))
                conn.commit()
                st.warning(f"Removed {remove_team} from {selected_player}'s picks.")

# --- Tab 3: Manage Players ---
with tab3:
    st.subheader("👤 Manage Players")

    new_player = st.text_input("Player Name")
    new_email = st.text_input("Email Address")
    paid = st.checkbox("Paid", value=False)

    if st.button("Add Player") and new_player.strip():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO players (name, email, paid) VALUES (?, ?, ?)",
                (new_player.strip(), new_email.strip(), int(paid))
            )
            conn.commit()
            st.success(f"Added new player: {new_player.strip()} (Paid: {paid})")

    delete_player = st.selectbox("Delete Existing Player", list(player_names.keys()))
    if st.button("Delete Player"):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM player_picks WHERE player_id = (SELECT id FROM players WHERE name = ?)", (delete_player,))
            cursor.execute("DELETE FROM players WHERE name = ?", (delete_player,))
            conn.commit()
            st.warning(f"Deleted player: {delete_player} and all associated picks.")

# --- Tab 4: Users ---
with tab4:
    st.subheader("👥 All Users")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, paid FROM players ORDER BY name")
        rows = cursor.fetchall()

    for player_id, name, email, paid in rows:
        cols = st.columns([3, 4, 2, 2])
        cols[0].write(name)
        cols[1].write(email)
        is_paid = cols[2].checkbox("Paid", value=bool(paid), key=f"paid_{player_id}")

        if is_paid != bool(paid):
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE players SET paid = ? WHERE id = ?", (int(is_paid), player_id))
                conn.commit()
                st.success(f"Updated {name}'s paid status to {'✅' if is_paid else '❌'}")
                st.rerun()
