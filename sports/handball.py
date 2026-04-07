# handball.py
import os
import pandas as pd
import streamlit as st
import time
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
    phone = st.text_input("Player Phone")
    team = st.selectbox("Team", teams["team_name"])
    tid = teams.loc[teams["team_name"]==team,"team_id"].values[0]

    if st.button("Add Player"):
        new_id = df["player_id"].max()+1 if not df.empty else 1
        
        if "phone_number" not in df.columns:
             df["phone_number"] = ""
             
        new_row = pd.DataFrame([[new_id, player, tid, str(phone)]], columns=["player_id","player_name","team_id","phone_number"])
        df = pd.concat([df, new_row], ignore_index=True)
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

    tournaments = load_csv(TOURNAMENTS, T_HDR)
    if tournaments.empty:
        st.warning("No tournaments found.")
        return

    # 1. Select Tournament
    t_names = tournaments["tournament_name"].tolist()
    sel_tourney = st.selectbox("Select Tournament", t_names)
    tid = tournaments.loc[tournaments["tournament_name"]==sel_tourney, "tournament_id"].values[0]

    # 2. Filter Matches
    t_matches = matches[matches["tournament_id"] == tid].copy()
    if t_matches.empty:
        st.info("No matches in this tournament")
        return

    # 3. Match Selection (Local Numbering)
    t_matches = t_matches.sort_values("match_id")
    t_matches["local_id"] = range(1, len(t_matches)+1)

    teams_df = load_csv(TEAMS, TEAM_HDR)
    def get_tn(team_id):
        r = teams_df[teams_df["team_id"]==team_id]
        return r.iloc[0]["team_name"] if not r.empty else "Unknown"

    match_opts = {}
    for _, r in t_matches.iterrows():
        mid_val = r["match_id"]
        lid = r["local_id"]
        t1_val = get_tn(r["team1_id"])
        t2_val = get_tn(r["team2_id"])
        lbl = f"Match #{lid}: {t1_val} vs {t2_val} ({r['match_date']})"
        match_opts[lbl] = mid_val

    sel_lbl = st.selectbox("Select Match", list(match_opts.keys()))
    m = match_opts[sel_lbl]
    match = matches[matches["match_id"]==m].iloc[0]

    teams = load_csv(TEAMS, TEAM_HDR)
    plys = load_csv(PLAYERS, PLAYER_HDR)

    t1 = teams.loc[teams["team_id"]==match["team1_id"],"team_name"].values[0]
    t2 = teams.loc[teams["team_id"]==match["team2_id"],"team_name"].values[0]

    st.write(f"### {t1} vs {t2}")

    # --- Match Timer ---
    if "hb_timer_start" not in st.session_state:
        st.session_state["hb_timer_start"] = None
    if "hb_timer_paused" not in st.session_state:
        st.session_state["hb_timer_paused"] = False
    if "hb_timer_elapsed" not in st.session_state:
        st.session_state["hb_timer_elapsed"] = 0.0

    st.markdown("### ⏱ Match Timer")
    t1_col, t2_col, t3_col = st.columns(3)
    if t1_col.button("▶ Start/Resume"):
        if st.session_state["hb_timer_start"] is None:
            st.session_state["hb_timer_start"] = time.time()
        elif st.session_state["hb_timer_paused"]:
            st.session_state["hb_timer_start"] = time.time() - st.session_state["hb_timer_elapsed"]
            st.session_state["hb_timer_paused"] = False

    if t2_col.button("⏸ Pause"):
        if st.session_state["hb_timer_start"] is not None and not st.session_state["hb_timer_paused"]:
            st.session_state["hb_timer_elapsed"] = time.time() - st.session_state["hb_timer_start"]
            st.session_state["hb_timer_paused"] = True

    if t3_col.button("🔄 Reset"):
        st.session_state["hb_timer_start"] = None
        st.session_state["hb_timer_paused"] = False
        st.session_state["hb_timer_elapsed"] = 0.0

    # Display Time (Countdown)
    HALF_DURATION = 30 * 60 # 30 mins
    
    hb_current_elapsed = 0.0
    if st.session_state["hb_timer_start"] is not None:
        if st.session_state["hb_timer_paused"]:
            hb_current_elapsed = st.session_state["hb_timer_elapsed"]
        else:
            hb_current_elapsed = time.time() - st.session_state["hb_timer_start"]
    
    hb_remaining = max(0, HALF_DURATION - hb_current_elapsed)
    
    hb_mins = int(hb_remaining // 60)
    hb_secs = int(hb_remaining % 60)
    st.markdown(f"## **{hb_mins:02d}:{hb_secs:02d}** (Countdown)")

    if st.session_state["hb_timer_start"] is not None and not st.session_state["hb_timer_paused"] and hb_remaining > 0:
        time.sleep(1)
        st.rerun()

    st.markdown(f"## **{hb_mins:02d}:{hb_secs:02d}**")

    # --- Live Scoreboard ---
    score_df = load_csv(SCORES, SCORE_HDR)
    sh_match = score_df[score_df["match_id"] == m]
    sh_goals = sh_match[sh_match["event"] == "Goal"]
    
    # Calculate scores
    t1_goals = sh_goals[sh_goals["team_id"] == match["team1_id"]]["points"].sum()
    t2_goals = sh_goals[sh_goals["team_id"] == match["team2_id"]]["points"].sum()
    
    st.markdown(
        f"<h1 style='text-align:center; color: #FF9800;'>{t1} {t1_goals} - {t2_goals} {t2}</h1>", 
        unsafe_allow_html=True
    )

    # --- Button-Based Scoring Flow ---
    st.divider()
    if "hb_step" not in st.session_state:
        st.session_state["hb_step"] = "SELECT_EVENT" 
    if "hb_event_type" not in st.session_state:
        st.session_state["hb_event_type"] = None

    def reset_hb_flow():
        st.session_state["hb_step"] = "SELECT_EVENT"
        st.session_state["hb_event_type"] = None

    def safe_rerun():
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()
            
    if st.button("❌ Reset Form"):
        reset_hb_flow()
        safe_rerun()

    # STEP 1: Select Event
    if st.session_state["hb_step"] == "SELECT_EVENT":
        st.markdown("#### Select Event")
        c1, c2, c3 = st.columns(3)
        if c1.button("🔥 Goal", use_container_width=True):
             st.session_state["hb_event_type"] = "Goal"
             st.session_state["hb_step"] = "DETAILS"
             safe_rerun()
        if c2.button("🟨 Yellow Card", use_container_width=True):
             st.session_state["hb_event_type"] = "Yellow Card"
             st.session_state["hb_step"] = "DETAILS"
             safe_rerun()
        if c3.button("🟥 Red Card", use_container_width=True):
             st.session_state["hb_event_type"] = "Red Card"
             st.session_state["hb_step"] = "DETAILS"
             safe_rerun()
             
        c4, c5 = st.columns(2)
        if c4.button("⏱️ 2min Suspension", use_container_width=True):
             st.session_state["hb_event_type"] = "2min"
             st.session_state["hb_step"] = "DETAILS"
             safe_rerun()
        if c5.button("🚫 Timeout", use_container_width=True):
             st.session_state["hb_event_type"] = "Timeout"
             st.session_state["hb_step"] = "DETAILS"
             safe_rerun()

    # STEP 2: Details
    if st.session_state["hb_step"] == "DETAILS":
        evt = st.session_state["hb_event_type"]
        st.info(f"Recording: **{evt}**")
        
        with st.form("hb_event_form"):
            sc_team = st.selectbox("Team Involvement", [t1, t2])
            
            # Helper to get players based on team name
            def get_players(team_name, tm1_name, tm1_id, tm2_id):
                 tid = tm1_id if team_name == tm1_name else tm2_id
                 return plys[plys["team_id"]==tid]["player_name"].tolist(), tid
            
            plist, tid = get_players(sc_team, t1, match["team1_id"], match["team2_id"])
            
            player = st.selectbox("Player", plist if plist else ["Unknown"])
            pid = 0
            if player and player != "Unknown":
                 pid = plys.loc[(plys["team_id"]==tid) & (plys["player_name"]==player),"player_id"].values[0]

            pts = 1 if evt == "Goal" else 0
            if evt == "Goal":
                pts = st.number_input("Points", 0, 5, 1)

            if st.form_submit_button("✅ Save Event"):
                df = load_csv(SCORES, SCORE_HDR)
                df.loc[len(df)] = [m, tid, pid, pts, evt, datetime.now()]
                save_csv(df, SCORES)
                st.success("Updated!")
                reset_hb_flow()
                safe_rerun()
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
        
    # --- Commentary ---
    st.markdown("---")
    st.subheader("🎙 Commentary (Match Feed)")
    
    # Reload scores
    live_scores = load_csv(SCORES, SCORE_HDR)
    if not live_scores.empty:
        m_events = live_scores[live_scores["match_id"]==m]
        
        if not m_events.empty:
            # Sort latest
            comm_df = m_events.sort_index(ascending=False).head(10)
            
            for _, row in comm_df.iterrows():
                # Format: Minute | Event | Desc
                # event time not explicitly minute in some old logic? New logic has minute?
                # The data structure has 'timestamp'. We can infer or if minute stored.
                # Inspect SCORE_HDR.. wait, handball SCORE_HDR?
                # "match_id","event","player_id","team_id","points","details"
                # It doesn't seem to have 'minute' explicitly in older parts?
                # Let's check CSV header in code.
                # SCORE_HDR = ["match_id","event","player_id","team_id","points","details"]
                # It does NOT have minute or timestamp?
                # Wait, if I added it... 
                # Let's just show Event | Desc.
                
                evt = row['event']
                
                # Get names
                pid = row['player_id']
                p_name = "Unknown"
                if pid:
                    pr = plys[plys["player_id"]==pid]
                    if not pr.empty: p_name = pr.iloc[0]["player_name"]
                
                tid = row['team_id']
                t_name = t1 if tid == match["team1_id"] else t2
                
                desc = f"**{p_name}** ({t_name})"
                highlight = ""
                
                if evt == "Goal":
                    desc += " scored! 🤾‍♂️"
                    highlight = "🔥"
                elif "Card" in evt:
                    desc += f" received a **{evt}**"
                    highlight = "⚠️"
                elif "Suspension" in evt:
                    desc += " **Suspended (2min)**"
                elif "Timeout" in evt:
                    desc = f"**{t_name}** called Timeout"
                
                st.markdown(f"{evt} | {desc} {highlight}")
                st.divider()
        else:
            st.info("No events.")

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

