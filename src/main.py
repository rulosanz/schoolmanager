import streamlit as st
import login
import app

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user:
    app.app_main()  # Ejecuta la app principal
else:
    login.login()   # Ejecuta el login