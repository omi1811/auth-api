import streamlit as st
import requests
import os

API_URL = os.environ.get("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Auth System", layout="centered")
st.title("JWT Auth Demo")

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None

# 🔹 LOGIN SECTION
if st.session_state.token is None:
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        res = requests.post(
            f"{API_URL}/login",
            json={"email": email, "password": password}
        )
        if res.status_code == 200:
            st.session_state.token = res.json()["access_token"]
            st.success(" Logged in!")
            st.rerun()
        else:
            try:
                error_detail = res.json().get("detail", "Unknown error")
            except requests.exceptions.JSONDecodeError:
                error_detail = f"Server error ({res.status_code}). Check backend terminal."
            st.error(f" {error_detail}")
    
    st.divider()
    
    # Quick register link
    with st.expander("Don't have an account? Register"):
        reg_email = st.text_input("Register Email", key="reg_email")
        reg_password = st.text_input("Register Password", type="password", key="reg_pw")
        if st.button("Register"):
            res = requests.post(
                f"{API_URL}/register",
                json={"email": reg_email, "password": reg_password}
            )
            if res.status_code in [201, 200]:
                st.success("Registered! Now login above.")
                reg_email = ""
                reg_password = ""
            else:
                try:
                    error_detail = res.json().get("detail", "Unknown error")
                except requests.exceptions.JSONDecodeError:
                        # Fallback if backend returns HTML/plain text or empty response
                    error_detail = f"Server error ({res.status_code}). Check backend terminal for logs."

                st.error(f"{error_detail}")

# 🔹 AUTHENTICATED SECTION
else:
    st.success("🔑 Logged in!")
    
    # Show profile
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    res = requests.get(f"{API_URL}/profile", headers=headers)
    
    if res.status_code == 200:
        profile = res.json()
        st.json(profile)
    else:
        st.error("Token expired or invalid")
        st.session_state.token = None
        st.rerun()
    
    if st.button("Logout"):
        st.session_state.token = None
        st.rerun()