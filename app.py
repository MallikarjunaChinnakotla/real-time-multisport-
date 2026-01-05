import streamlit as st

# Import all 9 sport modules
from sports import (
    cricket,
    football,
    basketball,
    volleyball,
    kabaddi,
    handball,
    table_tennis,
    hockey,
    softball
)

# --- Main App ---
def main():
    st.set_page_config(page_title="🏆 Multi-Sports Dashboard", layout="centered")

    st.markdown("Welcome! Select a sport from the sidebar to begin.")

    # Sidebar Sport Selection
    sport = st.sidebar.selectbox(
        "Select a Sport",
        (
            "Cricket",
            "Football",
            "Basketball",
            "Volleyball",
            "Kabaddi",
            "Handball",
            "Table Tennis",
            "Hockey",
            "Softball"
        )
    )

    if sport == "Cricket":
        cricket.c_run()
        cricket.run_cricket()

    elif sport == "Football":
        football.run()
        football.run_football()

    elif sport == "Basketball":
        basketball.run()
        basketball.run_basketball()

    elif sport == "Volleyball":
        volleyball.run()
        volleyball.run_volleyball()

    elif sport == "Kabaddi":
        kabaddi.run()
        kabaddi.run_kabaddi()

    elif sport == "Handball":
        handball.run()
        handball.run_handball()

    elif sport == "Table Tennis":
        table_tennis.run()
        table_tennis.run_table_tennis()

    elif sport == "Hockey":
        hockey.run()
        hockey.run_hockey()

    elif sport == "Softball":
        softball.run()
        softball.run_softball()


if __name__ == "__main__":
    main()

