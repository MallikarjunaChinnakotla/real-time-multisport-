# kabaddi.py
import os
import time
from datetime import datetime
import pandas as pd
import streamlit as st

# -------- CONFIG ----------
DATA_DIR = "sports_dashboard/data"
os.makedirs(DATA_DIR, exist_ok=True)

TOURNAMENTS_CSV = os.path.join(DATA_DIR, "kabaddi_tournaments.csv")
TEAMS_CSV = os.path.join(DATA_DIR, "kabaddi_teams.csv")
PLAYERS_CSV = os.path.join(DATA_DIR, "kabaddi_players.csv")
MATCHES_CSV = os.path.join(DATA_DIR, "kabaddi_matches.csv")
SCORES_CSV = os.path.join(DATA_DIR, "kabaddi_scores.csv")
MATCH_STATE_CSV = os.path.join(DATA_DIR, "kabaddi_match_state.csv")

# Kabaddi rules
HALF_SECONDS = 20 * 60        # 20 minutes per half
TOTAL_SECONDS = HALF_SECONDS * 2
MAX_TIMEOUTS_PER_TEAM = 2
# ---- CSV Headers for Kabaddi ----
TOURNAMENTS_HDR = ["tournament_id", "tournament_name", "start_date", "end_date", "location"]
TEAMS_HDR = ["team_id", "team_name", "tournament_id"]
PLAYERS_HDR = ["player_id", "player_name", "team_id"]
MATCHES_HDR = ["match_id", "tournament_id", "team1_id", "team2_id", "match_date", "venue"]
SCORES_HDR = ["match_id", "minute", "event_type", "player_id", "team_id", "points", "details", "timestamp"]
MATCH_STATE_HDR = [
    "match_id", "half", "start_time_iso",
    "accumulated_seconds", "is_running",
    "team1_timeouts", "team2_timeouts",
    "team1_active_count", "team2_active_count"
]


# --------- Utility CSV helpers ----------
def ensure_csv(path, cols):
    """Create CSV with headers if missing or empty."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        pd.DataFrame(columns=cols).to_csv(path, index=False)

def load_csv(path, cols=None):
    """Load CSV; if file missing or empty create it with headers and return empty DF."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        if cols is None:
            return pd.DataFrame()
        else:
            pd.DataFrame(columns=cols).to_csv(path, index=False)
            return pd.DataFrame(columns=cols)
    return pd.read_csv(path)

def save_csv(df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)

# Ensure all files exist with the correct headers
ensure_csv(TOURNAMENTS_CSV, TOURNAMENTS_HDR)
ensure_csv(TEAMS_CSV, TEAMS_HDR)
ensure_csv(PLAYERS_CSV, PLAYERS_HDR)
ensure_csv(MATCHES_CSV, MATCHES_HDR)
ensure_csv(SCORES_CSV, SCORES_HDR)
ensure_csv(MATCH_STATE_CSV, MATCH_STATE_HDR)

# --------- Match state persistence ----------
def load_state_row(match_id):
    state_df = load_csv(MATCH_STATE_CSV, MATCH_STATE_HDR)
    row = state_df[state_df["match_id"] == match_id]
    if row.empty:
        # initialize a new state record
        new = pd.DataFrame([{
            "match_id": match_id,
            "half": 1,
            "start_time_iso": "",
            "accumulated_seconds": 0.0,
            "is_running": False,
            "team1_timeouts": 0,
            "team2_timeouts": 0,
            "team1_active_count": 7,
            "team2_active_count": 7
        }])
        state_df = pd.concat([state_df, new], ignore_index=True)
        save_csv(state_df, MATCH_STATE_CSV)
        return new.iloc[0].to_dict()
    else:
        # return as dict
        return row.iloc[0].to_dict()

def save_state_row(state_obj):
    state_df = load_csv(MATCH_STATE_CSV, MATCH_STATE_HDR)
    mid = int(state_obj["match_id"])
    if mid in state_df["match_id"].values:
        idx = state_df[state_df["match_id"] == mid].index[0]
        for k, v in state_obj.items():
            state_df.at[idx, k] = v
    else:
        state_df = pd.concat([state_df, pd.DataFrame([state_obj])], ignore_index=True)
    save_csv(state_df, MATCH_STATE_CSV)

# --------- Helpers ----------
def get_team(row_df, team_id):
    teams = load_csv(TEAMS_CSV, TEAMS_HDR)
    match = teams[teams["team_id"] == int(team_id)]
    if match.empty:
        return {"team_id": team_id, "team_name": f"Team {team_id}"}
    return match.iloc[0].to_dict()

def get_player_name(player_id):
    if player_id == "" or pd.isnull(player_id):
        return ""
    players = load_csv(PLAYERS_CSV, PLAYERS_HDR)
    row = players[players["player_id"] == int(player_id)]
    return row.iloc[0]["player_name"] if not row.empty else str(player_id)

def compute_scores_for_match(match_id):
    scores = load_csv(SCORES_CSV, SCORES_HDR)
    if scores.empty:
        return {}
    m = scores[scores["match_id"] == int(match_id)]
    if m.empty:
        return {}
    totals = m.groupby("team_id")["points"].sum().to_dict()
    # convert keys to int
    new = {}
    for k, v in totals.items():
        try:
            new[int(k)] = int(v)
        except:
            new[k] = int(v)
    return new

def is_match_over(match_id: int) -> bool:
    """
    Check if a Kabaddi match is over (full 40 mins completed).
    Uses the same timing logic as the live screen.
    """
    state, total_elapsed, elapsed_in_half, remaining_in_half, match_over = load_state_and_compute(match_id)
    return match_over

# --------- Admin UI ----------
def add_tournament():
    st.subheader("🏆 Add Tournament")
    df = load_csv(TOURNAMENTS_CSV, TOURNAMENTS_HDR)
    name = st.text_input("Tournament Name")
    start = st.date_input("Start Date")
    end = st.date_input("End Date")
    location = st.text_input("Location")
    if st.button("Add Tournament"):
        if not name.strip():
            st.warning("Please enter a name")
            return
        new_id = int(df["tournament_id"].max()) + 1 if not df.empty else 1
        df = pd.concat([df, pd.DataFrame([[new_id, name, str(start), str(end), location]], columns=TOURNAMENTS_HDR)], ignore_index=True)
        save_csv(df, TOURNAMENTS_CSV)
        st.success(f"Tournament '{name}' added (ID {new_id})")
        
def safe_rerun():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()


def add_team():
    st.subheader("➕ Add Team")
    teams = load_csv(TEAMS_CSV, TEAMS_HDR)
    tours = load_csv(TOURNAMENTS_CSV, TOURNAMENTS_HDR)
    if tours.empty:
        st.warning("Add a tournament first.")
        return
    tour_choice = st.selectbox("Tournament", tours["tournament_name"].tolist())
    team_name = st.text_input("Team Name")
    if st.button("Add Team"):
        if not team_name.strip():
            st.warning("Enter team name")
            return
        tournament_id = int(tours[tours["tournament_name"] == tour_choice]["tournament_id"].iloc[0])
        new_id = int(teams["team_id"].max()) + 1 if not teams.empty else 1
        teams = pd.concat([teams, pd.DataFrame([[new_id, team_name, tournament_id]], columns=TEAMS_HDR)], ignore_index=True)
        save_csv(teams, TEAMS_CSV)
        st.success(f"Team '{team_name}' added (ID {new_id})")

def add_player():
    st.subheader("➕ Add Player")
    players = load_csv(PLAYERS_CSV, PLAYERS_HDR)
    teams = load_csv(TEAMS_CSV, TEAMS_HDR)
    if teams.empty:
        st.warning("Add teams first.")
        return
    team_choice = st.selectbox("Team", teams["team_name"].tolist())
    player_name = st.text_input("Player Name")
    phone_number = st.text_input("Player Phone Number")
    uploaded_file = st.file_uploader("Upload Player Photo", type=['jpg', 'jpeg', 'png'])
    
    if st.button("Add Player"):
        if not player_name.strip():
            st.warning("Enter player name")
            return
        team_id = int(teams[teams["team_name"] == team_choice]["team_id"].iloc[0])
        new_id = int(players["player_id"].max()) + 1 if not players.empty else 1
        
        # Check/Create columns
        if "phone_number" not in players.columns:
            players["phone_number"] = ""
        if "profile_image" not in players.columns:
            players["profile_image"] = ""
            
        image_path = ""
        if uploaded_file is not None:
            img_dir = os.path.join(DATA_PATH, "player_images")
            os.makedirs(img_dir, exist_ok=True)
            
            timestamp = int(datetime.datetime.now().timestamp())
            safe_name = "".join(x for x in player_name if x.isalnum())
            ext = uploaded_file.name.split('.')[-1]
            filename = f"{new_id}_{safe_name}_{timestamp}.{ext}"
            save_path = os.path.join(img_dir, filename)
            
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            image_path = save_path
            
        players = pd.concat([players, pd.DataFrame([[new_id, player_name, team_id, str(phone_number), image_path]], columns=["player_id", "player_name", "team_id", "phone_number", "profile_image"])], ignore_index=True)
        save_csv(players, PLAYERS_CSV)
        st.success(f"Player '{player_name}' added (ID {new_id})")
        if image_path:
            st.image(image_path, width=150, caption="Uploaded Photo")
def view_tournaments():
    st.subheader("📋 View Kabaddi Tournaments")

    tournaments = load_csv(TOURNAMENTS_CSV, TOURNAMENTS_HDR)
    matches = load_csv(MATCHES_CSV, MATCHES_HDR)
    teams = load_csv(TEAMS_CSV, TEAMS_HDR)

    if tournaments.empty:
        st.warning("No tournaments found. Please add a tournament first.")
        return

    selected_tournament = st.selectbox("Select Tournament", tournaments["tournament_name"].tolist())

    if selected_tournament:
        st.markdown(f"### Matches in {selected_tournament}")

        # Fetch Tournament ID
        tid = int(tournaments.loc[
            tournaments["tournament_name"] == selected_tournament,
            "tournament_id"
        ].iloc[0])

        # Filter matches of selected tournament
        t_matches = matches[matches["tournament_id"] == tid]

        if t_matches.empty:
            st.info("No matches scheduled for this tournament yet.")
            return

        # Helper function to fetch team name
        def get_team_name(team_id):
            row = teams[teams["team_id"] == int(team_id)]
            return row.iloc[0]["team_name"] if not row.empty else "Unknown"

        # Prepare UI table
        display_df = t_matches.copy()
        display_df["Team 1"] = display_df["team1_id"].apply(get_team_name)
        display_df["Team 2"] = display_df["team2_id"].apply(get_team_name)
        display_df["Match Date"] = display_df["match_date"]
        display_df["Venue"] = display_df["venue"]

        st.dataframe(
            display_df[["match_id", "Team 1", "Team 2", "Match Date", "Venue"]]
            .reset_index(drop=True)
        )
        
        # --- Tournament Stats ---
        st.divider()
        st.subheader("🏆 Tournament Hub")
        if st.button("📊 Series Stats & MVP"):
            scores_df = load_csv(SCORES_CSV, SCORES_HDR)
            players_df = load_csv(PLAYERS_CSV, PLAYERS_HDR)
            
            if scores_df.empty or t_matches.empty:
                st.warning("No data available.")
            else:
                # Filter scores for this tournament's matches
                tm_ids = t_matches["match_id"].tolist()
                t_scores = scores_df[scores_df["match_id"].isin(tm_ids)].copy()
                
                if t_scores.empty:
                    st.warning("No live scores recorded yet.")
                else:
                     # Aggregation
                     # We need to map player_id -> name
                     # Ensure points are numeric
                     t_scores["points"] = pd.to_numeric(t_scores["points"], errors='coerce').fillna(0).astype(int)
                     
                     stats = t_scores.groupby(["player_id", "event_type"])["points"].sum().unstack(fill_value=0).reset_index()
                     # stats columns: player_id, Bonus, Extra, Raid, Tackle (if present)
                     
                     if "Raid" not in stats.columns: stats["Raid"] = 0
                     if "Tackle" not in stats.columns: stats["Tackle"] = 0
                     if "Bonus" not in stats.columns: stats["Bonus"] = 0
                     if "Extra" not in stats.columns: stats["Extra"] = 0 # Extra might be assigned to dummy player or real? usually real if input.
                     
                     stats["Total_Raid_Points"] = stats["Raid"] + stats["Bonus"]
                     stats["Total_Tackle_Points"] = stats["Tackle"]
                     stats["Total_Points"] = stats["Total_Raid_Points"] + stats["Total_Tackle_Points"]
                     
                     # Merge Player Name
                     stats = pd.merge(stats, players_df, on="player_id", how="left")
                     stats["player_name"] = stats["player_name"].fillna("Unknown")
                     
                     # Sort by Total Points
                     leaderboard = stats.sort_values("Total_Points", ascending=False).head(10)
                     
                     top = leaderboard.iloc[0]
                     
                     c1, c2 = st.columns([1,2])
                     with c1:
                         st.markdown("### 🏅 Best Raider/MVP")
                         st.image("https://cdn-icons-png.flaticon.com/512/2583/2583319.png", width=80) 
                     with c2:
                         st.markdown(f"## **{top['player_name']}**")
                         st.markdown(f"**Total Points: {top['Total_Points']}**")
                         st.caption(f"Raid: {top['Total_Raid_Points']} | Tackle: {top['Total_Tackle_Points']}")
                     
                     st.dataframe(leaderboard[["player_name", "Total_Points", "Total_Raid_Points", "Total_Tackle_Points"]])

def schedule_match():
    st.subheader("📅 Schedule Match")
    matches = load_csv(MATCHES_CSV, MATCHES_HDR)
    teams = load_csv(TEAMS_CSV, TEAMS_HDR)
    tours = load_csv(TOURNAMENTS_CSV, TOURNAMENTS_HDR)
    if tours.empty or teams.empty:
        st.warning("Add tournaments and teams first.")
        return
    tour_choice = st.selectbox("Tournament", tours["tournament_name"].tolist())
    tournament_id = int(tours[tours["tournament_name"] == tour_choice]["tournament_id"].iloc[0])
    eligible = teams[teams["tournament_id"] == tournament_id]
    if eligible.shape[0] < 2:
        st.warning("Need at least 2 teams in the tournament.")
        return
    team1 = st.selectbox("Team 1", eligible["team_name"].tolist())
    team2 = st.selectbox("Team 2", [t for t in eligible["team_name"].tolist() if t != team1])
    match_date = st.date_input("Match Date")
    venue = st.text_input("Venue")
    if st.button("Schedule Match"):
        new_id = int(matches["match_id"].max()) + 1 if not matches.empty else 1
        t1_id = int(eligible[eligible["team_name"] == team1]["team_id"].iloc[0])
        t2_id = int(eligible[eligible["team_name"] == team2]["team_id"].iloc[0])
        matches = pd.concat(
            [matches, pd.DataFrame([[new_id, tournament_id, t1_id, t2_id, str(match_date), venue]], columns=MATCHES_HDR)],
            ignore_index=True
        )
        save_csv(matches, MATCHES_CSV)
        
        # Calculate Tournament Match Index
        count_in_tourney = matches[matches["tournament_id"] == tournament_id].shape[0]
        st.success(f"Match scheduled successfully! (ID {new_id}) — Match #{count_in_tourney} for this tournament")

# --------- Live match UI ----------
def render_scoreboard(team1_row, team2_row, team1_points, team2_points):
    col1, colmid, col2 = st.columns([3, 1, 3])
    with col1:
        st.markdown(f"### {team1_row['team_name']}")
        st.markdown(f"## {team1_points}")
    with colmid:
        st.markdown("### VS")
    with col2:
        st.markdown(f"### {team2_row['team_name']}")
        st.markdown(f"## {team2_points}")

def load_state_and_compute(match_id):
    state = load_state_row(int(match_id))
    # compute elapsed (accumulated + running)
    accumulated = float(state["accumulated_seconds"]) if state["accumulated_seconds"] != "" else 0.0
    if state["is_running"] and state["start_time_iso"]:
        try:
            start_dt = datetime.fromisoformat(state["start_time_iso"])
            delta = (datetime.utcnow() - start_dt).total_seconds()
            accumulated += delta
        except Exception:
            # malformed iso string — ignore and treat as paused
            pass
    # determine half automatically if necessary (but we persist half)
    # switch half if accumulated >= HALF_SECONDS and half == 1
    if accumulated >= HALF_SECONDS and int(state["half"]) == 1:
        state["half"] = 2
        # set accumulated_seconds to value >= HALF_SECONDS so 2nd half elapsed starts from HALF_SECONDS
        state["accumulated_seconds"] = float(accumulated)
        save_state_row(state)
    # compute elapsed_in_half and remaining
    total_elapsed = accumulated
    if int(state["half"]) == 1:
        elapsed_in_half = min(total_elapsed, HALF_SECONDS)
        remaining_in_half = max(HALF_SECONDS - elapsed_in_half, 0)
    else:
        elapsed_in_half = max(0, min(total_elapsed - HALF_SECONDS, HALF_SECONDS))
        remaining_in_half = max(HALF_SECONDS - elapsed_in_half, 0)
    # auto end match if total_elapsed >= TOTAL_SECONDS
    match_over = total_elapsed >= TOTAL_SECONDS
    return state, total_elapsed, elapsed_in_half, remaining_in_half, match_over

def update_live_match():
    st.subheader("🔴 Live Match")
    matches = load_csv(MATCHES_CSV, MATCHES_HDR)
    teams = load_csv(TEAMS_CSV, TEAMS_HDR)
    players = load_csv(PLAYERS_CSV, PLAYERS_HDR)
    scores = load_csv(SCORES_CSV, SCORES_HDR)

    if matches.empty:
        st.warning("No matches scheduled.")
        return

    # 1. Select Tournament
    tournaments = load_csv(TOURNAMENTS_CSV, TOURNAMENTS_HDR)
    if tournaments.empty:
        st.warning("No tournaments found.")
        return
        
    tourney_options = tournaments["tournament_name"].tolist()
    sel_tourney = st.selectbox("Select Tournament", tourney_options, key="live_tourney_select")
    
    # Get Tournament ID
    tourney_id = int(tournaments[tournaments["tournament_name"] == sel_tourney]["tournament_id"].iloc[0])
    
    # 2. Filter Matches
    tourney_matches = matches[matches["tournament_id"] == tourney_id]
    
    if tourney_matches.empty:
        st.info(f"No matches found for {sel_tourney}.")
        return

    # select match
    teams_df = load_csv(TEAMS_CSV)
    match_options = []
    
    # Calculate match number within tournament for display
    # We can just rank them by match_id or date
    tourney_matches = tourney_matches.sort_values("match_id")
    tourney_matches["match_number"] = range(1, len(tourney_matches) + 1)
    
    match_map = {}
    for _, r in tourney_matches.iterrows():
        t1 = get_team(teams_df, int(r["team1_id"]))["team_name"]
        t2 = get_team(teams_df, int(r["team2_id"]))["team_name"]
        mid = int(r["match_id"])
        mnum = r["match_number"]
        date = r["match_date"]
        label = f"Match #{mnum}: {t1} vs {t2} ({date})"
        match_map[label] = mid
        match_options.append(label)

    sel_label = st.selectbox("Select Match", match_options)
    mid = match_map[sel_label]
    
    match_row = matches[matches["match_id"] == mid].iloc[0]
    teams_df = load_csv(TEAMS_CSV)
    team1_row = get_team(teams_df, match_row["team1_id"])
    team2_row = get_team(teams_df, match_row["team2_id"])

    # compute totals
    totals = compute_scores_for_match(mid)
    t1_points = totals.get(int(team1_row["team_id"]), 0)
    t2_points = totals.get(int(team2_row["team_id"]), 0)

    render_scoreboard(team1_row, team2_row, t1_points, t2_points)

    # --- Active Players Dots Visualization ---
    st.markdown("### 🟢 Active Players on Mat")
    
    # Load current active counts
    state = load_state_row(mid)
    
    # Safely get counts (handle existing rows missing these fields)
    t1_active = int(state.get("team1_active_count", 7))
    t2_active = int(state.get("team2_active_count", 7))
    
    # Visual Logic: Generic dots
    def render_dots(count, color_hex="#4CAF50"):
        # count is 0-7
        dots_html = ""
        for i in range(7):
            if i < count:
                dots_html += f"<span style='display:inline-block; width:20px; height:20px; border-radius:50%; background-color:{color_hex}; margin:2px;'></span>"
            else:
                dots_html += f"<span style='display:inline-block; width:20px; height:20px; border-radius:50%; background-color:#ccc; margin:2px;'></span>"
        return dots_html

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**{team1_row['team_name']}** ({t1_active})")
        st.markdown(render_dots(t1_active, "#E91E63"), unsafe_allow_html=True) # Pink/Reddish
    with c2:
        st.markdown(f"**{team2_row['team_name']}** ({t2_active})")
        st.markdown(render_dots(t2_active, "#2196F3"), unsafe_allow_html=True) # Blue
        
    # Manual Adjusters (Collapsible)
    with st.expander("Adjust Active Players Manually"):
        col_adj1, col_adj2 = st.columns(2)
        new_t1 = col_adj1.slider(f"{team1_row['team_name']} Count", 1, 7, t1_active, key="slider_t1_active")
        new_t2 = col_adj2.slider(f"{team2_row['team_name']} Count", 1, 7, t2_active, key="slider_t2_active")
        
        if st.button("Update Counts"):
            state["team1_active_count"] = new_t1
            state["team2_active_count"] = new_t2
            save_state_row(state)
            st.success("Updated!")
            safe_rerun()
            
    # controls_start
    # controls
    st.markdown("### ⏱ Clock Controls")
    cols = st.columns(4)
    start_btn = cols[0].button("▶ Start / Resume")
    pause_btn = cols[1].button("⏸ Pause")
    reset_btn = cols[2].button("🔄 Reset Match")

    # load state
    state = load_state_row(mid)

    # start/resume
    if start_btn:
        if not state["is_running"]:
            state["is_running"] = True
            state["start_time_iso"] = datetime.utcnow().isoformat()
            save_state_row(state)
            st.success("Timer started/resumed.")
        else:
            st.info("Timer already running.")

    # pause
    if pause_btn:
        if state["is_running"] and state["start_time_iso"]:
            try:
                start_dt = datetime.fromisoformat(state["start_time_iso"])
                delta = (datetime.utcnow() - start_dt).total_seconds()
            except Exception:
                delta = 0.0
            state["accumulated_seconds"] = float(state["accumulated_seconds"]) + delta
            state["is_running"] = False
            state["start_time_iso"] = ""
            save_state_row(state)
            st.success("Timer paused.")
        else:
            st.info("Timer not running.")

    # reset
    if reset_btn:
        state = {
            "match_id": mid,
            "half": 1,
            "start_time_iso": "",
            "accumulated_seconds": 0.0,
            "is_running": False,
            "team1_timeouts": 0,
            "team2_timeouts": 0,
            "team1_active_count": 7,
            "team2_active_count": 7
        }
        save_state_row(state)
        st.success("Match reset.")

    # compute updated timing info
    state, total_elapsed, elapsed_in_half, remaining_in_half, match_over = load_state_and_compute(mid)

    # auto-switch half if required (handled in load_state_and_compute); persist again just in case
    save_state_row(state)

    # display times
    st.markdown(f"### **Current Half:** {int(state['half'])}")
    
    # Countdown Display
    rem_min = int(remaining_in_half)//60
    rem_sec = int(remaining_in_half)%60
    st.markdown(f"## **{rem_min:02d}:{rem_sec:02d}** (Countdown)")
    
    # Status line
    st.caption(f"Elapsed: {int(elapsed_in_half)//60:02d}:{int(elapsed_in_half)%60:02d} | Total: {int(total_elapsed)//60:02d}:{int(total_elapsed)%60:02d}")

    if match_over:
        st.success("🏁 Match ended (40 minutes). Timer stopped.")
        # ensure stopped
        if state["is_running"]:
            state["is_running"] = False
            state["start_time_iso"] = ""
            save_state_row(state)

    # Match timer refresh moved to end of function to avoid blocking UI rendering


    # --- RAID TIMER (30s) ---
    st.markdown("---")
    st.markdown("### ⏱ Raid Timer")
    
    col_r1, col_r2, col_r3 = st.columns(3)
    
    # Init Raid Timer State
    if "kb_raid_start" not in st.session_state:
        st.session_state["kb_raid_start"] = None
    if "kb_raid_paused" not in st.session_state:
        st.session_state["kb_raid_paused"] = False
    if "kb_raid_elapsed" not in st.session_state:
        st.session_state["kb_raid_elapsed"] = 0.0
    
    raid_duration = 30 # seconds
    
    with col_r1:
        if st.button("🚀 Start / Resume", use_container_width=True):
            if st.session_state["kb_raid_start"] is None:
                st.session_state["kb_raid_start"] = time.time()
                st.session_state["kb_raid_paused"] = False
            elif st.session_state["kb_raid_paused"]:
                st.session_state["kb_raid_start"] = time.time() - st.session_state["kb_raid_elapsed"]
                st.session_state["kb_raid_paused"] = False
            safe_rerun()
            
    with col_r2:
        if st.button("⏸ Pause", use_container_width=True):
            if st.session_state["kb_raid_start"] is not None and not st.session_state["kb_raid_paused"]:
                st.session_state["kb_raid_elapsed"] = time.time() - st.session_state["kb_raid_start"]
                st.session_state["kb_raid_paused"] = True
                safe_rerun()
                
    with col_r3:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state["kb_raid_start"] = None
            st.session_state["kb_raid_paused"] = False
            st.session_state["kb_raid_elapsed"] = 0.0
            safe_rerun()

    # Display Raid Time
    current_raid_val = 30.0
    if st.session_state["kb_raid_start"] is not None:
        if st.session_state["kb_raid_paused"]:
            e = st.session_state["kb_raid_elapsed"]
        else:
            e = time.time() - st.session_state["kb_raid_start"]
        
        raid_rem = max(0, raid_duration - e)
        
        # Color coding: Green > 10s, Yellow > 5s, Red <= 5s
        color = "#4CAF50" # Green
        if raid_rem <= 5: color = "#F44336" # Red
        elif raid_rem <= 10: color = "#FF9800" # Orange
        
        st.markdown(f"<h1 style='text-align:center; color: {color}; font-size: 50px;'>{int(raid_rem)}s</h1>", unsafe_allow_html=True)
        
        # Auto-stop if done
        if raid_rem <= 0:
            st.session_state["kb_raid_start"] = None
            st.session_state["kb_raid_paused"] = False
            st.session_state["kb_raid_elapsed"] = 0.0
            st.rerun()
    else:
        st.markdown("<h1 style='text-align:center; color: #888; font-size: 50px;'>30s</h1>", unsafe_allow_html=True)


    # --- Event Recording (Button Flow) ---
    st.markdown("---")
    st.markdown("### ➕ Record Event (Button Mode)")

    # 1. Initialize State Machine for Flow
    if "kb_step" not in st.session_state:
        st.session_state["kb_step"] = "TYPE_SELECT" # TYPE_SELECT -> DETAILS -> CONFIRM
    if "kb_event_type" not in st.session_state:
        st.session_state["kb_event_type"] = None

    # Helper to reset
    def reset_kb_flow():
        st.session_state["kb_step"] = "TYPE_SELECT"
        st.session_state["kb_event_type"] = None
        st.session_state["kb_temp_data"] = {}

    if st.button("❌ Cancel / Reset Form"):
        reset_kb_flow()
        safe_rerun()

    # STEP 1: SELECT EVENT TYPE
    if st.session_state["kb_step"] == "TYPE_SELECT":
        st.info("Select Event Type:")
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("🏃 Raid Point", use_container_width=True):
            st.session_state["kb_event_type"] = "Raid"
            st.session_state["kb_step"] = "DETAILS"
            safe_rerun()
        if c2.button("🤼 Tackle Point", use_container_width=True):
            st.session_state["kb_event_type"] = "Tackle"
            st.session_state["kb_step"] = "DETAILS"
            safe_rerun()
        if c3.button("🎁 Bonus Point", use_container_width=True):
            st.session_state["kb_event_type"] = "Bonus"
            st.session_state["kb_step"] = "DETAILS"
            safe_rerun()
        if c4.button("🛑 All Out / Extra", use_container_width=True):
             st.session_state["kb_event_type"] = "Extra"
             st.session_state["kb_step"] = "DETAILS"
             safe_rerun()

    # STEP 2: DETAILS
    if st.session_state["kb_step"] == "DETAILS":
        evt = st.session_state["kb_event_type"]
        st.markdown(f"#### Recording: **{evt}**")
        
        # A. Select Team involved (OUTSIDE FORM to trigger rerun)
        scoring_team_name = st.selectbox("Scoring Team", [team1_row["team_name"], team2_row["team_name"]])
        scoring_team_id = int(team1_row["team_id"]) if scoring_team_name == team1_row["team_name"] else int(team2_row["team_id"])
        
        # Determine Lists
        p_df = load_csv(PLAYERS_CSV, PLAYERS_HDR)
        scorers_list = p_df[p_df["team_id"] == scoring_team_id]["player_name"].tolist()
        
        defending_team_id = int(team2_row["team_id"]) if scoring_team_id == int(team1_row["team_id"]) else int(team1_row["team_id"])
        defenders_list = p_df[p_df["team_id"] == defending_team_id]["player_name"].tolist()
        
        with st.form("kb_event_form"):
            # UI logic uses pre-calculated lists
            points = 0
            details_text = ""
            main_player = ""
            is_all_out = False  # Ensure initialized
            
            if evt == "Raid":
                st.markdown("##### Raid Details")
                touch_points = st.number_input("Touch Points (Players Out)", 0, 7, 1)
                bonus = st.checkbox("Plus Bonus Point? (+1)")
                
                # Super Raid logic? Just checking box
                if touch_points + int(bonus) >= 3:
                    st.caption("🔥 This is a **SUPER RAID**!")

                points = touch_points + int(bonus)
                
                main_player = st.selectbox("Raider (Who scored?)", scorers_list)
                
                # Opponent Selection
                outs = st.multiselect("Who is out? (Defenders)", defenders_list)
                details_text = ", ".join(outs)

            elif evt == "Tackle":
                st.markdown("##### Tackle Details")
                is_super = st.checkbox("Super Tackle? (2 pts)", value=False)
                points = 2 if is_super else 1
                
                main_player = st.selectbox("Defender (Who tackled?)", scorers_list)
                
                # Who was tackled? (Opponent Raider)
                raider_out = st.selectbox("Raider Out (Name)", defenders_list)
                details_text = raider_out
                
            elif evt == "Bonus":
                points = 1
                main_player = st.selectbox("Raider (Who took bonus?)", scorers_list)
            
            elif evt == "Extra":
                st.markdown("##### Extras (All Out / Technical)")
                is_all_out = st.checkbox("All Out Award (2 pts)")
                tech_pts = st.number_input("Technical Points", 0, 5, 0)
                points = (2 if is_all_out else 0) + tech_pts
                details_text = "All Out" if is_all_out else "Technical"
            
            # Minute
            current_minute = int(total_elapsed // 60)
            mnt = st.number_input("Minute", 0, 40, current_minute)

            if st.form_submit_button("✅ Confirm Event"):
                # Save
                new_row = {
                    "match_id": int(mid),
                    "minute": int(mnt),
                    "event_type": evt,
                    "player_id": int(p_df[p_df["player_name"]==main_player]["player_id"].iloc[0]) if main_player and main_player in scorers_list else "",
                    "team_id": int(scoring_team_id),
                    "points": int(points),
                    "details": details_text,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                scores_df = load_csv(SCORES_CSV, SCORES_HDR)
                scores_df = pd.concat([scores_df, pd.DataFrame([new_row])], ignore_index=True)
                save_csv(scores_df, SCORES_CSV)
                
                # --- Auto-Update Active Players ---
                st_up = load_state_row(mid)
                a1 = int(st_up.get("team1_active_count", 7))
                a2 = int(st_up.get("team2_active_count", 7))
                
                # Identify scoring/defending vs Team 1/2
                # scoring_team_id, defending_team_id are available
                t1_id = int(team1_row["team_id"])
                
                # Helper: Get current counts for Scorer / Defender
                if scoring_team_id == t1_id:
                    s_active, d_active = a1, a2
                else:
                    s_active, d_active = a2, a1
                    
                # Apply Rules
                if evt == "Raid":
                    # touch_points defined in Raid block
                    # Defender loses touch_points
                    # Scorer (Attacker) gains touch_points (Revival)
                    d_active = max(0, d_active - touch_points)
                    s_active = min(7, s_active + touch_points)
                    
                elif evt == "Tackle":
                    # Scorer = Defender who tackled. Opponent = Raider.
                    # Raider Team (Opponent) loses 1
                    # Scorer Team gains 1 (Revival)
                    d_active = max(0, d_active - 1)
                    s_active = min(7, s_active + 1)
                    
                elif evt == "Extra":
                    if is_all_out:
                        # If Scoring Team gets All Out, Opponent was All Out -> Reset to 7
                        d_active = 7
                        st.toast("Opponent Team Revived to 7 Players! 🏃‍♂️", icon="🔄")
                        
                # Assign back
                if scoring_team_id == t1_id:
                    st_up["team1_active_count"] = s_active
                    st_up["team2_active_count"] = d_active
                else:
                    st_up["team1_active_count"] = d_active
                    st_up["team2_active_count"] = s_active
                    
                save_state_row(st_up)
                
                st.success("Event Recorded & Player Counts Updated!")
                reset_kb_flow()
                safe_rerun()

    # Recent events (Commentary Style)
    st.markdown("---")
    st.subheader("🎙 Commentary (Recent Events)")
    scores_df = load_csv(SCORES_CSV, SCORES_HDR)
    if not scores_df.empty:
        # Filter and Sort
        display = scores_df[scores_df["match_id"] == int(mid)].sort_values("timestamp", ascending=False).head(10)
        
        # Merge names
        p_df = load_csv(PLAYERS_CSV, PLAYERS_HDR)
        t_df = load_csv(TEAMS_CSV, TEAMS_HDR)
        
        if not display.empty:
            display = display.merge(p_df[["player_id", "player_name"]], how="left", on="player_id")
            display = display.merge(t_df[["team_id", "team_name"]], how="left", on="team_id")
            
            for _, row in display.iterrows():
                # Construct Commentary String
                # Format: Minute XX | Event Type | Player Name (Team) | Details
                min_str = f"**{row['minute']}'**"
                evt_type = row['event_type']
                p_name = row['player_name'] if pd.notna(row['player_name']) else "Matches"
                t_name = row['team_name'] if pd.notna(row['team_name']) else ""
                pts = row['points']
                dets = row['details'] if pd.notna(row['details']) else ""
                
                # Contextual Description
                desc = ""
                highlight = ""
                
                if evt_type == "Raid":
                    desc = f"**{p_name}** ({t_name}) scored **{pts} pts**"
                    if "Super Raid" in dets or pts >= 3: highlight = "🔥 **SUPER RAID**"
                    if dets: desc += f" [{dets}]"
                    
                elif evt_type == "Tackle":
                    desc = f"**{p_name}** ({t_name}) initiated a **Super Tackle**" if pts > 1 else f"**{p_name}** ({t_name}) tackled successfully"
                    desc += f" (**{pts} pts**)"
                    if dets: desc += f" [Raider Out: {dets}]"
                    if pts > 1: highlight = "🛡 **SUPER TACKLE**"
                    
                elif evt_type == "Bonus":
                    desc = f"**Bonus Point** for **{p_name}** ({t_name})"
                    
                elif evt_type == "Extra":
                    desc = f"**{t_name}** awarded **{pts} pts** ({dets})"
                    if "All Out" in str(dets): highlight = "🛑 **ALL OUT**"
                    
                # Render
                st.markdown(f"{min_str} | {evt_type} | {desc} {highlight}")
                st.divider()
        else:
             st.info("No events recorded yet.")

    # --- Combined Auto-Refresh Logic ---
    # Trigger rerun at the end to ensure ALL UI components (timers, forms, tables) are rendered first.
    should_rerun = False
    
    # 1. Match Timer Running?
    if state["is_running"] and not match_over:
        should_rerun = True
        
    # 2. Raid Timer Running?
    if st.session_state.get("kb_raid_start") is not None and not st.session_state.get("kb_raid_paused"):
         # Double check if raid finished (though handled in block above, good for safety)
         # Using cached logic or recompute
         r_elapsed = time.time() - st.session_state["kb_raid_start"]
         if max(0, 30 - r_elapsed) > 0:
             should_rerun = True
    
    if should_rerun:
        time.sleep(1)
        st.rerun()

# ---------- AWARDS LOGIC ----------
def compute_kabaddi_awards(match_id: int):
    """
    Compute:
      - Best Raider
      - Best Defender
      - Best All-rounder
      - Game-changing moment player
    using advanced MVP formula:
       MVP = Raid*2 + Tackle*3.5 + Bonus*1 + SuperRaid*5 + SuperTackle*4
    Super Raid   = single raid with points >= 3
    Super Tackle = single tackle with points >= 2  (approximation)
    """
    scores = load_csv(SCORES_CSV, SCORES_HDR)
    if scores.empty:
        return None

    df = scores[scores["match_id"] == int(match_id)].copy()
    if df.empty:
        return None

    # Merge player names
    players = load_csv(PLAYERS_CSV, PLAYERS_HDR)
    df = df.merge(players, how="left", left_on="player_id", right_on="player_id")

    # Only scoring events matter
    scoring_df = df[df["event_type"].isin(["Raid", "Tackle", "Bonus"])].copy()
    if scoring_df.empty:
        return None

    # Super raids / super tackles flags per event
    scoring_df["super_raid"] = ((scoring_df["event_type"] == "Raid") & (scoring_df["points"] >= 3)).astype(int)
    scoring_df["super_tackle"] = ((scoring_df["event_type"] == "Tackle") & (scoring_df["points"] >= 2)).astype(int)

    # Aggregate stats by player
    def sum_points(evt):
        sub = scoring_df[scoring_df["event_type"] == evt]
        if sub.empty:
            return pd.DataFrame(columns=["player_id", f"{evt.lower()}_points"])
        return (
            sub.groupby("player_id")["points"]
            .sum()
            .reset_index()
            .rename(columns={"points": f"{evt.lower()}_points"})
        )

    raid_stats = sum_points("Raid")
    tackle_stats = sum_points("Tackle")
    bonus_stats = sum_points("Bonus")

    super_raid_stats = (
        scoring_df.groupby("player_id")["super_raid"]
        .sum()
        .reset_index()
        .rename(columns={"super_raid": "super_raids"})
    )
    super_tackle_stats = (
        scoring_df.groupby("player_id")["super_tackle"]
        .sum()
        .reset_index()
        .rename(columns={"super_tackle": "super_tackles"})
    )
    # Base DF with unique players
    # Resolve team_id column after merge
    if "team_id" not in scoring_df.columns:
        if "team_id_x" in scoring_df.columns:
            scoring_df["team_id"] = scoring_df["team_id_x"]
        elif "team_id_y" in scoring_df.columns:
            scoring_df["team_id"] = scoring_df["team_id_y"]

    base = scoring_df[["player_id", "player_name", "team_id"]].drop_duplicates()
    # Merge all metrics
    stats = base.merge(raid_stats, how="left", on="player_id")
    stats = stats.merge(tackle_stats, how="left", on="player_id")
    stats = stats.merge(bonus_stats, how="left", on="player_id")
    stats = stats.merge(super_raid_stats, how="left", on="player_id")
    stats = stats.merge(super_tackle_stats, how="left", on="player_id")

    for col in ["raid_points", "tackle_points", "bonus_points", "super_raids", "super_tackles"]:
        if col in stats.columns:
            stats[col] = stats[col].fillna(0).astype(int)
        else:
            stats[col] = 0

    stats["total_points"] = stats["raid_points"] + stats["tackle_points"] + stats["bonus_points"]

    # Advanced MVP formula
    stats["mvp_score"] = (
        stats["raid_points"] * 2.0
        + stats["tackle_points"] * 3.5
        + stats["bonus_points"] * 1.0
        + stats["super_raids"] * 5.0
        + stats["super_tackles"] * 4.0
    )

    # Best roles
    best_raider = stats.sort_values(
        ["raid_points", "mvp_score", "total_points"],
        ascending=[False, False, False]
    ).head(1)

    best_defender = stats.sort_values(
        ["tackle_points", "mvp_score", "total_points"],
        ascending=[False, False, False]
    ).head(1)

    # All-rounder: must have both raid and tackle points
    allround_df = stats[(stats["raid_points"] > 0) & (stats["tackle_points"] > 0)]
    if allround_df.empty:
        best_allrounder = None
    else:
        best_allrounder = allround_df.sort_values(
            ["mvp_score", "total_points"],
            ascending=[False, False]
        ).head(1)

    # Game changing moment: highest single scoring raid/tackle
    gc_events = scoring_df[scoring_df["event_type"].isin(["Raid", "Tackle"])]
    gc_events = gc_events.sort_values(["points", "minute"], ascending=[False, True])
    gc_event = gc_events.head(1) if not gc_events.empty else None

    return {
        "stats": stats.sort_values("mvp_score", ascending=False),
        "best_raider": best_raider,
        "best_defender": best_defender,
        "best_allrounder": best_allrounder,
        "game_changer": gc_event
    }

# --------- Summary view ----------
def view_summary():
    st.subheader("📊 Match Summary")
    scores_df = load_csv(SCORES_CSV, SCORES_HDR)
    if scores_df.empty:
        st.warning("No events recorded.")
        return

    matches = load_csv(MATCHES_CSV, MATCHES_HDR)
    if matches.empty:
        st.warning("No matches file.")
        return

    match_choice = st.selectbox("Select match", matches["match_id"].tolist())
    m = int(match_choice)
    match_scores = scores_df[scores_df["match_id"] == m]
    if match_scores.empty:
        st.info("No events for this match.")
        return

    teams = load_csv(TEAMS_CSV, TEAMS_HDR)
    players = load_csv(PLAYERS_CSV, PLAYERS_HDR)

    # Team totals
    totals = match_scores.groupby("team_id")["points"].sum().reset_index()
    totals = totals.merge(teams[["team_id", "team_name"]], on="team_id", how="left")
    st.markdown("### Team Points")
    st.table(totals)

    # Player totals (raw points)
    player_totals = match_scores.groupby("player_id")["points"].sum().reset_index()
    player_totals = player_totals.merge(players[["player_id", "player_name"]], on="player_id", how="left")
    st.markdown("### Player Total Points (raw)")
    st.table(player_totals.sort_values("points", ascending=False))

    # Check if match is finished (40 mins done)
    if not is_match_over(m):
        st.info("⏱ Match is still LIVE – awards will be shown automatically once full 40 minutes are completed.")
        return

    # --------- Awards Section ----------
    st.markdown("---")
    st.subheader("🏆 Kabaddi Awards")

    awards = compute_kabaddi_awards(m)
    if not awards:
        st.info("Not enough data to compute awards yet.")
        return

    stats = awards["stats"]
    best_raider = awards["best_raider"]
    best_defender = awards["best_defender"]
    best_allrounder = awards["best_allrounder"]
    game_changer = awards["game_changer"]

    # Best Raider
    if best_raider is not None and not best_raider.empty:
        r = best_raider.iloc[0]
        st.success(
            f"🔥 **Best Raider:** {r['player_name']} "
            f"(Raid Points: {r['raid_points']}, Super Raids: {r['super_raids']})"
        )

    # Best Defender
    if best_defender is not None and not best_defender.empty:
        d = best_defender.iloc[0]
        st.info(
            f"🛡 **Best Defender:** {d['player_name']} "
            f"(Tackle Points: {d['tackle_points']}, Super Tackles: {d['super_tackles']})"
        )

    # Best All-rounder
    if best_allrounder is not None and not best_allrounder.empty:
        a = best_allrounder.iloc[0]
        st.warning(
            f"🔁 **Best All-Rounder:** {a['player_name']} "
            f"(Raid: {a['raid_points']}, Tackle: {a['tackle_points']}, "
            f"Bonus: {a['bonus_points']}, MVP: {a['mvp_score']:.1f})"
        )
    else:
        st.warning("🔁 No proper all-rounder (no one has both raid and tackle points).")

    # Game-changing moment
    if game_changer is not None and not game_changer.empty:
        g = game_changer.iloc[0]
        g_name = g["player_name"]
        g_evt = g["event_type"]
        g_min = g["minute"]
        g_pts = g["points"]
        st.markdown(
            f"⚡ **Game-Changing Moment:** {g_name} at minute {g_min} – "
            f"{g_evt} for **{g_pts} points**"
        )

    # Show detailed advanced stats table
    st.markdown("### 🌟 Detailed Player Performance (Advanced)")
    show_cols = [
        "player_name", "team_id", "raid_points", "tackle_points",
        "bonus_points", "super_raids", "super_tackles",
        "total_points", "mvp_score"
    ]
    st.dataframe(stats[show_cols].reset_index(drop=True))

def run():
    st.title("Kabaddi Dashboard")
    st.write("Live kabaddi stats go here...")

# --------- Main runner ----------
def run_kabaddi():
    st.sidebar.title("kabaddi Module")
    menu = [
        "Add Tournament", "Add Team", "Add Player",
        "View Tournaments", "Schedule Match",
        "Update Live Match", "View Match Summary"
    ]
    choice = st.sidebar.radio("Menu", menu)

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
    elif choice == "Update Live Match":
        update_live_match()
    elif choice == "View Match Summary":
        view_summary()

