import streamlit as st

def init_session():
    defaults = {
        "logged_in": False,
        "user_email": None,
        "user_name": None,
        "user_id": None,
        "user_role": None,
        "user_avatar": None,
        "fcm_token": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
