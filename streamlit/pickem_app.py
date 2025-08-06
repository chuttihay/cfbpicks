import streamlit as st
import sqlite3
from PIL import Image

DB_PATH = "../cfbpickem.db"

# Page config
st.set_page_config(page_title="College Pick'em", layout="centered")

# Custom sidebar CSS for button styling
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        text-align: left;
        margin: 0.25rem 0;
        font-size: 1rem;
        padding: 0.5rem;
    }
    .sidebar-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.image(Image.open("white.png"), use_container_width=True)
st.title("Presented by the Shelby Fellas")

# Sidebar nav menu
st.sidebar.markdown('<div class="sidebar-title">📂 Navigation</div>', unsafe_allow_html=True)

nav_options = {
    "Standings": "🏆 Standings",
    "Game Stats": "🎯 Game Stats",
    "Rules": "📜 Rules"
}

for key, label in nav_options.items():
    if st.sidebar.button(label):
        st.session_state["page"] = key

if "page" not in st.session_state:
    st.session_state["page"] = "Standings"

page = st.session_state["page"]

# Database helpers
def get_db_connection():
    return sqlite3.connect(DB_PATH)

def get_all_players():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM players")
        return [row[0] for row in cursor.fetchall()]

def get_player_points(player_name):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.losses, t.tier
            FROM player_picks p
            JOIN players pl ON p.player_id = pl.id
            JOIN teams t ON p.team_id = t.id
            WHERE pl.name = ?
        """, (player_name,))
        return sum(row[0] * row[1] for row in cursor.fetchall())

def get_teams_and_records_for(player_name):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.name, t.wins, t.losses, t.ties, t.conf_wins, t.conf_losses
            FROM player_picks p
            JOIN players pl ON p.player_id = pl.id
            JOIN teams t ON p.team_id = t.id
            WHERE pl.name = ?
        """, (player_name,))
        return [
            (name, f"{w}-{l}-{t} (Conf: {cw}-{cl})")
            for name, w, l, t, cw, cl in cursor.fetchall()
        ]

def calculate_all_player_points():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM players")
        players = cursor.fetchall()

        def calculate_points(player_id):
            cursor.execute("""
                SELECT t.losses, t.tier
                FROM player_picks p
                JOIN teams t ON p.team_id = t.id
                WHERE p.player_id = ?
            """, (player_id,))
            return sum(row[0] * row[1] for row in cursor.fetchall())

        return [(player[1], calculate_points(player[0])) for player in players]

def get_teams_and_records_for(player_name, include_points=False):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if include_points:
            cursor.execute("""
                SELECT t.name, t.wins, t.losses, t.ties, t.tier, t.losses * t.tier as points
                FROM player_picks p
                JOIN players pl ON p.player_id = pl.id
                JOIN teams t ON p.team_id = t.id
                WHERE pl.name = ?
            """, (player_name,))
            return [
                (name, f"{w}-{l}-{t}", tier, points)
                for name, w, l, t, tier, points in cursor.fetchall()
            ]
        else:
            cursor.execute("""
                SELECT t.name, t.wins, t.losses, t.ties, t.tier
                FROM player_picks p
                JOIN players pl ON p.player_id = pl.id
                JOIN teams t ON p.team_id = t.id
                WHERE pl.name = ?
            """, (player_name,))
            return [
                (name, f"{w}-{l}-{t}", tier)
                for name, w, l, t, tier in cursor.fetchall()
            ]



# --- Pages ---

if page == "Standings":
    st.header("🏆 Standings")

    player_points = calculate_all_player_points()
    player_points.sort(key=lambda x: x[1])  # always ascending

    all_player_names = [name for name, _ in player_points]
    selected = st.selectbox("Select Player (or view all)", ["All"] + all_player_names)

    for idx, (name, pts) in enumerate(player_points, start=1):
        if selected != "All" and selected != name:
            continue

        with st.expander(f"#{idx} {name} - {pts} pts"):
            teams = get_teams_and_records_for(name, include_points=True)
            for team, record, tier, team_points in teams:
                st.write(f"- {team} [Tier {tier}] ({record}) → {team_points} pts")


elif page == "Game Stats":
    st.header("🏈 Team Overview")

    tab1, tab2 = st.tabs(["📊 Team Stats", "📈 Pick Popularity"])

    with tab1:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name, wins, losses, ties, conf_wins, conf_losses, 
                       COALESCE(preseason_rank, '-') as preseason_rank, 
                       COALESCE(tier, '-') as tier
                FROM teams
                ORDER BY name
            """)
            rows = cursor.fetchall()

        st.subheader("All Teams & Stats")
        st.dataframe(
            {
                "Team": [r[0] for r in rows],
                "Record": [f"{r[1]}-{r[2]}-{r[3]}" for r in rows],
                "Conf Record": [f"{r[4]}-{r[5]}" for r in rows],
                "Preseason Rank": [r[6] for r in rows],
                "Tier": [r[7] for r in rows],
            },
            use_container_width=True
        )

    with tab2:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.name, COUNT(*) as pick_count
                FROM player_picks p
                JOIN teams t ON p.team_id = t.id
                GROUP BY t.name
                ORDER BY pick_count DESC
            """)
            data = cursor.fetchall()

        st.subheader("Team Pick Popularity")
        if data:
            import pandas as pd
            import altair as alt

            df = pd.DataFrame(data, columns=["Team", "Picks"])
            chart = alt.Chart(df).mark_bar().encode(
                x=alt.X("Picks:Q", title="Number of Players"),
                y=alt.Y("Team:N", sort='-x', title="Team"),
                tooltip=["Team", "Picks"]
            ).properties(height=600)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No picks yet!")



elif page == "Rules":
    st.header("📜 Rules")
    st.markdown("""
    - Each player selects a group of teams before the season starts.  
    - You earn points whenever one of your selected teams loses a game.  
    - The number of points earned per loss is based on the team's tier:  
      - Tier 1 = 6pts   - Preseason rank 1-10
      - Tier 2 = 4pts   - Preseason rank 11-25
      - Tier 3 = 3pts   - Preseason rank 26-50  
      - Tier 4 = 2pts   - Preseason rank 51-75
      - Tier 5 = 1pt    - Preseason rank 76+ 
    - The player with the **least points** at the end of the season wins.
    """)
