# hockey.py
import os
import time
from datetime import datetime
import pandas as pd
import streamlit as st

DATA = "sports_dashboard/data"
os.makedirs(DATA, exist_ok=True)

T_CSV = os.path.join(DATA, "hockey_tournaments.csv")
TEAM_CSV = os.path.join(DATA, "hockey_teams.csv")
PLAYER_CSV = os.path.join(DATA, "hockey_players.csv")
MATCH_CSV = os.path.join(DATA, "hockey_matches.csv")
SCORE_CSV = os.path.join(DATA, "hockey_events.csv")

# Headers
T_HDR    = ["tournament_id","tournament_name","start","end","location"]
TEAM_HDR = ["team_id","team_name","tournament_id"]
PLY_HDR  = ["player_id","player_name","team_id"]
MATCH_HDR = ["match_id","tournament_id","team1_id","team2_id","date","venue"]
# Added 'saves' column for GK stats
EVENT_HDR = ["match_id","period","team_id","scorer","assist","event_type","penalty","saves","timestamp"]

TOTAL_MATCH_SECONDS = 3 * 20 * 60  # 3 periods x 20 minutes = 3600 seconds

def init():
    for f,h in [
        (T_CSV,T_HDR),
        (TEAM_CSV,TEAM_HDR),
        (PLAYER_CSV,PLY_HDR),
        (MATCH_CSV,MATCH_HDR),
        (SCORE_CSV,EVENT_HDR)
    ]:
        if not os.path.exists(f):
            pd.DataFrame(columns=h).to_csv(f,index=False)

def load(f,h):
    if not os.path.exists(f):
        return pd.DataFrame(columns=h)
    df = pd.read_csv(f)
    # ensure new column 'saves' exists if file is old
    if f == SCORE_CSV and "saves" not in df.columns:
        df["saves"] = 0
    return df

def save(df,f): df.to_csv(f,index=False)

init()
# --------------- ADMIN ---------------
def add_tournament():
    st.subheader("🏆 Add Tournament")
    df = load(T_CSV,T_HDR)
    n = st.text_input("Tournament Name")
    s = st.date_input("Start")
    e = st.date_input("End")
    loc = st.text_input("Location")
    if st.button("Save Tournament") and n:
        new = df["tournament_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [new,n,s,e,loc]
        save(df,T_CSV)
        st.success("Tournament added!")

def add_team():
    st.subheader("➕ Add Team")
    df = load(TEAM_CSV,TEAM_HDR)
    tdf= load(T_CSV,T_HDR)
    if tdf.empty: 
        st.warning("Add tournament first")
        return

    tn = st.text_input("Team Name")
    tour = st.selectbox("Tournament",tdf["tournament_name"])
    tid = tdf.loc[tdf["tournament_name"]==tour,"tournament_id"].values[0]
    if st.button("Save") and tn:
        new = df["team_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [new,tn,tid]
        save(df,TEAM_CSV)
        st.success("Team added!")

def add_player():
    st.subheader("➕ Add Player")
    df = load(PLAYER_CSV,PLY_HDR)
    t = load(TEAM_CSV,TEAM_HDR)
    if t.empty: 
        st.warning("Add team first")
        return

    p = st.text_input("Player Name")
    tm = st.selectbox("Team",t["team_name"])
    tid = t.loc[t["team_name"]==tm,"team_id"].values[0]

    if st.button("Save Player") and p:
        new = df["player_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [new,p,tid]
        save(df,PLAYER_CSV)
        st.success("Player Added!")
# --------------- MATCH SCHEDULING ---------------
def schedule_match():
    st.subheader("📅 Schedule Match")
    df = load(MATCH_CSV,MATCH_HDR)
    teams = load(TEAM_CSV,TEAM_HDR)
    tours = load(T_CSV,T_HDR)

    if tours.empty or teams.empty: 
        st.warning("Add team+tour first")
        return

    tour = st.selectbox("Tournament",tours["tournament_name"])
    tid = tours.loc[tours["tournament_name"]==tour,"tournament_id"].values[0]
    valid = teams[teams["tournament_id"]==tid]
    if len(valid)<2: 
        st.warning("Need 2+ teams")
        return

    t1 = st.selectbox("Team 1",valid["team_name"])
    t2 = st.selectbox("Team 2",[x for x in valid["team_name"] if x != t1])

    d = st.date_input("Match Date")
    v = st.text_input("Venue")

    if st.button("Schedule"):
        mid = df["match_id"].max()+1 if not df.empty else 1
        df.loc[len(df)] = [
            mid,tid,
            valid.loc[valid["team_name"]==t1,"team_id"].values[0],
            valid.loc[valid["team_name"]==t2,"team_id"].values[0],
            d,v
        ]
        save(df,MATCH_CSV)
        st.success(f"Match Scheduled! (ID {mid})")
# --------------- LIVE MATCH (TIMER + SCORE) ---------------
def _init_timer_for_match(mid):
    key_prefix = f"hockey_{mid}_"
    if st.session_state.get(key_prefix + "current_match") != mid:
        st.session_state[key_prefix + "current_match"] = mid
        st.session_state[key_prefix + "start"] = time.time()
        st.session_state[key_prefix + "paused"] = False
        st.session_state[key_prefix + "paused_time"] = 0.0
        st.session_state[key_prefix + "pause_start"] = None

def _timer_block(mid):
    key_prefix = f"hockey_{mid}_"
    _init_timer_for_match(mid)

    start = st.session_state[key_prefix + "start"]
    paused = st.session_state[key_prefix + "paused"]
    paused_time = st.session_state[key_prefix + "paused_time"]
    pause_start = st.session_state[key_prefix + "pause_start"]

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⏸ Pause Timer"):
            if not paused:
                st.session_state[key_prefix + "paused"] = True
                st.session_state[key_prefix + "pause_start"] = time.time()
    with c2:
        if st.button("▶ Resume Timer"):
            if paused:
                st.session_state[key_prefix + "paused"] = False
                extra = time.time() - st.session_state[key_prefix + "pause_start"]
                st.session_state[key_prefix + "paused_time"] += extra
                st.session_state[key_prefix + "pause_start"] = None
    with c3:
        if st.button("🔄 Reset Timer"):
            st.session_state[key_prefix + "start"] = time.time()
            st.session_state[key_prefix + "paused"] = False
            st.session_state[key_prefix + "paused_time"] = 0.0
            st.session_state[key_prefix + "pause_start"] = None

    # recompute updated state
    start = st.session_state[key_prefix + "start"]
    paused = st.session_state[key_prefix + "paused"]
    paused_time = st.session_state[key_prefix + "paused_time"]
    pause_start = st.session_state[key_prefix + "pause_start"]

    if paused and pause_start is not None:
        elapsed = pause_start - start - paused_time
    else:
        elapsed = time.time() - start - paused_time

    elapsed = max(0, elapsed)
    remaining = max(0, TOTAL_MATCH_SECONDS - elapsed)

    # Determine current period from elapsed
    if remaining <= 0:
        period_label = "Full Time"
        current_period = 3
    else:
        period_seconds = 20 * 60
        current_period = int(elapsed // period_seconds) + 1
        current_period = min(current_period, 3)
        period_label = f"Period {current_period}"

    rem_min = int(remaining // 60)
    rem_sec = int(remaining % 60)
    el_min = int(elapsed // 60)
    el_sec = int(elapsed % 60)

    st.markdown(
        f"⏱ **Match Time:** {el_min:02d}:{el_sec:02d} elapsed | "
        f"{rem_min:02d}:{rem_sec:02d} remaining | {period_label}"
    )

    match_over = remaining == 0
    return current_period, match_over


def live_score():
    st.subheader("🏒 Live Match Event Logging")
    match_df = load(MATCH_CSV,MATCH_HDR)
    if match_df.empty: 
        st.warning("No matches")
        return

    matches = match_df["match_id"].tolist()
    mid = st.selectbox("Match",matches)
    match = match_df[match_df["match_id"]==mid].iloc[0]

    teams = load(TEAM_CSV,TEAM_HDR)
    ply = load(PLAYER_CSV,PLY_HDR)
    scores_df = load(SCORE_CSV,EVENT_HDR)

    t1 = teams.loc[teams["team_id"]==match["team1_id"],"team_name"].values[0]
    t2 = teams.loc[teams["team_id"]==match["team2_id"],"team_name"].values[0]

    st.write(f"### {t1} vs {t2}")

    # ---- Timer & Period from clock ----
    current_period, match_over = _timer_block(mid)

    # ---- Live Scoreboard ----
    if not scores_df.empty:
        goals = scores_df[(scores_df["match_id"] == mid) & (scores_df["event_type"]=="Goal")]
        team_goals = goals.groupby("team_id")["event_type"].count()
        score1 = int(team_goals.get(match["team1_id"],0))
        score2 = int(team_goals.get(match["team2_id"],0))
    else:
        score1 = score2 = 0

    st.markdown(f"## 🔴 Live Score: **{t1} {score1} - {score2} {t2}**")

    if match_over:
        st.warning("⏰ Match time completed (3 x 20 mins). You can still view stats, but avoid logging new events.")
        # We continue showing stats but you might choose to return here if you want to strictly block logging.

    # period defaults to current_period from timer
    period = st.selectbox("Period", [1,2,3], index=current_period-1)

    team = st.selectbox("Team", [t1,t2])
    tid = match["team1_id"] if team==t1 else match["team2_id"]
    pteam = ply[ply["team_id"]==tid]["player_name"].tolist()

    event = st.selectbox("Event Type",["Goal","Assist","Penalty","Save"])
    scorer=assist=penalty=""
    saves_count = 0

    if event=="Goal":
        scorer = st.selectbox("Scorer",pteam)
        assist = st.selectbox("Assist",["None"]+pteam)
        if assist=="None": assist=""
    elif event=="Penalty":
        scorer = st.selectbox("Penalty on Player",pteam)
        penalty = st.text_input("Penalty Details")
    elif event=="Save":
        scorer = st.selectbox("Goalkeeper",pteam)
        saves_count = st.number_input("Number of Saves",1,10,1)
    elif event=="Assist":
        # pure assist event if you want to log chance creation separately
        scorer = st.selectbox("Creator (Assist Player)",pteam)

    if st.button("Record Event"):
        df = load(SCORE_CSV,EVENT_HDR)
        df.loc[len(df)] = [mid,period,tid,scorer,assist,event,penalty,saves_count,datetime.now()]
        save(df,SCORE_CSV)
        st.success("Event Logged!")
        st.experimental_rerun()  # refresh live score

# --------------- SUMMARY + AWARDS + PLAYER STATS ---------------
def summary():
    st.subheader("📊 Match Summary")
    df = load(SCORE_CSV,EVENT_HDR)
    if df.empty: 
        st.info("No data")
        return

    mid = st.selectbox("Match",df["match_id"].unique())
    sub = df[df["match_id"]==mid].copy()

    # ensure saves numeric
    if "saves" not in sub.columns:
        sub["saves"] = 0
    sub["saves"] = pd.to_numeric(sub["saves"], errors="coerce").fillna(0).astype(int)

    teams = load(TEAM_CSV,TEAM_HDR)
    match = load(MATCH_CSV,MATCH_HDR)
    meta = match[match["match_id"]==mid].iloc[0]

    t1 = teams.loc[teams["team_id"]==meta["team1_id"],"team_name"].values[0]
    t2 = teams.loc[teams["team_id"]==meta["team2_id"],"team_name"].values[0]

    goals = sub[sub["event_type"]=="Goal"]
    result = goals.groupby("team_id")["event_type"].count()
    score1 = int(result.get(meta["team1_id"],0))
    score2 = int(result.get(meta["team2_id"],0))

    st.success(f"Final: **{t1} {score1} - {score2} {t2}**")

    st.markdown("### All Events")
    st.dataframe(sub)

    # ----- Player Stats Table -----
    st.markdown("### 👥 Player Stats (Goals / Assists / Saves)")
    # goals per player
    g_stats = goals.groupby("scorer")["event_type"].count().reset_index()
    g_stats.columns = ["player_name","goals"]

    # assists per player
    a_df = sub[sub["assist"]!=""]
    if not a_df.empty:
        a_stats = a_df.groupby("assist")["assist"].count().reset_index()
        a_stats.columns = ["player_name","assists"]
    else:
        a_stats = pd.DataFrame(columns=["player_name","assists"])

    # saves per player
    s_df = sub[sub["saves"]>0]
    if not s_df.empty:
        s_stats = s_df.groupby("scorer")["saves"].sum().reset_index()
        s_stats.columns = ["player_name","saves"]
    else:
        s_stats = pd.DataFrame(columns=["player_name","saves"])

    # merge all
    stats = pd.merge(g_stats, a_stats, on="player_name", how="outer")
    stats = pd.merge(stats, s_stats, on="player_name", how="outer").fillna(0)
    stats[["goals","assists","saves"]] = stats[["goals","assists","saves"]].astype(int)

    st.dataframe(stats.sort_values(["goals","assists","saves"], ascending=[False,False,False]).reset_index(drop=True))

    # ----- Awards -----
    st.markdown("---")
    st.subheader("🏆 Awards")

    # Best Striker
    if not g_stats.empty:
        best_striker = g_stats.sort_values("goals",ascending=False).iloc[0]
        st.success(f"🔥 Best Striker: **{best_striker['player_name']}** – {best_striker['goals']} goals")

    # Best Creator
    if not a_stats.empty:
        best_creator = a_stats.sort_values("assists",ascending=False).iloc[0]
        st.info(f"🎯 Best Creator: **{best_creator['player_name']}** – {best_creator['assists']} assists")

    # Best Goalkeeper
    if not s_stats.empty:
        best_gk = s_stats.sort_values("saves",ascending=False).iloc[0]
        st.warning(f"🧤 Best Goalkeeper: **{best_gk['player_name']}** – {best_gk['saves']} saves")

# --------------- TOURNAMENT VIEW + LEADERBOARD ---------------
def view_tournaments():
    st.subheader("📋 View Tournaments")
    
    tournaments = load(T_CSV, T_HDR)
    matches = load(MATCH_CSV, MATCH_HDR)
    teams = load(TEAM_CSV, TEAM_HDR)
    scores = load(SCORE_CSV, EVENT_HDR)

    if tournaments.empty:
        st.warning("No tournaments found.")
        return
    
    tournament_names = tournaments["tournament_name"].tolist()
    selected_tournament = st.selectbox("Select Tournament", tournament_names)

    if not selected_tournament:
        return

    tournament_id = int(
        tournaments.loc[
            tournaments["tournament_name"] == selected_tournament,
            "tournament_id"
        ].values[0]
    )

    t_matches = matches[matches["tournament_id"] == tournament_id]

    st.markdown(f"### Matches in {selected_tournament}")
    if t_matches.empty:
        st.info("No matches scheduled for this tournament yet.")
    else:
        def get_team_name(team_id):
            val = teams.loc[teams["team_id"] == team_id, "team_name"]
            return val.values[0] if not val.empty else "Unknown"

        display_df = t_matches.copy()
        display_df["Team 1"] = display_df["team1_id"].apply(get_team_name)
        display_df["Team 2"] = display_df["team2_id"].apply(get_team_name)
        display_df["Match Date"] = display_df["date"]
        display_df["Venue"] = display_df["venue"]

        st.dataframe(
            display_df[["match_id", "Team 1", "Team 2", "Match Date", "Venue"]]
            .reset_index(drop=True)
        )

    # -------- LEADERBOARD --------
    st.markdown("---")
    st.subheader("🏆 Tournament Leaderboard")

    teams_in_tour = teams[teams["tournament_id"] == tournament_id].copy()
    if teams_in_tour.empty:
        st.info("No teams found for this tournament.")
        return

    # init standings
    standings = pd.DataFrame({
        "team_id": teams_in_tour["team_id"],
        "team_name": teams_in_tour["team_name"],
        "played": 0,
        "won": 0,
        "draw": 0,
        "lost": 0,
        "gf": 0,
        "ga": 0,
        "points": 0
    }).set_index("team_id")

    if not t_matches.empty:
        for _, row in t_matches.iterrows():
            mid = row["match_id"]
            t1 = row["team1_id"]
            t2 = row["team2_id"]

            if scores.empty:
                g1 = g2 = 0
            else:
                sub = scores[(scores["match_id"]==mid) & (scores["event_type"]=="Goal")]
                goals_team = sub.groupby("team_id")["event_type"].count()
                g1 = int(goals_team.get(t1,0))
                g2 = int(goals_team.get(t2,0))

            # update basic stats
            for tid, gf, ga in [(t1,g1,g2),(t2,g2,g1)]:
                if tid not in standings.index:
                    continue
                standings.at[tid,"played"] += 1
                standings.at[tid,"gf"] += gf
                standings.at[tid,"ga"] += ga

            # result
            if g1 > g2:   # team1 wins
                if t1 in standings.index:
                    standings.at[t1,"won"] += 1
                    standings.at[t1,"points"] += 3
                if t2 in standings.index:
                    standings.at[t2,"lost"] += 1
            elif g2 > g1: # team2 wins
                if t2 in standings.index:
                    standings.at[t2,"won"] += 1
                    standings.at[t2,"points"] += 3
                if t1 in standings.index:
                    standings.at[t1,"lost"] += 1
            else:         # draw
                if t1 in standings.index:
                    standings.at[t1,"draw"] += 1
                    standings.at[t1,"points"] += 1
                if t2 in standings.index:
                    standings.at[t2,"draw"] += 1
                    standings.at[t2,"points"] += 1

    standings["gd"] = standings["gf"] - standings["ga"]
    standings = standings.sort_values(
        ["points","gd","gf"],
        ascending=[False,False,False]
    ).reset_index()

    st.dataframe(
        standings[["team_name","played","won","draw","lost","gf","ga","gd","points"]]
    )

def run():
    st.title("🏒 Hockey Dashboard")

def run_hockey():
    st.sidebar.title("Hockey Module")
    nav = st.sidebar.radio(
        "Menu",
        [
            "Add Tournament","Add Team","Add Player",
            "View Tournaments","Schedule Match",
            "Update Live Score","Match Summary"
        ]
    )
    if nav=="Add Tournament": add_tournament()
    elif nav=="Add Team": add_team()
    elif nav=="Add Player": add_player()
    elif nav=="View Tournaments": view_tournaments()
    elif nav=="Schedule Match": schedule_match()
    elif nav=="Update Live Score": live_score()
    elif nav=="Match Summary": summary()

