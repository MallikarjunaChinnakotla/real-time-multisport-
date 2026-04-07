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
    phone=st.text_input("Player Phone Number")
    team=st.selectbox("Team",teams["team_name"])
    tid=teams.loc[teams["team_name"]==team,"team_id"].values[0]

    if st.button("Save Player") and name:
        new=df["player_id"].max()+1 if not df.empty else 1
        
        if "phone_number" not in df.columns:
             df["phone_number"] = ""
             
        new_row = pd.DataFrame([[new,name,tid,str(phone)]], columns=["player_id","player_name","team_id","phone_number"])
        df = pd.concat([df, new_row], ignore_index=True)
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

    tours = load(T_CSV,T_HDR)
    if tours.empty:
        st.warning("No tournaments found")
        return

    # 1. Select Tournament
    t_names = tours["tournament_name"].tolist()
    sel_tour = st.selectbox("Select Tournament", t_names)
    tid = tours.loc[tours["tournament_name"]==sel_tour,"tournament_id"].values[0]

    # 2. Filter matches
    t_matches = matches[matches["tournament_id"] == tid].copy()
    if t_matches.empty:
        st.info("No matches in this tournament")
        return

    # 3. Match Selection (Local Numbering)
    t_matches = t_matches.sort_values("match_id")
    t_matches["local_id"] = range(1, len(t_matches)+1)

    teams=load(TEAM_CSV,TEAM_HDR)
    def get_tn(tid):
        r = teams[teams["team_id"]==tid]
        return r.iloc[0]["team_name"] if not r.empty else "Unknown"

    match_opts = {}
    for _, r in t_matches.iterrows():
        mid_val = r["match_id"]
        lid = r["local_id"]
        t1 = get_tn(r["team1_id"])
        t2 = get_tn(r["team2_id"])
        lbl = f"Match #{lid}: {t1} vs {t2} ({r['date']})"
        match_opts[lbl] = mid_val

    sel_lbl = st.selectbox("Select Match", list(match_opts.keys()))
    mid = match_opts[sel_lbl]
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

    # --- Button-Based Scoring Flow ---
    st.divider()
    if "sb_step" not in st.session_state:
        st.session_state["sb_step"] = "SELECT_EVENT"
    if "sb_event_type" not in st.session_state:
        st.session_state["sb_event_type"] = None

    def reset_sb_flow():
        st.session_state["sb_step"] = "SELECT_EVENT"
        st.session_state["sb_event_type"] = None

    def safe_rerun():
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()

    if st.button("❌ Reset Form"):
        reset_sb_flow()
        safe_rerun()

    # STEP 1: Event Selection
    if st.session_state["sb_step"] == "SELECT_EVENT":
        st.markdown("#### Select Play Result")
        c1, c2, c3 = st.columns(3)
        if c1.button("⚾ Hit / Run", use_container_width=True):
            st.session_state["sb_event_type"] = "Hit"
            st.session_state["sb_step"] = "DETAILS"
            safe_rerun()
        if c2.button("🛑 Out", use_container_width=True):
            st.session_state["sb_event_type"] = "Out"
            st.session_state["sb_step"] = "DETAILS"
            safe_rerun()
        if c3.button("👟 Walk / Other", use_container_width=True):
            st.session_state["sb_event_type"] = "Other"
            st.session_state["sb_step"] = "DETAILS"
            safe_rerun()

    # STEP 2: Details
    if st.session_state["sb_step"] == "DETAILS":
        evt = st.session_state["sb_event_type"]
        st.info(f"Recording: **{evt}**")
        
        with st.form("sb_play_form"):
            inn_val = st.selectbox("Inning", range(1, 8))
            outs_val = st.number_input("Current Outs (0-2)", 0, 2, 0)
            
            bat_team = st.selectbox("Batting Team", [t1, t2])
            
            # Opposting team is pitcher team
            pit_team_name = t1 if bat_team == t2 else t2
            
            tid = m["team1_id"] if bat_team == t1 else m["team2_id"]
            
            # Batters list
            b_list = ply[ply["team_id"]==tid]["player_name"].tolist()
            batter_name = st.selectbox("Batter", b_list if b_list else ["Unknown"])
            
            pitcher_name = st.text_input(f"Pitcher ({pit_team_name})")
            
            runs_sc = 0
            rbi_sc = 0
            
            if evt == "Hit":
                runs_sc = st.number_input("Runs Scored on Play", 0, 4, 0)
                rbi_sc = st.number_input("RBI", 0, 4, 0)
            elif evt == "Out":
                st.info("Batter is Out.")
            
            if st.form_submit_button("✅ Record Play"):
                sc = load(SCORE_CSV, SCORE_HDR)
                # For 'Out', usually we increment outs, but here we just log the play event.
                # Logic for auto-incrementing game outs could be added later.
                final_outs = outs_val + 1 if evt == "Out" else outs_val
                
                sc.loc[len(sc)] = [mid, inn_val, final_outs, tid, runs_sc, rbi_sc, batter_name, pitcher_name, datetime.now()]
                save(sc, SCORE_CSV)
                st.success("Play Recorded!")
                reset_sb_flow()
                safe_rerun()
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

