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
    phone = st.text_input("Phone Number")
    tm = st.selectbox("Team",t["team_name"])
    tid = t.loc[t["team_name"]==tm,"team_id"].values[0]
    uploaded = st.file_uploader("Upload Player Photo", type=['jpg', 'jpeg', 'png'])

    if st.button("Save Player") and p:
        new = df["player_id"].max()+1 if not df.empty else 1
        
        if "phone_number" not in df.columns: df["phone_number"] = ""
        if "profile_image" not in df.columns: df["profile_image"] = ""
        
        image_path = ""
        if uploaded:
            img_dir = os.path.join(DATA, "player_images")
            os.makedirs(img_dir, exist_ok=True)
            ts = int(datetime.now().timestamp())
            fname = f"{new}_{''.join(x for x in p if x.isalnum())}_{ts}.{uploaded.name.split('.')[-1]}"
            fpath = os.path.join(img_dir, fname)
            with open(fpath, "wb") as f:
                f.write(uploaded.getbuffer())
            image_path = fpath
            
        new_row = pd.DataFrame([ [new,p,tid, str(phone), image_path]], columns=["player_id","player_name","team_id","phone_number","profile_image"])
        df = pd.concat([df, new_row], ignore_index=True)
        save(df,PLAYER_CSV)
        st.success("Player Added!")
        if image_path: st.image(image_path, width=150)
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
    period_length = 20 * 60
    
    # We essentially reset timer for each period in a real app, or track total.
    # Current implementation tracks TOTAL elapsed.
    # Let's derive Countdown for current period.
    
    # Period 1: 0-20m. P2: 20-40m. P3: 40-60m.
    if elapsed < period_length:
        current_period = 1
        period_rem = period_length - elapsed
    elif elapsed < 2 * period_length:
        current_period = 2
        period_rem = (2 * period_length) - elapsed
    elif elapsed < 3 * period_length:
        current_period = 3
        period_rem = (3 * period_length) - elapsed
    else:
        current_period = 3
        period_rem = 0
        
    period_label = f"Period {current_period}"
    if remaining <= 0: period_label = "Full Time"

    rem_min = int(period_rem // 60)
    rem_sec = int(period_rem % 60)

    st.markdown(
        f"⏱ **Period Timer:** {rem_min:02d}:{rem_sec:02d} (Countdown) | {period_label}"
    )

    if not paused and remaining > 0:
        time.sleep(1)
        st.rerun()

    match_over = remaining <= 0
    return current_period, match_over


def live_score():
    st.subheader("🏒 Live Match Event Logging")
    match_df = load(MATCH_CSV,MATCH_HDR)
    if match_df.empty: 
        st.warning("No matches")
        return

    if match_df.empty: 
        st.warning("No matches")
        return

    tournaments = load(T_CSV, T_HDR)
    if tournaments.empty:
        st.warning("No tournaments found")
        return

    # 1. Select Tournament
    t_names = tournaments["tournament_name"].tolist()
    sel_tourney = st.selectbox("Select Tournament", t_names)
    tid = tournaments.loc[tournaments["tournament_name"]==sel_tourney, "tournament_id"].values[0]

    # 2. Filter Matches
    t_matches = match_df[match_df["tournament_id"]==tid].copy()
    if t_matches.empty:
        st.info("No matches in this tournament")
        return

    # 3. Match Selection (Local Numbering)
    t_matches = t_matches.sort_values("match_id")
    t_matches["local_id"] = range(1, len(t_matches)+1)

    teams_df = load(TEAM_CSV, TEAM_HDR)
    def get_tn(team_id):
        r = teams_df[teams_df["team_id"]==team_id]
        return r.iloc[0]["team_name"] if not r.empty else "Unknown"

    match_opts = {}
    for _, r in t_matches.iterrows():
        mid_val = r["match_id"]
        lid = r["local_id"]
        t1_val = get_tn(r["team1_id"])
        t2_val = get_tn(r["team2_id"])
        lbl = f"Match #{lid}: {t1_val} vs {t2_val} ({r['date']})"
        match_opts[lbl] = mid_val

    sel_lbl = st.selectbox("Select Match", list(match_opts.keys()))
    mid = match_opts[sel_lbl]
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

    # Period Breakdown
    st.markdown("#### Period Breakdown")
    p_scores = scores_df[scores_df["event_type"]=="Goal"].groupby(["period","team_id"])["event_type"].count().unstack(fill_value=0)
    for p in [1,2,3]:
        if p not in p_scores.index: p_scores.loc[p] = 0
    p_scores = p_scores.fillna(0).astype(int)

    p_display = pd.DataFrame({
        t1: [p_scores.loc[p,match["team1_id"]] if match["team1_id"] in p_scores.columns else 0 for p in [1,2,3]],
        t2: [p_scores.loc[p,match["team2_id"]] if match["team2_id"] in p_scores.columns else 0 for p in [1,2,3]]
    }, index=["P1","P2","P3"]).T
    st.dataframe(p_display)

    if match_over:
        st.warning("⏰ Match time completed (3 x 20 mins). You can still view stats, but avoid logging new events.")
        # We continue showing stats but you might choose to return here if you want to strictly block logging.

    # period defaults to current_period from timer
    period = st.selectbox("Period", [1,2,3], index=current_period-1 if current_period<=3 else 2)

    team = st.selectbox("Team", [t1,t2])
    tid = match["team1_id"] if team==t1 else match["team2_id"]
    pteam = ply[ply["team_id"]==tid]["player_name"].tolist()

    # --- Button-Based Scoring Flow ---
    st.divider()    
    if "hk_step" not in st.session_state:
        st.session_state["hk_step"] = "SELECT_EVENT" 
    if "hk_event_type" not in st.session_state:
        st.session_state["hk_event_type"] = None

    def reset_hk_flow():
        st.session_state["hk_step"] = "SELECT_EVENT"
        st.session_state["hk_event_type"] = None

    def safe_rerun():
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()
            
    if st.button("❌ Reset Form"):
        reset_hk_flow()
        safe_rerun()

    # STEP 1: Select Event
    if st.session_state["hk_step"] == "SELECT_EVENT":
        st.markdown("#### Select Event")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("🏒 Goal", use_container_width=True):
             st.session_state["hk_event_type"] = "Goal"
             st.session_state["hk_step"] = "DETAILS"
             safe_rerun()
        if c2.button("🚫 Penalty", use_container_width=True):
             st.session_state["hk_event_type"] = "Penalty"
             st.session_state["hk_step"] = "DETAILS"
             safe_rerun()
        if c3.button("🧤 GK Save", use_container_width=True):
             st.session_state["hk_event_type"] = "Save"
             st.session_state["hk_step"] = "DETAILS"
             safe_rerun()
        if c4.button("👟 Assist", use_container_width=True):
             st.session_state["hk_event_type"] = "Assist"
             st.session_state["hk_step"] = "DETAILS"
             safe_rerun()

    # STEP 2: Details
    if st.session_state["hk_step"] == "DETAILS":
        evt = st.session_state["hk_event_type"]
        st.info(f"Recording: **{evt}**")
        
        with st.form("hk_event_form"):
             # Period selection defaults to timer
             pd_select = st.selectbox("Period", [1,2,3], index=current_period-1 if current_period<=3 else 2)
             
             tm = st.selectbox("Team", [t1, t2])
             tid = match["team1_id"] if tm == t1 else match["team2_id"]
             pteam_list = ply[ply["team_id"]==tid]["player_name"].tolist()
             
             scorer_val = ""
             assist_val = ""
             penalty_val = ""
             saves_val = 0
             
             if evt == "Goal":
                 scorer_val = st.selectbox("Scorer", pteam_list)
                 assist_val = st.selectbox("Assist", ["None"] + pteam_list)
                 if assist_val == "None": assist_val = ""
             elif evt == "Penalty":
                 scorer_val = st.selectbox("Player (Penalty)", pteam_list)
                 penalty_val = st.text_input("Penalty Reason")
             elif evt == "Save":
                 scorer_val = st.selectbox("Goalkeeper", pteam_list)
                 saves_val = st.number_input("Count", 1, 10, 1)
             elif evt == "Assist":
                 scorer_val = st.selectbox("Creator", pteam_list)
                 
             if st.form_submit_button("✅ Record Event"):
                 df = load(SCORE_CSV, EVENT_HDR)
                 df.loc[len(df)] = [mid, pd_select, tid, scorer_val, assist_val, evt, penalty_val, saves_val, datetime.now()]
                 save(df, SCORE_CSV)
                 st.success("Log Saved!")
                 reset_hk_flow()
                 safe_rerun()
                 
    # --- Commentary ---
    st.markdown("---")
    st.subheader("🎙 Commentary (Period Feed)")
    if not scores_df.empty:
        # Filter for this match
        match_events = scores_df[scores_df["match_id"]==mid]
        if not match_events.empty:
            comm_df = match_events.sort_index(ascending=False).head(10)
            
            # Helper to get names
            def get_pname(pid):
                row = ply[ply["player_name"]==pid] # stored as name?
                if not row.empty: return row.iloc[0]["player_name"]
                return pid # fallback
                
            for _, row in comm_df.iterrows():
                # Format: P1 | Event | Player (Team)
                per_str = f"**P{row['period']}**"
                evt = row['event_type']
                team_id = row['team_id']
                t_name = t1 if team_id == match["team1_id"] else t2
                
                desc = f"**{row['scorer']}** ({t_name})"
                highlight = ""
                
                if evt == "Goal":
                    desc += " scored a **GOAL!** 🏒"
                    highlight = "🔥"
                    if row['assist']: desc += f" (Assist: {row['assist']})"
                elif evt == "Penalty":
                    desc += f" received a **{row['penalty_type']} Penalty**"
                    highlight = "⚠️"
                elif evt == "Save":
                    desc += f" made a **Save** ({row['saves']}x) 🧤"
                else:
                    desc += f" - {evt}"
                    
                st.markdown(f"{per_str} | {desc} {highlight}")
                st.divider()
        else:
            st.info("No events in this match.")

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

