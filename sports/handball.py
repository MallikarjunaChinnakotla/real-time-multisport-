# handball.py
import os
import pandas as pd
import streamlit as st
from datetime import datetime

# ===== Paths =====
DATA_DIR = "sports_dashboard/data"
os.makedirs(DATA_DIR, exist_ok=True)

TOURNAMENTS = os.path.join(DATA_DIR, "handball_tournaments.csv")
TEAMS = os.path.join(DATA_DIR, "handball_teams.csv")
PLAYERS = os.path.join(DATA_DIR, "handball_players.csv")
MATCHES = os.path.join(DATA_DIR, "handball_matches.csv")
SCORES = os.path.join(DATA_DIR, "handball_scores.csv")

# CSV headers
T_HDR = ["tournament_id", "tournament_name", "start_date", "end_date", "location"]
TEAM_HDR = ["team_id", "team_name", "tournament_id"]
PLAYER_HDR = ["player_id", "player_name", "team_id"]
MATCH_HDR = ["match_id", "tournament_id", "team1_id", "team2_id", "match_date", "venue"]
SCORE_HDR = ["match_id", "team_id", "player_id", "points", "event", "timestamp"]


def init_files():
    for f, hdr in [(TOURNAMENTS, T_HDR),(TEAMS, TEAM_HDR),(PLAYERS, PLAYER_HDR),(MATCHES, MATCH_HDR),(SCORES, SCORE_HDR)]:
        if not os.path.exists(f):
            pd.DataFrame(columns=hdr).to_csv(f, index=False)


def load_csv(f, h): return pd.read_csv(f) if os.path.exists(f) else pd.DataFrame(columns=h)
def save_csv(df, f): df.to_csv(f, index=False)

init_files()

# === Admin Operations ===
def add_tournament():
    st.subheader("➕ Add Tournament")
    df = load_csv(TOURNAMENTS, T_HDR)
    name = st.text_input("Tournament Name")
    loc = st.text_input("Location")
    start = st.date_input("Start Date")
    end = st.date_input("End Date")
    if st.button("Save Tournament"):
        new_id = df["tournament_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [new_id, name, start, end, loc]
        save_csv(df, TOURNAMENTS)
        st.success("Tournament added!")

def add_team():
    st.subheader("➕ Add Team")
    df = load_csv(TEAMS, TEAM_HDR)
    tours = load_csv(TOURNAMENTS, T_HDR)
    if tours.empty: st.warning("Add tournaments first"); return

    team = st.text_input("Team Name")
    tour = st.selectbox("Tournament", tours["tournament_name"])
    tid = tours.loc[tours["tournament_name"]==tour,"tournament_id"].values[0]
    
    if st.button("Add Team"):
        new_id = df["team_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [new_id, team, tid]
        save_csv(df, TEAMS)
        st.success("Team added!")

def add_player():
    st.subheader("➕ Add Player")
    df = load_csv(PLAYERS, PLAYER_HDR)
    teams = load_csv(TEAMS, TEAM_HDR)
    if teams.empty: st.error("No teams! Add teams first"); return

    player = st.text_input("Player Name")
    team = st.selectbox("Team", teams["team_name"])
    tid = teams.loc[teams["team_name"]==team,"team_id"].values[0]

    if st.button("Add Player"):
        new_id = df["player_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [new_id, player, tid]
        save_csv(df, PLAYERS)
        st.success("Player added!")

def schedule_match():
    st.subheader("📅 Schedule Match")
    df = load_csv(MATCHES, MATCH_HDR)
    teams = load_csv(TEAMS, TEAM_HDR)
    tours = load_csv(TOURNAMENTS, T_HDR)

    if tours.empty or teams.empty: return st.error("Add tournaments & teams first")

    tour = st.selectbox("Tournament", tours["tournament_name"])
    tid = tours.loc[tours["tournament_name"]==tour,"tournament_id"].values[0]

    valid = teams[teams["tournament_id"]==tid]
    if len(valid)<2: return st.warning("Need 2+ teams")

    t1 = st.selectbox("Team 1", valid["team_name"])
    t2 = st.selectbox("Team 2", [x for x in valid["team_name"] if x!=t1])
    
    d = st.date_input("Match Date")
    venue = st.text_input("Venue")

    if st.button("Schedule"):
        nid = df["match_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [nid, tid,
                           valid.loc[valid["team_name"]==t1,"team_id"].values[0],
                           valid.loc[valid["team_name"]==t2,"team_id"].values[0],
                           d, venue]
        save_csv(df, MATCHES)
        st.success("Match added!")

# === Live Match ===
def update_live_match():
    st.subheader("🎯 Live Score Update")
    matches = load_csv(MATCHES, MATCH_HDR)
    if matches.empty: return st.warning("No matches!")

    m = st.selectbox("Select Match", matches["match_id"])
    match = matches[matches["match_id"]==m].iloc[0]

    teams = load_csv(TEAMS, TEAM_HDR)
    plys = load_csv(PLAYERS, PLAYER_HDR)

    t1 = teams.loc[teams["team_id"]==match["team1_id"],"team_name"].values[0]
    t2 = teams.loc[teams["team_id"]==match["team2_id"],"team_name"].values[0]

    st.write(f"### {t1} vs {t2}")

    scoring_team = st.selectbox("Scoring Team",[t1,t2])
    tid = match["team1_id"] if scoring_team==t1 else match["team2_id"]
    team_players = plys[plys["team_id"]==tid]

    player = st.selectbox("Player",team_players["player_name"])
    pid = team_players.loc[team_players["player_name"]==player,"player_id"].values[0]

    points = st.number_input("Points",0,5,1)

    if st.button("Add Score"):
        df = load_csv(SCORES, SCORE_HDR)
        df.loc[len(df)] = [m, tid, pid, points, "Goal", datetime.now()]
        save_csv(df,SCORES)
        st.success("Updated!")
def view_tournaments():
    st.subheader("📋 View Handball Tournaments")
    
    tournaments = load_csv(TOURNAMENTS, T_HDR)
    matches = load_csv(MATCHES, MATCH_HDR)
    teams = load_csv(TEAMS, TEAM_HDR)

    if tournaments.empty:
        st.warning("No tournaments found. Please add a tournament first.")
        return

    tournament_list = tournaments["tournament_name"].tolist()
    selected = st.selectbox("Select Tournament", tournament_list)

    if selected:
        st.markdown(f"### Matches in {selected}")

        tournament_id = int(
            tournaments.loc[
                tournaments["tournament_name"] == selected,
                "tournament_id"
            ].values[0]
        )

        tournament_matches = matches[matches["tournament_id"] == tournament_id]

        if tournament_matches.empty:
            st.info("No matches scheduled for this tournament.")
            return

        def get_team_name(team_id):
            name = teams.loc[teams["team_id"] == team_id, "team_name"]
            return name.values[0] if not name.empty else "Unknown"

        display_df = tournament_matches.copy()
        display_df["Team 1"] = display_df["team1_id"].apply(get_team_name)
        display_df["Team 2"] = display_df["team2_id"].apply(get_team_name)
        display_df["Match Date"] = display_df["match_date"]
        display_df["Venue"] = display_df["venue"]

        st.dataframe(
            display_df[["match_id", "Team 1", "Team 2", "Match Date", "Venue"]]
            .reset_index(drop=True)
        )

# === Summary ===
def view_summary():
    st.header("📊 Match Summary")
    df = load_csv(SCORES, SCORE_HDR)
    if df.empty: return st.info("No records")

    match = st.selectbox("Match",df["match_id"].unique())
    show = df[df["match_id"]==match]
    st.dataframe(show)
def view_tournaments():
    st.subheader("📋 View Tournaments")

    tournaments = load_csv(TOURNAMENTS, T_HDR)
    matches = load_csv(MATCHES, MATCH_HDR)
    teams = load_csv(TEAMS, TEAM_HDR)

    if tournaments.empty:
        st.warning("No tournaments found.")
        return
    
    tournament_list = tournaments["tournament_name"].tolist()
    selected = st.selectbox("Select Tournament", tournament_list)

    if selected:
        st.markdown(f"### Matches in {selected}")
        
        tid = int(tournaments.loc[
            tournaments["tournament_name"] == selected,
            "tournament_id"
        ].values[0])

        t_matches = matches[matches["tournament_id"] == tid]

        if t_matches.empty:
            st.info("No matches scheduled in this tournament.")
        else:
            def get_team_name(team_id):
                name = teams.loc[teams["team_id"] == team_id, "team_name"]
                return name.values[0] if not name.empty else "Unknown"

            display_df = t_matches.copy()
            display_df["Team 1"] = display_df["team1_id"].apply(get_team_name)
            display_df["Team 2"] = display_df["team2_id"].apply(get_team_name)
            display_df["Match Date"] = display_df["match_date"]
            display_df["Venue"] = display_df["venue"]

            st.dataframe(
                display_df[["match_id", "Team 1", "Team 2", "Match Date", "Venue"]]
                .reset_index(drop=True)
            )


def run():
    st.title("🤾 Handball")

def run_handball():
    st.sidebar.title("Handball Module")
    page = st.sidebar.radio("→",[ "Add Tournament","Add Team","Add Player","View Tournaments",
                                 "Schedule Match","Update Live","Match Summary"])

    if page=="Add Tournament": add_tournament()
    if page=="Add Team": add_team()
    if page=="Add Player": add_player()
    if page=="View Tournaments": view_tournaments()
    if page=="Schedule Match": schedule_match()
    if page=="Update Live": update_live_match()
    if page=="Match Summary": view_summary()

