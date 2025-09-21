import streamlit as st
import pandas as pd
from numpy.random import default_rng as rng

st.title("Control escolar - Docente")


subtab1, subtab2, subtab3 = st.tabs(["Medicina 1A", "Medicina 1B", "Nutricion 4C"])
with subtab1:
    # Opciones del selectbox (el índice 0 es el "None")
    opciones = ["-- Selecciona --", "Agregar alumn@", "Crear actividad", "Revisar actividad"]

    # --- Definimos los diálogos ---
    @st.dialog("Agregar alumn@")
    def alumno():
        id_ = st.text_input("ID")
        nombre = st.text_input("Nombre")
        tel = st.text_input("Teléfono")
        email = st.text_input("Email")

        if st.button("Guardar"):
            st.session_state.vote = {
                "id": id_,
                "nombre": nombre,
                "telefono": tel,
                "email": email,
            }
            st.session_state["modal"] = None
            st.session_state["accion"] = opciones[0]  # 🔄 reset al placeholder
            st.rerun()


    @st.dialog("Crear actividad")
    def agregar():
        option = st.selectbox(
            "How would you like to be contacted?",
            ("Examen", "Actividad Libro", "Exposicion", "Trabajo en clase", "Otra"),
        )
        nombre = st.text_input("Nombre de la actividad")
        descripcion = st.text_input("Descripcion")
        if st.button("Guardar"):
            st.session_state.vote = {"actividad": nombre}
            st.session_state["modal"] = None
            st.session_state["accion"] = opciones[0]
            st.rerun()


    @st.dialog("Revisar actividad")
    def revisar():
        id_ = st.text_input("Ingresa el código o escanéalo con el lector")
        df = pd.DataFrame(
            {
                "name": ["Roadmap", "Extras", "Issues"],
                "url": [
                    "https://roadmap.streamlit.app",
                    "https://extras.streamlit.app",
                    "https://issues.streamlit.app",
                ],
                "stars": rng(0).integers(0, 1000, size=3),
                "views_history": rng(0).integers(0, 5000, size=(3, 30)).tolist(),
            }
        )

        st.dataframe(
            df,
            column_config={
                "name": "App name",
                "stars": st.column_config.NumberColumn(
                    "Github Stars",
                    help="Number of stars on GitHub",
                    format="%d ⭐",
                ),
                "url": st.column_config.LinkColumn("App URL"),
                "views_history": st.column_config.LineChartColumn(
                    "Views (past 30 days)", y_min=0, y_max=5000
                ),
            },
            hide_index=True,
        )


        if st.button("Guardar"):
            st.session_state.vote = {"actividad_id": id_}
            st.session_state["modal"] = None
            st.session_state["accion"] = opciones[0]
            st.rerun()


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

    
    

    

with subtab2:
    st.write("Estadistica Medica")
with subtab3:
    st.write("Estadistica Medica")    

