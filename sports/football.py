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

    st.divider()
    st.subheader("🏆 Tournament Stats")
    if st.button("📊 Show Golden Boot & Stats"):
        sc = load_csv(SCORES_CSV, ["match_id","minute","event_type","team_name","player_name","xg","timestamp"])
        if sc.empty:
            st.warning("No scores available.")
        else:
            mid_list = matches["match_id"].tolist()
            t_sc = sc[sc["match_id"].isin(mid_list)].copy()
            
            if t_sc.empty:
                st.warning("No stats for this tournament yet.")
            else:
                 # Count Goals per Player
                 goals = t_sc[t_sc["event_type"]=="Goal"]
                 if goals.empty:
                     st.info("No goals recorded yet.")
                 else:
                     leaderboard = goals["player_name"].value_counts().reset_index()
                     leaderboard.columns = ["Player", "Goals"]
                     
                     # Merge for Image (by player_name)
                     # Load Players to get images
                     players_df = load_csv(PLAYERS_CSV, ["player_id","player_name","team_id","phone_number","profile_image"])
                     
                     if not players_df.empty and "profile_image" in players_df.columns:
                         p_imgs = players_df[["player_name", "profile_image"]].drop_duplicates("player_name")
                         leaderboard = pd.merge(leaderboard, p_imgs, left_on="Player", right_on="player_name", how="left")
                     
                     top = leaderboard.iloc[0]
                     
                     def get_img(row):
                        default_img = "https://cdn-icons-png.flaticon.com/512/334/334656.png"
                        if "profile_image" in row and pd.notna(row["profile_image"]) and row["profile_image"]:
                            if os.path.exists(row["profile_image"]):
                                return row["profile_image"]
                        return default_img
                     
                     top_img = get_img(top)
                     
                     c1, c2 = st.columns([1,2])
                     with c1:
                         st.markdown("### 👟 Golden Boot")
                         st.image(top_img, width=150)
                     with c2:
                         st.markdown(f"## **{top['Player']}**")
                         st.markdown(f"**Goals: {top['Goals']}**")
                         
                     st.dataframe(leaderboard[["Player", "Goals"]].head(10))

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
    phone = st.text_input("Player Phone Number")
    uploaded = st.file_uploader("Upload Player Photo", type=['jpg', 'jpeg', 'png'])

    if st.button("Add Player") and pname:
        df = load_csv(PLAYERS_CSV, ["player_id","player_name","team_id","phone_number","profile_image"])
        new_id = df["player_id"].max()+1 if not df.empty else 1
        
        if "phone_number" not in df.columns: df["phone_number"] = ""
        if "profile_image" not in df.columns: df["profile_image"] = ""
        
        image_path = ""
        if uploaded:
            img_dir = os.path.join(DATA_PATH, "player_images")
            os.makedirs(img_dir, exist_ok=True)
            ts = int(datetime.now().timestamp())
            fname = f"{new_id}_{''.join(x for x in pname if x.isalnum())}_{ts}.{uploaded.name.split('.')[-1]}"
            fpath = os.path.join(img_dir, fname)
            with open(fpath, "wb") as f:
                f.write(uploaded.getbuffer())
            image_path = fpath

        new_row = pd.DataFrame([[new_id,pname,tid,str(phone),image_path]], columns=["player_id","player_name","team_id","phone_number","profile_image"])
        df = pd.concat([df, new_row], ignore_index=True)
        save_csv(df,PLAYERS_CSV)
        st.success("Player Added")
        if image_path: st.image(image_path, width=150)
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

    tournaments = load_csv(TOURNAMENTS_CSV)
    if tournaments.empty:
        st.warning("No tournaments found.")
        return

    # 1. Select Tournament
    t_names = tournaments["tournament_name"].tolist()
    sel_tourney = st.selectbox("Select Tournament", t_names)
    tid = tournaments[tournaments["tournament_name"] == sel_tourney]["tournament_id"].values[0]

    # 2. Filter Matches
    t_matches = matches[matches["tournament_id"] == tid].copy()
    
    if t_matches.empty:
        st.info("No matches in this tournament.")
        return

    # 3. Match Selection with Local Numbering
    # Sort by numeric ID to ensure stable order
    t_matches = t_matches.sort_values("match_id")
    t_matches["local_id"] = range(1, len(t_matches) + 1)
    
    # helper for names
    def get_tname(team_id):
        row = teams[teams["team_id"]==team_id]
        return row.iloc[0]["team_name"] if not row.empty else "Unknown"

    match_options = {}
    for _, r in t_matches.iterrows():
        mid = r["match_id"]
        lid = r["local_id"]
        t1 = get_tname(r["team1_id"])
        t2 = get_tname(r["team2_id"])
        date = r["match_date"]
        label = f"Match #{lid}: {t1} vs {t2} ({date})"
        match_options[label] = mid

    sel_label = st.selectbox("Select Match", list(match_options.keys()))
    match_id = match_options[sel_label]

    st.markdown(f"## **{fb_mins:02d}:{fb_secs:02d}**")

    # --- Live Scoreboard ---
    goals = df[(df["match_id"]==match_id)&(df["event_type"]=="Goal")].groupby("team_name").size().to_dict()
    s1 = goals.get(team1, 0)
    s2 = goals.get(team2, 0)
    
    st.markdown(
        f"<h1 style='text-align:center; color: #2196F3;'>{team1} {s1} - {s2} {team2}</h1>", 
        unsafe_allow_html=True
    )

    # --- Button-Based Scoring Flow ---
    if "fb_timer_start" not in st.session_state:
        st.session_state["fb_timer_start"] = None
    if "fb_timer_paused" not in st.session_state:
        st.session_state["fb_timer_paused"] = False
    if "fb_timer_elapsed" not in st.session_state:
        st.session_state["fb_timer_elapsed"] = 0.0

    st.markdown("### ⏱ Match Timer")
    t1_col, t2_col, t3_col = st.columns(3)
    if t1_col.button("▶ Start/Resume"):
        if st.session_state["fb_timer_start"] is None:
            st.session_state["fb_timer_start"] = time.time()
        elif st.session_state["fb_timer_paused"]:
            st.session_state["fb_timer_start"] = time.time() - st.session_state["fb_timer_elapsed"]
            st.session_state["fb_timer_paused"] = False

    if t2_col.button("⏸ Pause"):
        if st.session_state["fb_timer_start"] is not None and not st.session_state["fb_timer_paused"]:
            st.session_state["fb_timer_elapsed"] = time.time() - st.session_state["fb_timer_start"]
            st.session_state["fb_timer_paused"] = True

    if t3_col.button("🔄 Reset"):
        st.session_state["fb_timer_start"] = None
        st.session_state["fb_timer_paused"] = False
        st.session_state["fb_timer_elapsed"] = 0.0

    # Display Time (Countdown)
    HALF_DURATION = 45 * 60 # 45 minutes
    
    fb_current_elapsed = 0.0
    if st.session_state["fb_timer_start"] is not None:
        if st.session_state["fb_timer_paused"]:
            fb_current_elapsed = st.session_state["fb_timer_elapsed"]
        else:
            fb_current_elapsed = time.time() - st.session_state["fb_timer_start"]
    
    remaining = max(0, HALF_DURATION - fb_current_elapsed)
    
    fb_mins = int(remaining // 60)
    fb_secs = int(remaining % 60)
    st.markdown(f"## **{fb_mins:02d}:{fb_secs:02d}** (Countdown)")
    
    if st.session_state["fb_timer_start"] is not None and not st.session_state["fb_timer_paused"] and remaining > 0:
        time.sleep(1)
        st.rerun()

    # --- Button-Based Scoring Flow ---
    st.divider()
    if "fb_step" not in st.session_state:
        st.session_state["fb_step"] = "SELECT_EVENT" 
    if "fb_event_type" not in st.session_state:
        st.session_state["fb_event_type"] = None

    def reset_fb_flow():
        st.session_state["fb_step"] = "SELECT_EVENT"
        st.session_state["fb_event_type"] = None

    def safe_rerun():
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()
            
    if st.button("❌ Reset Form"):
        reset_fb_flow()
        safe_rerun()

    # STEP 1: Select Event
    if st.session_state["fb_step"] == "SELECT_EVENT":
        st.markdown("#### Select Event")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("⚽ Goal", use_container_width=True):
             st.session_state["fb_event_type"] = "Goal"
             st.session_state["fb_step"] = "DETAILS"
             safe_rerun()
        if c2.button("👟 Assist", use_container_width=True):
             st.session_state["fb_event_type"] = "Assist"
             st.session_state["fb_step"] = "DETAILS"
             safe_rerun()
        if c3.button("🧤 Save", use_container_width=True):
             st.session_state["fb_event_type"] = "Save"
             st.session_state["fb_step"] = "DETAILS"
             safe_rerun()
        if c4.button("🎯 Shot on Target", use_container_width=True):
             st.session_state["fb_event_type"] = "Shot on Target"
             st.session_state["fb_step"] = "DETAILS"
             safe_rerun()

        c5, c6, c7 = st.columns(3)
        if c5.button("🟨 Yellow Card", use_container_width=True):
             st.session_state["fb_event_type"] = "Yellow Card"
             st.session_state["fb_step"] = "DETAILS"
             safe_rerun()
        if c6.button("🟥 Red Card", use_container_width=True):
             st.session_state["fb_event_type"] = "Red Card"
             st.session_state["fb_step"] = "DETAILS"
             safe_rerun()
        if c7.button("🔄 Sub/Other", use_container_width=True):
             st.session_state["fb_event_type"] = "Other"
             st.session_state["fb_step"] = "DETAILS"
             safe_rerun()

    # STEP 2: Details
    if st.session_state["fb_step"] == "DETAILS":
        evt = st.session_state["fb_event_type"]
        st.info(f"Recording: **{evt}**")
        
        with st.form("fb_event_form"):
            sc_team = st.selectbox("Team", [team1, team2])
            
            # Filter players by selected team
            plist = players[players["team_id"]==match["team1_id"]]["player_name"].tolist() if sc_team==team1 else players[players["team_id"]==match["team2_id"]]["player_name"].tolist()
            
            player = st.selectbox("Player", plist if plist else ["Unknown"])
            
            xg_val = 0.0
            if evt in ["Goal", "Shot on Target"]:
                xg_val = st.slider("Expected Goal (xG)", 0.01, 1.0, 0.30, 0.01)
            
            # Auto-fill minute from new timer (Duration - Remaining)
            elapsed_min = int((HALF_DURATION - remaining) // 60)
            # Add 45 if 2nd half? For now just raw minute
            minute = st.number_input("Minute", min_value=0, max_value=120, value=elapsed_min)
            
            if st.form_submit_button("✅ Confirm Event"):
                df.loc[len(df)] = [match_id, minute, evt, sc_team, player, xg_val, datetime.now()]
                save_csv(df, SCORES_CSV)
                st.success("Event Recorded!")
                reset_fb_flow()
                safe_rerun()

    goals = df[(df["match_id"]==match_id)&(df["event_type"]=="Goal")].groupby("team_name").size().to_dict()
    st.info(f"Score: {team1} {goals.get(team1,0)} - {goals.get(team2,0)} {team2}")
    
    # --- Commentary ---
    st.markdown("---")
    st.subheader("🎙 Commentary (Match Feed)")
    
    match_events = df[df["match_id"]==match_id]
    if not match_events.empty:
        # Sort latest first
        comm_df = match_events.sort_index(ascending=False).head(12)
        
        for _, row in comm_df.iterrows():
            min_str = f"**{row['minute']}'**"
            evt = row['event_type']
            team = row['team_name']
            player = row['player_name']
            xg = row['xg']
            
            desc = f"**{player}** ({team})"
            highlight = ""
            
            if evt == "Goal":
                desc += " scored a **GOAL!** ⚽"
                highlight = "🔥"
                if xg > 0: desc += f" (xG: {xg})"
            elif evt == "Yellow Card":
                desc += " received a **Yellow Card** 🟨"
            elif evt == "Red Card":
                desc += " sent off! **Red Card** 🟥"
            elif evt == "Assist":
                 desc += " provided an **Assist** 👟"
            elif evt == "Save":
                 desc += " made a **Save** 🧤"
            else:
                 desc += f" - {evt}"
                 
            st.markdown(f"{min_str} | {desc} {highlight}")
            st.divider()
    else:
        st.info("No events yet.")

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

