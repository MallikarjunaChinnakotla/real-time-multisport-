import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import time

# Paths
DATA_DIR = "sports_data/volleyball"
TEAMS_FILE = os.path.join(DATA_DIR, "volleyball_teams.csv")
TOURNAMENTS_FILE = os.path.join(DATA_DIR, "volleyball_tournaments.csv")
MATCHES_FILE = os.path.join(DATA_DIR, "volleyball_matches.csv")
SCORES_FILE = os.path.join(DATA_DIR, "volleyball_scores.csv")

# Ensure directories & files exist
os.makedirs(DATA_DIR, exist_ok=True)
for file in [TEAMS_FILE, TOURNAMENTS_FILE, MATCHES_FILE, SCORES_FILE]:
    if not os.path.exists(file):
        pd.DataFrame().to_csv(file, index=False)

def load_csv(file):
    try:
        return pd.read_csv(file)
    except:
        return pd.DataFrame()

def save_csv(df, file):
    df.to_csv(file, index=False)

# 1. Add Tournament
def add_tournament():
    st.subheader("Add Volleyball Tournament")
    name = st.text_input("Tournament Name")
    location = st.text_input("Location")
    date = st.date_input("Date")
    if st.button("Add Tournament"):
        df = load_csv(TOURNAMENTS_FILE)
        new_row = {"name": name, "location": location, "date": date}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_csv(df, TOURNAMENTS_FILE)
        st.success("Tournament added!")

# 2. Add Team
def add_team():
    st.subheader("Add Volleyball Team")
    team_name = st.text_input("Team Name")
    players = st.text_area("Players (comma-separated, max 10)")
    if st.button("Add Team"):
        plist = [p.strip() for p in players.split(",") if p.strip()]
        if len(plist) > 10:
            st.error("Max 10 players allowed.")
        else:
            df = load_csv(TEAMS_FILE)
            new_row = {"team_name": team_name, "players": ", ".join(plist)}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_csv(df, TEAMS_FILE)
            st.success("Team added!")

# 3. View Tournaments
def view_tournaments():
    st.subheader("View Tournaments")
    df = load_csv(TOURNAMENTS_FILE)
    st.dataframe(df)

# 4. Schedule Match
def schedule_match():
    st.subheader("Schedule Match")
    tournaments = load_csv(TOURNAMENTS_FILE)
    teams = load_csv(TEAMS_FILE)
    if tournaments.empty or teams.empty:
        st.warning("Add tournaments and teams first.")
        return

    tournament = st.selectbox("Tournament", tournaments["name"])
    team1 = st.selectbox("Team 1", teams["team_name"])
    team2 = st.selectbox("Team 2", teams["team_name"])
    date = st.date_input("Match Date")

    if st.button("Schedule"):
        if team1 == team2:
            st.error("Teams must be different.")
        else:
            df = load_csv(MATCHES_FILE)
            new_row = {"tournament": tournament, "team1": team1, "team2": team2, "date": date}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_csv(df, MATCHES_FILE)
            st.success("Match scheduled.")

# 5. Update Live Score
def update_score():
    st.subheader("Live Match")
    matches = load_csv(MATCHES_FILE)
    if matches.empty:
        st.warning("No matches scheduled.")
        return

    match_strs = matches.apply(lambda row: f"{row['team1']} vs {row['team2']} ({row['date']})", axis=1)
    match_choice = st.selectbox("Select Match", match_strs)
    selected_row = matches.iloc[match_strs.tolist().index(match_choice)]

    team1, team2 = selected_row["team1"], selected_row["team2"]

    st.markdown(f"### {team1} vs {team2}")
    score1 = st.number_input(f"{team1} Score", min_value=0)
    score2 = st.number_input(f"{team2} Score", min_value=0)
    serve_team = st.selectbox("Serve Team", [team1, team2])
    timeout_team = st.selectbox("Timeout Called By", ["None", team1, team2])
    
    # Timer
    match_start = st.time_input("Match Start Time", value=datetime.now().time())
    duration = st.slider("Match Duration (minutes)", 10, 120, 60)

    if st.button("Start Timer"):
        st.session_state['start_time'] = datetime.now()
        st.session_state['end_time'] = datetime.now() + timedelta(minutes=duration)

    if 'start_time' in st.session_state:
        elapsed = datetime.now() - st.session_state['start_time']
        time_left = st.session_state['end_time'] - datetime.now()
        st.success(f"Elapsed: {str(elapsed).split('.')[0]} | Remaining: {str(time_left).split('.')[0]}")

        if datetime.now() >= st.session_state['end_time']:
            st.warning("⏰ Match Time Over!")

    if st.button("Update Score"):
        df = load_csv(SCORES_FILE)
        new_row = {
            "match": match_choice,
            "team1": team1,
            "team2": team2,
            "score1": score1,
            "score2": score2,
            "serve_team": serve_team,
            "timeout_team": "" if timeout_team == "None" else timeout_team,
            "timestamp": datetime.now()
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_csv(df, SCORES_FILE)
        st.success("Score logged!")

    # Undo last entry
    if st.button("Undo Last Entry"):
        df = load_csv(SCORES_FILE)
        df = df[df["match"] != match_choice] if df.empty else df.iloc[:-1]
        save_csv(df, SCORES_FILE)
        st.success("Last entry removed.")

# 6. View Summary
def view_summary():
    st.subheader("Match Summary")
    df = load_csv(SCORES_FILE)
    if df.empty:
        st.info("No data.")
        return

    match_filter = st.selectbox("Select Match", df["match"].unique())
    match_data = df[df["match"] == match_filter]
    st.dataframe(match_data)

    st.markdown("### Serve Count")
    st.bar_chart(match_data["serve_team"].value_counts())

    st.markdown("### Timeout Count")
    timeout_data = match_data["timeout_team"].value_counts()
    timeout_data = timeout_data[timeout_data.index != ""]
    st.bar_chart(timeout_data)
def run():
    st.title("🏐 Volleyball  Dashboard")
    st.write("Live Volleyball  stats go here...")
# MAIN
def run_volleyball():
    st.sidebar.title("🏐 Volleyball Module")
    choice = st.sidebar.radio("Select Option", [
        "Add Tournament", "Add Team", "View Tournaments",
        "Schedule Match", "Update Live Score", "View Match Summary"
    ])
    if choice == "Add Tournament":
        add_tournament()
    elif choice == "Add Team":
        add_team()
    elif choice == "View Tournaments":
        view_tournaments()
    elif choice == "Schedule Match":
        schedule_match()
    elif choice == "Update Live Score":
        update_score()
    elif choice == "View Match Summary":
        view_summary()

