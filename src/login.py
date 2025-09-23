import streamlit as st
import time
from supabase import create_client

supabase_url = st.secrets["supabase"]["url"]
supabase_key = st.secrets["supabase"]["key"]
supabase = create_client(supabase_url, supabase_key)

def login():
    st.title("Login")

    email = st.text_input("Email")
    password = st.text_input("Contraseña", type="password")

    if st.button("Iniciar sesión"):
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            user = response.user
            if user:
                st.session_state.user = user
                st.success(f"Bienvenido {user.email}")
                time.sleep(2)
                st.rerun()  # Recarga para mostrar app.py
            else:
                st.error("Credenciales incorrectas")
        except Exception as e:
            st.error(f"Error: {e}")
