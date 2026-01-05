# table_tennis.py
import os
import pandas as pd
import streamlit as st
from datetime import datetime

DATA_DIR = "sports_dashboard/data"
os.makedirs(DATA_DIR, exist_ok=True)

T_CSV = os.path.join(DATA_DIR, "tt_tournaments.csv")
TEAM_CSV = os.path.join(DATA_DIR, "tt_teams.csv")
PLAYER_CSV = os.path.join(DATA_DIR, "tt_players.csv")
MATCH_CSV = os.path.join(DATA_DIR, "tt_matches.csv")
SCORE_CSV = os.path.join(DATA_DIR, "tt_scores.csv")

# CSV HEADERS
T_HDR = ["tournament_id", "tournament_name", "start_date", "end_date", "location"]
TEAM_HDR = ["team_id", "team_name", "tournament_id"]
PLAYER_HDR = ["player_id", "player_name", "team_id"]
MATCH_HDR = ["match_id", "tournament_id", "team1_id", "team2_id", "match_date", "venue", "format"]
SCORE_HDR = ["match_id", "set_no", "team_id", "points", "timestamp"]


def init_files():
    for f, h in [(T_CSV, T_HDR),(TEAM_CSV, TEAM_HDR),(PLAYER_CSV, PLAYER_HDR),
                 (MATCH_CSV, MATCH_HDR),(SCORE_CSV, SCORE_HDR)]:
        if not os.path.exists(f):
            pd.DataFrame(columns=h).to_csv(f, index=False)


def load_csv(p, h): return pd.read_csv(p) if os.path.exists(p) else pd.DataFrame(columns=h)
def save_csv(df, p): df.to_csv(p, index=False)

init_files()

def add_tournament():
    st.subheader("🏆 Add Tournament")
    df = load_csv(T_CSV, T_HDR)
    name = st.text_input("Tournament Name")
    loc = st.text_input("Location")
    s = st.date_input("Start")
    e = st.date_input("End")

    if st.button("ADD"):
        new_id = df["tournament_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [new_id, name, s, e, loc]
        save_csv(df, T_CSV)
        st.success("Tournament Added!")

def add_team():
    st.subheader("➕ Add Team")
    df = load_csv(TEAM_CSV, TEAM_HDR)
    tours = load_csv(T_CSV, T_HDR)
    if tours.empty: return st.warning("Add a tournament first")

    team = st.text_input("Team Name")
    tour = st.selectbox("Tournament", tours["tournament_name"])

    tid = tours.loc[tours["tournament_name"]==tour,"tournament_id"].values[0]
    if st.button("Save Team"):
        new_id = df["team_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [new_id, team, tid]
        save_csv(df, TEAM_CSV)
        st.success("Team added")


def add_player():
    st.subheader("➕ Add Player")
    df = load_csv(PLAYER_CSV, PLAYER_HDR)
    teams = load_csv(TEAM_CSV, TEAM_HDR)
    if teams.empty: return st.warning("Add teams first")

    p = st.text_input("Player Name")
    tm = st.selectbox("Team", teams["team_name"])
    tid = teams.loc[teams["team_name"]==tm,"team_id"].values[0]

    if st.button("Save Player"):
        pid = df["player_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [pid,p,tid]
        save_csv(df, PLAYER_CSV)
        st.success("Player added!")

def schedule_match():
    st.subheader("📅 Schedule Match")
    df = load_csv(MATCH_CSV, MATCH_HDR)
    teams = load_csv(TEAM_CSV, TEAM_HDR)
    tours = load_csv(T_CSV, T_HDR)
    if tours.empty or teams.empty: return st.warning("Add teams+tournaments first")

    tour = st.selectbox("Tournament", tours["tournament_name"])
    tid = tours.loc[tours["tournament_name"]==tour,"tournament_id"].values[0]

    valid = teams[teams["tournament_id"]==tid]
    if len(valid)<2: return st.error("Need 2+ teams")

    t1 = st.selectbox("Team 1", valid["team_name"])
    t2 = st.selectbox("Team 2", [x for x in valid["team_name"] if x!=t1])

    fmt = st.radio("Match Format",["Single Set (21)","Best of 3 (11 per set)"])
    d = st.date_input("Match Date")
    venue = st.text_input("Venue")

    if st.button("Schedule"):
        mid = df["match_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [mid,tid,
                           valid.loc[valid["team_name"]==t1,"team_id"].values[0],
                           valid.loc[valid["team_name"]==t2,"team_id"].values[0],
                           d,venue,fmt]
        save_csv(df, MATCH_CSV)
        st.success("Match scheduled!")

def update_live():
    st.subheader("🏓 Live Scoring")
    matches = load_csv(MATCH_CSV, MATCH_HDR)
    if matches.empty: return st.warning("No matches")

    m = st.selectbox("Select Match", matches["match_id"])
    match = matches[matches["match_id"]==m].iloc[0]

    teams = load_csv(TEAM_CSV, TEAM_HDR)
    team1 = teams.loc[teams["team_id"]==match["team1_id"],"team_name"].values[0]
    team2 = teams.loc[teams["team_id"]==match["team2_id"],"team_name"].values[0]

    fmt = match["format"]
    max_sets = 1 if "Single" in fmt else 3
    max_points = 21 if "Single" in fmt else 11

    st.write(f"### Format: {fmt} | Target: {max_points} points per set")

    score_df = load_csv(SCORE_CSV, SCORE_HDR)

    set_no = st.selectbox("Set Number",range(1,max_sets+1))
    team_select = st.selectbox("Point Won By",[team1,team2])
    tid = match["team1_id"] if team_select==team1 else match["team2_id"]

    if st.button("Add Point"):
        score_df.loc[len(score_df)] = [m,set_no,tid,1,datetime.now(),datetime.now()]
        save_csv(score_df,SCORE_CSV)
        st.success("Point Added!")

    # Show live score
    st.markdown("### Current Scores")
    live = score_df[score_df["match_id"]==m]
    if not live.empty:
        r = live.groupby(["set_no","team_id"])["points"].sum().unstack(fill_value=0)

        for s in r.index:
            t1_pts = r.loc[s,match["team1_id"]]
            t2_pts = r.loc[s,match["team2_id"]]
            st.write(f"Set {s}: **{team1} {t1_pts} - {t2_pts} {team2}**")
    else:
        st.info("No points yet!")

def summary():
    st.subheader("📊 Match Summary")
    df = load_csv(SCORE_CSV, SCORE_HDR)
    if df.empty: return st.info("No scores")

    m = st.selectbox("Match",df["match_id"].unique())
    show = df[df["match_id"]==m]

    if show.empty: return st.info("No score yet")

    match = load_csv(MATCH_CSV, MATCH_HDR)
    meta = match[match["match_id"]==m].iloc[0]
    teams = load_csv(TEAM_CSV, TEAM_HDR)

    t1 = teams.loc[teams["team_id"]==meta["team1_id"],"team_name"].values[0]
    t2 = teams.loc[teams["team_id"]==meta["team2_id"],"team_name"].values[0]

    final = show.groupby(["set_no","team_id"])["points"].sum().unstack(fill_value=0)

    wins_t1 = wins_t2 = 0

    st.write("### Final Scorecard")
    for s in final.index:
        t1_pts = final.loc[s,meta["team1_id"]]
        t2_pts = final.loc[s,meta["team2_id"]]
        result = f"{t1_pts} - {t2_pts}"
        if t1_pts > t2_pts: wins_t1 += 1
        elif t2_pts > t1_pts: wins_t2 += 1
        st.write(f"Set {s}: **{team1} {result} {team2}**")

    st.success(f"🏆 Winner: {team1 if wins_t1>wins_t2 else team2}")

def view_tournaments():
    st.subheader("📋 View Tournaments")

    tournaments = load_csv(T_CSV, T_HDR)
    matches = load_csv(MATCH_CSV, MATCH_HDR)
    teams = load_csv(TEAM_CSV, TEAM_HDR)

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
            st.info("No matches scheduled for this tournament yet.")
        else:
            def get_team(team_id):
                name = teams.loc[teams["team_id"] == team_id, "team_name"]
                return name.values[0] if not name.empty else "Unknown"
            
            display_df = t_matches.copy()
            display_df["Team 1"] = display_df["team1_id"].apply(get_team)
            display_df["Team 2"] = display_df["team2_id"].apply(get_team)
            display_df["Date"] = display_df["match_date"]
            display_df["Format"] = display_df["format"]
            
            st.dataframe(
                display_df[["match_id","Team 1","Team 2","Date","venue","Format"]].reset_index(drop=True)
            )

def run():
    st.title("🏓 Table Tennis Dashboard")

def run_table_tennis():
    st.sidebar.title("Table Tennis Module")
    nav = st.sidebar.radio("Menu",
                           ["Add Tournament","Add Team","Add Player","View Tournaments",
                            "Schedule Match","Update Live Score","Match Summary"])

    if nav=="Add Tournament": add_tournament()
    if nav=="Add Team": add_team()
    if nav=="Add Player": add_player()
    if nav=="View Tournaments": view_tournaments()
    if nav=="Schedule Match": schedule_match()
    if nav=="Update Live Score": update_live()
    if nav=="Match Summary": summary()

