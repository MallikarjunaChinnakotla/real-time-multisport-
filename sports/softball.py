# softball.py
import os
import pandas as pd
import streamlit as st
from datetime import datetime

DATA = "sports_dashboard/data"
os.makedirs(DATA, exist_ok=True)

T_CSV = os.path.join(DATA,"softball_tournaments.csv")
TEAM_CSV = os.path.join(DATA,"softball_teams.csv")
PLAYER_CSV = os.path.join(DATA,"softball_players.csv")
MATCH_CSV = os.path.join(DATA,"softball_matches.csv")
SCORE_CSV = os.path.join(DATA,"softball_scores.csv")

T_HDR=["tournament_id","tournament_name","start","end","location"]
TEAM_HDR=["team_id","team_name","tournament_id"]
PLY_HDR=["player_id","player_name","team_id"]
MATCH_HDR=["match_id","tournament_id","team1_id","team2_id","date","venue"]
SCORE_HDR=["match_id","inning","outs","team_id","runs","rbi","batter","pitcher","timestamp"]

def init():
    for f,h in [(T_CSV,T_HDR),(TEAM_CSV,TEAM_HDR),
                (PLAYER_CSV,PLY_HDR),(MATCH_CSV,MATCH_HDR),(SCORE_CSV,SCORE_HDR)]:
        if not os.path.exists(f):
            pd.DataFrame(columns=h).to_csv(f,index=False)

def load(f,h):
    if not os.path.exists(f):
        return pd.DataFrame(columns=h)
    df = pd.read_csv(f)
    return df

def save(df,f): df.to_csv(f,index=False)

init()


# =============== ADMIN ===============
def add_tournament():
    st.subheader("🏆 Add Tournament")
    df=load(T_CSV,T_HDR)
    name=st.text_input("Tournament Name")
    s=st.date_input("Start")
    e=st.date_input("End")
    loc=st.text_input("Location")
    if st.button("Add Tournament") and name:
        new=df["tournament_id"].max()+1 if not df.empty else 1
        df.loc[len(df)]=[new,name,s,e,loc]
        save(df,T_CSV)
        st.success("Tournament Added!")

def add_team():
    st.subheader("➕ Add Team")
    df=load(TEAM_CSV,TEAM_HDR)
    tours=load(T_CSV,T_HDR)
    if tours.empty:
        return st.warning("Add Tournament first")

    tname=st.text_input("Team Name")
    tour=st.selectbox("Tournament",tours["tournament_name"])
    tid=tours.loc[tours["tournament_name"]==tour,"tournament_id"].values[0]

    if st.button("Save Team") and tname:
        new=df["team_id"].max()+1 if not df.empty else 1
        df.loc[len(df)]=[new,tname,tid]
        save(df,TEAM_CSV)
        st.success("Team Added!")

def add_player():
    st.subheader("➕ Add Player")
    df=load(PLAYER_CSV,PLY_HDR)
    teams=load(TEAM_CSV,TEAM_HDR)
    if teams.empty:
        return st.warning("Add Team first")

    name=st.text_input("Player Name")
    team=st.selectbox("Team",teams["team_name"])
    tid=teams.loc[teams["team_name"]==team,"team_id"].values[0]

    if st.button("Save Player") and name:
        new=df["player_id"].max()+1 if not df.empty else 1
        df.loc[len(df)]=[new,name,tid]
        save(df,PLAYER_CSV)
        st.success("Player Added!")

# ==================== MATCH SCHEDULING ====================
def schedule_match():
    st.subheader("📅 Schedule Match")
    df=load(MATCH_CSV,MATCH_HDR)
    teams=load(TEAM_CSV,TEAM_HDR)
    tours=load(T_CSV,T_HDR)

    if tours.empty or teams.empty:
        return st.warning("Add Tournament + Teams first")

    tour=st.selectbox("Tournament",tours["tournament_name"])
    tid=tours.loc[tours["tournament_name"]==tour,"tournament_id"].values[0]

    valid=teams[teams["tournament_id"]==tid]
    if len(valid)<2: return st.warning("Need 2+ Teams")

    t1=st.selectbox("Team 1",valid["team_name"])
    t2=st.selectbox("Team 2",[x for x in valid["team_name"] if x!=t1])

    date=st.date_input("Match Date")
    venue=st.text_input("Venue")

    if st.button("Schedule Match"):
        mid=df["match_id"].max()+1 if not df.empty else 1
        df.loc[len(df)]=[
            mid,tid,
            valid.loc[valid["team_name"]==t1,"team_id"].values[0],
            valid.loc[valid["team_name"]==t2,"team_id"].values[0],
            date,venue
        ]
        save(df,MATCH_CSV)
        st.success(f"Match Scheduled (ID: {mid})")


# ================ LIVE UPDATE ================
def live():
    st.subheader("🥎 Live Score")
    matches = load(MATCH_CSV,MATCH_HDR)
    if matches.empty:
        return st.info("No scheduled matches")

    mid = st.selectbox("Select Match", matches["match_id"])
    m = matches[matches["match_id"]==mid].iloc[0]

    teams=load(TEAM_CSV,TEAM_HDR)
    ply=load(PLAYER_CSV,PLY_HDR)

    t1=teams.loc[teams["team_id"]==m["team1_id"],"team_name"].values[0]
    t2=teams.loc[teams["team_id"]==m["team2_id"],"team_name"].values[0]

    # Live Scoreboard
    scores = load(SCORE_CSV,SCORE_HDR)
    sub = scores[scores["match_id"]==mid]
    result = sub.groupby("team_id")["runs"].sum()
    s1, s2 = result.get(m["team1_id"],0), result.get(m["team2_id"],0)
    st.success(f"Score: {t1} {s1} - {s2} {t2}")

    inning = st.selectbox("Inning (1 to 7)", range(1,8))
    outs = st.number_input("Outs (0-3)", 0, 3, 0)

    team = st.selectbox("Batting Team",[t1,t2])
    tid = m["team1_id"] if team==t1 else m["team2_id"]

    batters = ply[ply["team_id"]==tid]["player_name"].tolist()
    batter = st.selectbox("Batter", batters)
    pitcher = st.text_input("Pitcher Name")

    runs = st.number_input("Runs Scored",0,10,0)
    rbi = st.number_input("RBI",0,10,0)

    if st.button("Record Play"):
        sc = load(SCORE_CSV,SCORE_HDR)
        sc.loc[len(sc)] = [mid,inning,outs,tid,runs,rbi,batter,pitcher,datetime.now()]
        save(sc,SCORE_CSV)
        st.success("Play recorded!")
        st.experimental_rerun()
# =============== MATCH SUMMARY + AWARDS ===============
def summary():
    st.subheader("📊 Match Summary")
    scores = load(SCORE_CSV,SCORE_HDR)
    if scores.empty:
        return st.info("No score data")

    mid = st.selectbox("Select Match", scores["match_id"].unique())
    df = scores[scores["match_id"]==mid]
    st.dataframe(df)

    teams = load(TEAM_CSV,TEAM_HDR)
    match_info=load(MATCH_CSV,MATCH_HDR)
    meta = match_info[match_info["match_id"]==mid].iloc[0]

    t1 = teams.loc[teams["team_id"]==meta["team1_id"],"team_name"].values[0]
    t2 = teams.loc[teams["team_id"]==meta["team2_id"],"team_name"].values[0]
    runs = df.groupby("team_id")["runs"].sum()
    s1, s2 = runs.get(meta["team1_id"],0), runs.get(meta["team2_id"],0)

    st.success(f"Final Score: {t1} {s1} - {s2} {t2}")

    # ---------- Player Stats ----------
    st.markdown("### 🧾 Player Performance Statistics")

    batter_stats = df.groupby("batter").agg(
        total_runs=("runs","sum"),
        total_rbi=("rbi","sum")
    ).reset_index()
    batter_stats["performance"] = batter_stats["total_runs"] + batter_stats["total_rbi"]

    pitcher_stats = df.groupby("pitcher").agg(
        outs=("outs","sum")
    ).reset_index()

    st.dataframe(batter_stats)
    st.dataframe(pitcher_stats)

    # ---------- Awards ----------
    st.markdown("### 🥇 Awards")

    if not batter_stats.empty:
        best_batter = batter_stats.sort_values("performance",ascending=False).iloc[0]
        st.success(f"🔥 Best Batter: **{best_batter['batter']}** — "
                   f"Runs+RBI: {best_batter['performance']}")

    if not pitcher_stats.empty:
        best_pitcher = pitcher_stats.sort_values("outs",ascending=False).iloc[0]
        st.info(f"🎯 Best Pitcher: **{best_pitcher['pitcher']}** — "
                f"Outs: {best_pitcher['outs']}")

    # MVP = Runs*1.5 + RBI*1.5 + Outs*2
    df_players = batter_stats.merge(
        pitcher_stats, left_on="batter", right_on="pitcher", how="outer"
    )
    df_players["total_runs"] = df_players["total_runs"].fillna(0)
    df_players["total_rbi"] = df_players["total_rbi"].fillna(0)
    df_players["outs"] = df_players["outs"].fillna(0)

    df_players["mvp_score"] = (
        df_players["total_runs"]*1.5 +
        df_players["total_rbi"]*1.5 +
        df_players["outs"]*2
    )

    if not df_players.empty:
        mvp = df_players.sort_values("mvp_score",ascending=False).iloc[0]
        st.warning(f"🏆 MVP: **{mvp['batter']}** — Score: {mvp['mvp_score']:.1f}")

def view_tournaments():
    st.subheader("📋 View Tournaments")
    
    tournaments = load(T_CSV, T_HDR)
    matches = load(MATCH_CSV, MATCH_HDR)
    teams = load(TEAM_CSV, TEAM_HDR)

    if tournaments.empty:
        st.warning("No tournaments found.")
        return
    
    tournament_names = tournaments["tournament_name"].tolist()
    selected_tournament = st.selectbox("Select Tournament", tournament_names)

    if selected_tournament:
        st.markdown(f"### Matches in {selected_tournament}")
        
        tournament_id = int(
            tournaments.loc[
                tournaments["tournament_name"] == selected_tournament,
                "tournament_id"
            ].values[0]
        )

        tournament_matches = matches[matches["tournament_id"] == tournament_id]

        if tournament_matches.empty:
            st.info("📌 No matches scheduled yet for this tournament.")
            return

        def get_team_name(team_id):
            val = teams.loc[teams["team_id"] == team_id, "team_name"]
            return val.values[0] if not val.empty else "Unknown"

        display_df = tournament_matches.copy()
        display_df["Team 1"] = display_df["team1_id"].apply(get_team_name)
        display_df["Team 2"] = display_df["team2_id"].apply(get_team_name)

        display_df.rename(columns={"date": "Match Date", "venue": "Venue"}, inplace=True)

        st.dataframe(
            display_df[["match_id", "Team 1", "Team 2", "Match Date", "Venue"]]
            .reset_index(drop=True)
        )

# =============== MAIN ===============
def run():
    st.title("🥎 Softball Dashboard")

def run_softball():
    st.sidebar.title("Softball Module")
    nav = st.sidebar.radio("Menu",[
        "Add Tournament","Add Team","Add Player","View tournaments",
        "Schedule Match","Update Live Score","Match Summary"
    ])
    if nav=="Add Tournament": add_tournament()
    elif nav=="Add Team": add_team()
    elif nav=="Add Player": add_player()
    elif nav=="View tournaments": view_tournaments()
    elif nav=="Schedule Match": schedule_match()
    elif nav=="Update Live Score": live()
    elif nav=="Match Summary": summary()

