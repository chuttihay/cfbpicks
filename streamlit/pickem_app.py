import streamlit as st
import sqlite3
from PIL import Image
import pandas as pd
import altair as alt

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
    "Game Stats": "🎯  Game Stats",
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
                SELECT t.name, t.wins, t.losses, t.ties, t.tier, t.conf_wins, t.conf_losses
                FROM player_picks p
                JOIN players pl ON p.player_id = pl.id
                JOIN teams t ON p.team_id = t.id
                WHERE pl.name = ?
            """, (player_name,))
            return [
                (name, f"{w}-{l}-{t}", tier, conf_wins, conf_losses)
                for name, w, l, t, tier, conf_wins, conf_losses in cursor.fetchall()
            ]

def calculate_rat_king_scores():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM players")
        players = cursor.fetchall()

        def tier5_details(player_id):
            cursor.execute("""
                SELECT t.name, t.wins, t.losses
                FROM player_picks p
                JOIN teams t ON p.team_id = t.id
                WHERE p.player_id = ? AND t.tier = 1
            """, (player_id,))
            return cursor.fetchall()

        scores = []
        for player_id, name in players:
            details = tier5_details(player_id)
            if not details:
                scores.append((name, 0.0, []))
            else:
                rates = []
                for _, w, l in details:
                    total = w + l
                    win_rate = w / total if total else 0
                    rates.append(win_rate)
                avg = sum(rates) / len(rates)
                scores.append((name, avg, details))
        return scores

def calculate_conference_champ_scores():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM players")
        players = cursor.fetchall()

        results = []
        for player_id, name in players:
            cursor.execute("""
                SELECT t.name, t.conf_wins, t.conf_losses
                FROM player_picks p
                JOIN teams t ON p.team_id = t.id
                WHERE p.player_id = ?
            """, (player_id,))
            data = cursor.fetchall()
            margin = sum(w - l for _, w, l in data)
            results.append((name, margin, data))
        return results

# --- Pages ---

if page == "Standings":
    st.header("🏆 Standings")

    tab1, tab2, tab3 = st.tabs(["Main Game", "Rat King", "Conference Champ"])

    with tab1:
        player_points = calculate_all_player_points()
        player_points.sort(key=lambda x: x[1])

        all_player_names = [name for name, _ in player_points]
        selected = st.selectbox("Select Player (or view all)", ["All"] + all_player_names)

        for idx, (name, pts) in enumerate(player_points, start=1):
            if selected != "All" and selected != name:
                continue

            with st.expander(f"#{idx} {name} - {pts} pts"):
                teams = get_teams_and_records_for(name, include_points=True)
                for team, record, tier, team_points in teams:
                    player_tier = (
                        1 if tier == 6 else
                        2 if tier == 4 else
                        3 if tier == 3 else
                        4 if tier == 2 else
                        5 if tier == 1 else
                        tier
                    )
                    st.markdown(f"{team} [Tier {player_tier}] ({record}) → {team_points} pts")

    with tab2:
        st.subheader("Rat King Standings (Avg Win Rate of Tier 5 Picks)")
        scores = calculate_rat_king_scores()
        scores.sort(key=lambda x: x[1], reverse=True)

        all_names = [name for name, _, _ in scores]
        selected = st.selectbox("Select Player (or view all)", ["All"] + all_names, key="rat_king")

        for idx, (name, score, details) in enumerate(scores, start=1):
            if selected != "All" and selected != name:
                continue

            with st.expander(f"#{idx} {name} — Avg Win Rate: {score:.3%}"):
                for team_name, wins, losses in details:
                    total = wins + losses
                    rate = wins / total if total else 0
                    st.write(f"{team_name}: {wins}-{losses} ({rate:.1%})")

    with tab3:
        st.subheader("Conference Champ Standings (Conf Wins - Conf Losses)")
        scores = calculate_conference_champ_scores()
        scores.sort(key=lambda x: x[1], reverse=True)

        all_names = [name for name, _, _ in scores]
        selected = st.selectbox("Select Player (or view all)", ["All"] + all_names, key="conf_champ")

        for idx, (name, margin, data) in enumerate(scores, start=1):
            if selected != "All" and selected != name:
                continue

            with st.expander(f"#{idx} {name} — Conf Margin: {margin}"):
                for team_name, conf_wins, conf_losses in data:
                    st.write(f"{team_name}: {conf_wins}-{conf_losses}")

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
                "Cost": [r[7] for r in rows],
            },
            use_container_width=True
        )

    with tab2:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.name, t.tier, COUNT(*) as pick_count
                FROM player_picks p
                JOIN teams t ON p.team_id = t.id
                GROUP BY t.name, t.tier
                ORDER BY pick_count DESC
            """)
            data = cursor.fetchall()

        st.subheader("Team Pick Popularity")
        if data:
            df = pd.DataFrame(data, columns=["Team", "Tier", "Picks"])

            # Convert database tier to player-facing tier
            def convert_tier(db_tier):
                return (
                    1 if db_tier == 6 else
                    2 if db_tier == 4 else
                    3 if db_tier == 3 else
                    4 if db_tier == 2 else
                    5 if db_tier == 1 else
                    db_tier
                )

            df["PlayerTier"] = df["Tier"].apply(convert_tier)
            df = df.sort_values("PlayerTier")

            selected_tier = st.selectbox("Filter by Tier", sorted(df["PlayerTier"].unique()))
            df = df[df["PlayerTier"] == selected_tier]

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
    st.subheader("Cycle Through Tabs to Check Side-Pot Games & Buy-In/Payouts")

    main_tab, rat_tab, conf_tab, payout_tab = st.tabs(["Main Game", "Rat King", "Conference Champ", "Payouts"])

    with main_tab:
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
        **Buy-in is $25. Venmo Tanner with your DISPLAY NAME in the caption!!!**  
        - Pot Split:
        """)

        st.table({
            "Game": ["Main Game", "Rat King", "Conference Champ"],
            "Prize Split": ["70%", "10%", "20%"]
        })

        st.image("venmo.jpeg", use_container_width=True)
        st.markdown("""
        <div style="text-align: center;">
            <a href="https://venmo.com/code?user_id=1944273914167296153" target="_blank">Venmo Payment Link</a>
        </div>
        """, unsafe_allow_html=True)
