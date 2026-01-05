import streamlit as st
from sports.background import set_bg
import pandas as pd
import os
import time
from datetime import datetime

# ---------- Paths ----------
DATA_PATH = "sports_data/football"
TOURNAMENTS_CSV = os.path.join(DATA_PATH, "football_tournaments.csv")
TEAMS_CSV = os.path.join(DATA_PATH, "football_teams.csv")
PLAYERS_CSV = os.path.join(DATA_PATH, "football_players.csv")
MATCHES_CSV = os.path.join(DATA_PATH, "football_matches.csv")
SCORES_CSV = os.path.join(DATA_PATH, "football_scores.csv")

MATCH_PHASES = ["1st Half", "Half-Time", "2nd Half", "Full-Time"]

# ---------- Utils ----------
def load_csv(path, columns=None):
    if os.path.exists(path):
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip()
        return df
    else:
        return pd.DataFrame(columns=columns) if columns else pd.DataFrame()

def save_csv(df, path):
    os.makedirs(DATA_PATH, exist_ok=True)
    df.to_csv(path, index=False)

# ---------- Add Tournament ----------
def add_tournament():
    st.subheader("🏆 Add Football Tournament")
    df = load_csv(TOURNAMENTS_CSV, ["tournament_id","tournament_name","start_date","end_date","location"])

    name = st.text_input("Tournament Name")
    start = st.date_input("Start Date")
    end = st.date_input("End Date")
    loc = st.text_input("Location")

    if st.button("Add Tournament") and name:
        new_id = df["tournament_id"].max() + 1 if not df.empty else 1
        df.loc[len(df)] = [new_id,name,start,end,loc]
        save_csv(df,TOURNAMENTS_CSV)
        st.success("Tournament Added!")

# ---------- View Tournaments ----------
def view_tournaments():
    st.subheader("📋 View Tournaments")
    tdf = load_csv(TOURNAMENTS_CSV)
    mdf = load_csv(MATCHES_CSV)
    teams = load_csv(TEAMS_CSV)

    if tdf.empty: return st.warning("No tournaments found")

    tname = st.selectbox("Select Tournament", tdf["tournament_name"])
    tid = tdf.loc[tdf["tournament_name"]==tname,"tournament_id"].values[0]

    matches = mdf[mdf["tournament_id"]==tid]
    if matches.empty: return st.info("No matches yet")

    def g(x): return teams[teams["team_id"]==x]["team_name"].values[0]
    disp = matches.copy()
    disp["Team 1"] = disp["team1_id"].apply(g)
    disp["Team 2"] = disp["team2_id"].apply(g)

    st.dataframe(disp[["match_id","Team 1","Team 2","match_date","venue"]])

# ---------- Add Team ----------
def add_team():
    st.subheader("➕ Add Football Team")
    tdf = load_csv(TOURNAMENTS_CSV)
    if tdf.empty: return st.warning("Add tournament first")

    tname = st.selectbox("Select Tournament",tdf["tournament_name"])
    tid = tdf[tdf["tournament_name"]==tname]["tournament_id"].values[0]
    name = st.text_input("Team Name")

    if st.button("Add Team") and name:
        df = load_csv(TEAMS_CSV, ["team_id","team_name","tournament_id"])
        new_id = df["team_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [new_id,name,tid]
        save_csv(df,TEAMS_CSV)
        st.success("Team Added")

# ---------- Add Player ----------
def add_player():
    st.subheader("👤 Add Football Player")
    teams = load_csv(TEAMS_CSV)
    if teams.empty: return st.warning("Add team first")

    tname = st.selectbox("Team",teams["team_name"])
    tid = teams[teams["team_name"]==tname]["team_id"].values[0]
    pname = st.text_input("Player Name")

    if st.button("Add Player") and pname:
        df = load_csv(PLAYERS_CSV, ["player_id","player_name","team_id"])
        new_id = df["player_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [new_id,pname,tid]
        save_csv(df,PLAYERS_CSV)
        st.success("Player Added")

# ---------- Schedule Match ----------
def schedule_match():
    st.subheader("📅 Schedule Match")
    tdf = load_csv(TOURNAMENTS_CSV)
    teams = load_csv(TEAMS_CSV)

    if tdf.empty or teams.empty: return st.warning("Add tournament & teams first")

    tname = st.selectbox("Tournament",tdf["tournament_name"])
    tid = tdf[tdf["tournament_name"]==tname]["tournament_id"].values[0]
    tlist = teams[teams["tournament_id"]==tid]["team_name"].tolist()

    t1 = st.selectbox("Team 1",tlist)
    t2 = st.selectbox("Team 2",[x for x in tlist if x!=t1])
    d = st.date_input("Match Date")
    v = st.text_input("Venue")

    if st.button("Schedule"):
        df = load_csv(MATCHES_CSV, ["match_id","tournament_id","team1_id","team2_id","match_date","venue"])
        mid = df["match_id"].max()+1 if not df.empty else 1
        id1 = teams[teams["team_name"]==t1]["team_id"].values[0]
        id2 = teams[teams["team_name"]==t2]["team_id"].values[0]
        df.loc[len(df)] = [mid,tid,id1,id2,d,v]
        save_csv(df,MATCHES_CSV)
        st.success("Match Scheduled!")

def update_score():
    st.subheader("⚽ Live Match Events")

    matches = load_csv(MATCHES_CSV)
    teams = load_csv(TEAMS_CSV)
    players = load_csv(PLAYERS_CSV)
    df = load_csv(SCORES_CSV, ["match_id","minute","event_type","team_name","player_name","xg","timestamp"])

    if matches.empty: return st.warning("No matches found")

    match_id = st.selectbox("Select Match ID", matches["match_id"].unique())
    match = matches[matches["match_id"]==match_id].iloc[0]

    team1 = teams[teams["team_id"]==match["team1_id"]]["team_name"].values[0]
    team2 = teams[teams["team_id"]==match["team2_id"]]["team_name"].values[0]

    players_t1 = players[players["team_id"]==match["team1_id"]]["player_name"].tolist()
    players_t2 = players[players["team_id"]==match["team2_id"]]["player_name"].tolist()

    # Timer implemented (90 min)
    total_sec = 90*60
    if "start" not in st.session_state or st.session_state.get("mid")!=match_id:
        st.session_state.update({"start":time.time(),"pause":0,"paused":False,"mid":match_id})

    col1,col2 = st.columns(2)
    if col1.button("Pause"): st.session_state["paused"]=True; st.session_state["pause_at"]=time.time()
    if col2.button("Resume"):
        st.session_state["paused"]=False
        st.session_state["pause"]+= time.time()-st.session_state["pause_at"]

    elapsed = time.time()-st.session_state["start"]-st.session_state["pause"]
    remaining = max(total_sec-elapsed,0)

    st.markdown(f"⏳ Remaining: **{int(remaining//60):02d}:{int(remaining%60):02d}**")

    sc_team = st.selectbox("Team",[team1,team2])
    plist = players_t1 if sc_team==team1 else players_t2
    player = st.selectbox("Player",plist)

    event = st.selectbox("Event Type",["Goal","Assist","Save","Shot on Target"])
    xg = 0.0
    if event in ["Goal","Shot on Target"]:
        xg = st.slider("Expected Goal (xG)",0.01,1.0,0.30,0.01)

    minute = min(int(elapsed//60),90)

    if st.button("Record Event"):
        df.loc[len(df)] = [match_id,minute,event,sc_team,player,xg,datetime.now()]
        save_csv(df,SCORES_CSV)
        st.success("Event Recorded!")

    goals = df[(df["match_id"]==match_id)&(df["event_type"]=="Goal")].groupby("team_name").size().to_dict()
    st.info(f"Score: {team1} {goals.get(team1,0)} - {goals.get(team2,0)} {team2}")

def view_summary():
    st.subheader("📊 Match Summary / Awards")

    df = load_csv(SCORES_CSV)
    if df.empty:
        st.info("No data.")
        return
    mid = st.number_input("Match ID",min_value=1,step=1)  
    data = df[df["match_id"]==mid]

    st.dataframe(data)

    st.markdown("### 🏅 Player Awards")

    # Best Striker
    goals = data[data["event_type"]=="Goal"]
    if not goals.empty:
        goals["xg"]=goals["xg"].astype(float)
        g = goals.groupby("player_name").agg(Goals=("event_type","count"),Total_xG=("xg","sum"))
        g["Score"] = g["Goals"]*4 + g["Total_xG"]*3
        best = g.sort_values("Score",ascending=False).head(1)
        st.success(f"⚽ Best Striker: **{best.index[0]}** | Goals: {best.iloc[0]['Goals']} | xG: {best.iloc[0]['Total_xG']:.2f}")

    # Top Creator
    assists = data[data["event_type"]=="Assist"]
    if not assists.empty:
        a = assists.groupby("player_name").size().sort_values(ascending=False)
        st.info(f"🎯 Top Creator: **{a.idxmax()}** ({a.max()} assists)")

    # Best Goalkeeper
    saves = data[data["event_type"]=="Save"]
    if not saves.empty:
        s = saves.groupby("player_name").size().sort_values(ascending=False)
        st.warning(f"🧤 Best Goalkeeper: **{s.idxmax()}** ({s.max()} saves)")
def run():
    st.title(" ⚽ Football Dashboard")
    st.write("Live Football stats go here...")
# ---------- Main ----------
def run_football():
    st.sidebar.title("⚽ Football Module")
    menu = ["Add Tournament","Add Team","Add Player","View Tournaments","Schedule Match","Update Live Score","View Match Summary"]
    ch = st.sidebar.radio("Select Option", menu)

    if ch=="Add Tournament": add_tournament()
    if ch=="Add Team": add_team()
    if ch=="Add Player": add_player()
    if ch=="View Tournaments": view_tournaments()
    if ch=="Schedule Match": schedule_match()
    if ch=="Update Live Score": update_score()
    if ch=="View Match Summary": view_summary()

