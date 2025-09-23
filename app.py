import streamlit as st
import pandas as pd
import datetime
from numpy.random import default_rng as rng

def layout():
    # Opciones del selectbox (el índice 0 es el "None")
    opciones = ["-- Selecciona --", "Agregar alumn@", "Crear actividad", "Revisar actividad"]
    # --- Definimos los diálogos ---
    @st.dialog("Agregar alumn@")
    def alumno():
        id_student = st.text_input("ID")
        name_student = st.text_input("Nombre")
        tel_student = st.text_input("Teléfono")
        email_student = st.text_input("Email")
        if st.button("Guardar"):
            st.session_state.student = {
                "id": id_student,
                "nombre": name_student,
                "telefono": tel_student,
                "email": email_student,
            }
            st.session_state["modal"] = None
            st.session_state["accion"] = opciones[0]  # 🔄 reset al placeholder
            st.rerun()
    @st.dialog("Crear actividad")
    def agregar():
        activity_type = st.selectbox(
            "Tipo de actividad",
            ("Examen", "Actividad Libro", "Exposicion", "Trabajo en clase", "Otra"),
        )
        name_activity = st.text_input("Nombre de la actividad")
        description_activity = st.text_input("Descripcion")
        parcial = st.selectbox(
            "Parcial",
            ("1", "2", "3"),
        )
        possible_hits = st.text_input("Posibles aciertos")
        delivery_date = st.date_input("¿Cuándo se entrega?", datetime.date.today())
        if st.button("Guardar"):
            st.session_state.activity = {"actividad": name_activity}
            st.session_state["modal"] = None
            st.session_state["accion"] = opciones[0]
            st.rerun()
    @st.dialog("Revisar actividad")
    def revisar():
        select_activity = st.selectbox(
            "Actividad",
            ("A", "B", "C"),
        )
        activity_id = st.text_input("Ingresa el código o escanéalo con el lector")
        st.write("tabla")
        if st.button("Guardar"):
            st.session_state.revision = {"activity_name": select_activity, "activity_id": activity_id, "date_delivered": datetime.datetime.now()}
            st.session_state["modal"] = None
            st.session_state["accion"] = opciones[0]
            if "revision" in st.session_state:
                st.success(
                    f"✅ Revisión guardada:\n\n"
                    f"- Actividad Revisada: {st.session_state.revision}"
                )
            #st.rerun()
    
    # --- Selector principal ---
    opcion = st.selectbox(
        "Que deseas hacer?",
        opciones,
        index=0,
        key="accion"
    )
    # Guardamos en session_state qué modal abrir
    if opcion != opciones[0]:
        st.session_state["modal"] = opcion
    # Abrimos el modal correspondiente
    if st.session_state.get("modal") == "Agregar alumn@":
        alumno()
    elif st.session_state.get("modal") == "Crear actividad":
        agregar()
    elif st.session_state.get("modal") == "Revisar actividad":
        revisar()
    df = pd.DataFrame(
        [
            {"ID": "767586568", "Nombre": "Juan Perez", "Actividad 1": "", "Actividad 2": "", "Actividad 3": ""}
        ]
    )
    edited_df = st.data_editor(df)
    favorite_command = edited_df.loc[edited_df["Actividad 1"].idxmax()]["ID"]

#def app_main():
st.title("Control escolar")
subtab1, subtab2, subtab3 = st.tabs(["Medicina 1A", "Medicina 1B", "Nutricion 4C"])
with subtab1:
    layout()
with subtab2:
    st.write("Estadistica Medica")
with subtab3:
    st.write("Estadistica Medica")    

