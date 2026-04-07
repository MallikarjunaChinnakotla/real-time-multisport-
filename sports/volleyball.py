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
    tournaments = load_csv(TOURNAMENTS_FILE)
    if tournaments.empty:
        st.warning("Add Tournament first")
        return

    tour_choice = st.selectbox("Select Tournament", tournaments["name"].unique())
    team_name = st.text_input("Team Name")
    
    if st.button("Add Team"):
        if not team_name.strip(): 
            st.error("Enter a team name.")
            return
            
        df = load_csv(TEAMS_FILE)
        
        # Check if 'tournament' column exists
        if "tournament" not in df.columns:
            df["tournament"] = ""
            
        new_row = {"team_name": team_name, "tournament": tour_choice, "players": ""} 
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_csv(df, TEAMS_FILE)
        st.success(f"Team '{team_name}' added to '{tour_choice}'!")

# 2.1 Add Player
def add_player():
    st.subheader("➕ Add Volleyball Player")
    
    PLAYERS_FILE = os.path.join(DATA_DIR, "volleyball_players.csv")
    TEAMS_FILE = os.path.join(DATA_DIR, "volleyball_teams.csv")
    TOURNAMENTS_FILE = os.path.join(DATA_DIR, "volleyball_tournaments.csv")
    
    tournaments = load_csv(TOURNAMENTS_FILE)
    teams = load_csv(TEAMS_FILE)
    
    if tournaments.empty:
        st.warning("Add tournaments first")
        return
    if teams.empty:
        st.warning("Add teams first")
        return

    # Filter Teams by Tournament
    tour_choice = st.selectbox("Select Tournament", tournaments["name"].unique())
    
    # Handle legacy teams (empty tournament field)
    if "tournament" in teams.columns:
        filtered_teams = teams[teams["tournament"] == tour_choice]
    else:
        filtered_teams = teams # If schema not updated yet, show all
        
    if filtered_teams.empty:
        st.info(f"No teams in {tour_choice}. Add a team first.")
        return

    team_choice = st.selectbox("Select Team", filtered_teams["team_name"].unique())
    player_name = st.text_input("Player Name")
    phone_number = st.text_input("Player Phone Number")
    uploaded_file = st.file_uploader("Upload Player Photo", type=['jpg', 'jpeg', 'png'])
    
    if st.button("Add Player"):
        players_df = load_csv(PLAYERS_FILE)
        
        if "phone_number" not in players_df.columns:
            players_df["phone_number"] = ""
        if "profile_image" not in players_df.columns:
            players_df["profile_image"] = ""
            
        image_path = ""
        if uploaded_file is not None:
            img_dir = os.path.join(DATA_DIR, "player_images")
            os.makedirs(img_dir, exist_ok=True)
            
            timestamp = int(datetime.now().timestamp())
            safe_name = "".join(x for x in player_name if x.isalnum())
            ext = uploaded_file.name.split('.')[-1]
            filename = f"{safe_name}_{timestamp}.{ext}"
            save_path = os.path.join(img_dir, filename)
            
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            image_path = save_path
            
        new_row = {"player_name": player_name, "team_name": team_choice, "phone_number": str(phone_number), "profile_image": image_path}
        players_df = pd.concat([players_df, pd.DataFrame([new_row])], ignore_index=True)
        save_csv(players_df, PLAYERS_FILE)
        st.success(f"Player '{player_name}' added to {team_choice}!")
        if image_path:
            st.image(image_path, width=150, caption="Uploaded Photo")

# 3. View Tournaments
def view_tournaments():
    st.subheader("View Tournaments")
    df = load_csv(TOURNAMENTS_FILE)
    st.dataframe(df)

    st.divider()
    st.subheader("🏆 Tournament Stats (Team Standings)")
    if st.button("📊 Show Standings"):
        matches = load_csv(MATCHES_FILE)
        scores = load_csv(SCORES_FILE)
        if matches.empty or scores.empty:
            st.warning("No data.")
        else:
            # Group scores by match and find winners
            # Schema: match (string), set_no, winner, score1, score2
            # Since volleyball.py doesn't track player IDs in scoring, we show *Team Standings*
            
            # Count wins per team
            # Needs 'winner' column in scores?
            # scores keys: match, set_no, team_won, score1, score2
            # Wait, check SCORES_FILE usage in update_score to confirm schema
            pass 
            # Actually, `update_score` writes: {"match": match_choice, "set_no": set_no, "winner": winner, "score1": s1, "score2": s2}
            # So we can calculate Set Wins or Match Wins if we deduce it.
            
            if "winner" in scores.columns:
                wins = scores["winner"].value_counts().reset_index()
                wins.columns = ["Team", "Sets/Matches Won"]
                st.dataframe(wins)
            else:
                st.info("Winner data not found.")

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

    if matches.empty:
        st.warning("No matches scheduled.")
        return

    tournaments = load_csv(TOURNAMENTS_FILE)
    if tournaments.empty:
        st.warning("No tournaments found.")
        return

    # 1. Select Tournament
    t_names = tournaments["name"].tolist()
    sel_tourney = st.selectbox("Select Tournament", t_names)

    # 2. Filter Matches
    t_matches = matches[matches["tournament"] == sel_tourney].copy()
    if t_matches.empty:
        st.info("No matches in this tournament")
        return

    # 3. Match Selection (Local Numbering)
    # No explicit match_id in this file's schema? 
    # Let's see... schedule_match doesn't adding ID. It just appends.
    # So we must use index.
    # We should probably reset index to create a temporary local ID.
    t_matches["local_id"] = range(1, len(t_matches)+1)
    
    match_opts = {}
    for idx, r in t_matches.iterrows():
        # r is a row. idx is original index if we didn't reset, 
        # but we need original index or some unique identifier to find it again?
        # Actually `matches` has no ID column. 
        # We rely on "Team1 vs Team2 (Date)" string being unique enough or just use lookup.
        # But if we filter, we need to know which row in the MAIN matches df it corresponds to.
        # Since there's no ID, this is tricky.
        # BUT `matches` is just a dataframe. 
        # The original code did: selected_row = matches.iloc[match_strs.tolist().index(match_choice)]
        # which implies it relies on string uniqueness or just index.
        # Let's add a temporary global index to track it.
        pass

    # Better approach:
    # 1. Add temporary 'global_index' to filtered matches to retrieve it later.
    matches["global_index"] = matches.index
    t_matches = matches[matches["tournament"] == sel_tourney].copy()
    t_matches["local_id"] = range(1, len(t_matches)+1)
    
    match_map = {}
    for _, r in t_matches.iterrows():
        lid = r["local_id"]
        gid = r["global_index"]
        lbl = f"Match #{lid}: {r['team1']} vs {r['team2']} ({r['date']})"
        match_map[lbl] = gid
        
    match_choice = st.selectbox("Select Match", list(match_map.keys()))
    global_idx = match_map[match_choice]
    
    selected_row = matches.loc[global_idx]
    
    # We need to construct the unique string used for SAVING scores if scores rely on "match string"
    # In original code: `match_choice` string passed to `df_cur[df_cur["match"]==match_choice]`
    # The original code constructed: f"{row['team1']} vs {row['team2']} ({row['date']})"
    # We must preserve this format for the SCORE lookup to work, OR we update score lookup.
    # The score saving uses `match_choice` variable.
    # So we must define `match_choice` to be the OLD format string for compatibility, 
    # EVEN IF we display a styled string.
    
    # Re-construct the compatibility string
    match_compatibility_str = f"{selected_row['team1']} vs {selected_row['team2']} ({selected_row['date']})"
    
    # This variable 'match_choice' is used later for loading scores.
    # Overwrite `match_choice` with the compatibility string.
    # But wait, `match_choice` variable name is used in the UI for selectbox in original code.
    # Here we used `match_choice` for the UI selection key (the nice label).
    # Let's rename.
    
    ui_label = match_choice # The nice label e.g. "Match #1..."
    match_choice = match_compatibility_str # The database key e.g. "Team1 vs Team2..."

    team1, team2 = selected_row["team1"], selected_row["team2"]

    st.divider()

    # --- Live Scoreboard ---
    df_cur = load_csv(SCORES_FILE)
    cur_score1 = 0
    cur_score2 = 0
    if not df_cur.empty:
        m_df = df_cur[df_cur["match"]==match_choice]
        if not m_df.empty:
            cur_score1 = int(m_df.iloc[-1]["score1"])
            cur_score2 = int(m_df.iloc[-1]["score2"])

    st.markdown(
        f"<h1 style='text-align:center; color: #9C27B0;'>{team1} {cur_score1} - {cur_score2} {team2}</h1>", 
        unsafe_allow_html=True
    )

    # --- Button-Based Scoring Flow ---
    if "vb_step" not in st.session_state:
        st.session_state["vb_step"] = "SELECT_EVENT"
    if "vb_event_type" not in st.session_state:
        st.session_state["vb_event_type"] = None

    def reset_vb_flow():
        st.session_state["vb_step"] = "SELECT_EVENT"
        st.session_state["vb_event_type"] = None
    
    def safe_rerun():
        try:
            st.rerun()
        except AttributeError:
            st.experimental_rerun()

    if st.button("❌ Reset Form"):
        reset_vb_flow()
        safe_rerun()

    # STEP 1: Select Event
    if st.session_state["vb_step"] == "SELECT_EVENT":
        st.markdown("#### Select Score Update")
        c1, c2 = st.columns(2)
        if c1.button(f"🏐 Point for {team1}", use_container_width=True):
             st.session_state["vb_event_type"] = "Point_T1"
             st.session_state["vb_step"] = "DETAILS"
             safe_rerun()
        if c2.button(f"🏐 Point for {team2}", use_container_width=True):
             st.session_state["vb_event_type"] = "Point_T2"
             st.session_state["vb_step"] = "DETAILS"
             safe_rerun()
             
        c3, c4 = st.columns(2)
        if c3.button("🚫 Timeout", use_container_width=True):
             st.session_state["vb_event_type"] = "Timeout"
             st.session_state["vb_step"] = "DETAILS"
             safe_rerun()
        if c4.button("🔄 Substitution", use_container_width=True):
             st.session_state["vb_event_type"] = "Sub"
             st.session_state["vb_step"] = "DETAILS"
             safe_rerun()

    # STEP 2: DETAILS
    if st.session_state["vb_step"] == "DETAILS":
        evt = st.session_state["vb_event_type"]
        st.info(f"Recording: **{evt}**")
        
        with st.form("vb_event_form"):
            # Auto-increment scores based on selection if needed, or ask confirmation
            # For simplicity, we stick to Manual Input + Confirmation for now, 
            # OR we can calculate current score from CSV + 1.
            # But currently `score1`, `score2` are inputs. 
            # Ideally we read from CSV last row.
            
            # Let's read last score from CSV to helpful default
            df_cur = load_csv(SCORES_FILE)
            cur_score1 = 0
            cur_score2 = 0
            if not df_cur.empty:
                m_df = df_cur[df_cur["match"]==match_choice]
                if not m_df.empty:
                    cur_score1 = int(m_df.iloc[-1]["score1"])
                    cur_score2 = int(m_df.iloc[-1]["score2"])

            if evt == "Point_T1":
                cur_score1 += 1
            elif evt == "Point_T2":
                cur_score2 += 1
                
            new_s1 = st.number_input(f"{team1} Score", value=cur_score1)
            new_s2 = st.number_input(f"{team2} Score", value=cur_score2)
            
            srv = st.selectbox("Serve Team", [team1, team2])
            to_team = st.selectbox("Timeout Called By", ["None", team1, team2])
            
            if st.form_submit_button("✅ Update Score"):
                new_row = {
                    "match": match_choice,
                    "team1": team1,
                    "team2": team2,
                    "score1": new_s1,
                    "score2": new_s2,
                    "serve_team": srv,
                    "timeout_team": "" if to_team == "None" else to_team,
                    "timestamp": datetime.now()
                }
                save_csv(pd.concat([load_csv(SCORES_FILE), pd.DataFrame([new_row])], ignore_index=True), SCORES_FILE)
                st.success("Score Updated!")
                reset_vb_flow()
                safe_rerun()

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
        "Add Tournament", "Add Team", "Add Player", "View Tournaments",
        "Schedule Match", "Update Live Score", "View Match Summary"
    ])
    if choice == "Add Tournament":
        add_tournament()
    elif choice == "Add Team":
        add_team()
    elif choice == "Add Player":
        add_player()
    elif choice == "View Tournaments":
        view_tournaments()
    elif choice == "Schedule Match":
        schedule_match()
    elif choice == "Update Live Score":
        update_score()
    elif choice == "View Match Summary":
        view_summary()

