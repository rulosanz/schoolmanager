import streamlit as st
import pandas as pd
import datetime
import time
from nanoid import generate
from supabase import create_client
from numpy.random import default_rng as rng

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

@st.dialog("Agregar alumn@")
def insertar_alumno(opciones):
    id_student = generate('0123456789abcdefghijklmnopqrstuvwxyz', 12)
    name_student = st.text_input("Nombre")
    phone_student = st.text_input("Teléfono")
    email_student = st.text_input("Email")
    if st.button("Guardar"):
        st.session_state.alumno = {
            "id_alumno": id_student,
            "id_grupo": '1',
            "nombre_alumno": name_student,
            "email": email_student,
            "telefono": phone_student,
        }
        st.session_state["modal"] = None
        st.session_state["accion"] = opciones[0] 
        if "alumno" in st.session_state:
            #st.success(f"Alumno creado: {st.session_state.alumno}")
            ok, msg, data = insertDataToBD('alumno', st.session_state.alumno)
            st.success(
                f"✅ {msg}"
            )
        time.sleep(2)
        st.rerun()

@st.dialog("Crear actividad")
def agregar_actividad(opciones):
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
        st.session_state.actividad = {
            "id_grupo": '1',
            "tipo": activity_type,
            "nombre_actividad": name_activity, 
            "descripcion": description_activity, 
            "parcial": parcial,
            "aciertos_posibles": possible_hits, 
            "fecha_entrega": delivery_date.isoformat()
        }
        st.session_state["modal"] = None
        st.session_state["accion"] = opciones[0]
        if "actividad" in st.session_state:
            st.success(
                f"✅ Revisión guardada:\n\n"
                f"Actividad Revisada: {st.session_state.actividad}"
            )
            ok, msg, data = insertDataToBD('actividad', st.session_state.actividad)
            if ok:
                st.success(msg)
            else:
                st.warning(msg)
        #time.sleep(2)
        #st.rerun()

@st.dialog("Revisar actividad")
def revisar_actividad(opciones):
    ok, msg, data = getDataFromTable('actividad')
    st.success(data)
    select_activity = st.selectbox(
        "Actividad",
        ("A", "B", "C"),
    )
    student_id = st.text_input("Ingresa el código o escanéalo con el lector")
    activity_id = getActivityData(select_activity)
    if st.button("Guardar"):
        st.session_state.revision = {
            "id_actividad": select_activity,
            "id_alumno": student_id,
            "entregado": True,
            "aciertos_obtenidos": '',
            "calificacion": '',
            "fecha": datetime.datetime.now().isoformat()
        }
        st.session_state["modal"] = None
        st.session_state["accion"] = opciones[0]
        if "revision" in st.session_state:
            st.success(
                f"✅ Revisión guardada:\n\n"
                f"Actividad Revisada: {st.session_state.revision}"
            )
        #st.rerun()

def getActivityData(nameActivity):
    tableName = 'revision'
    try:
        query = supabase.table(tableName).select("*").eq('nombre_actividad', 'nameActivity')
        response = query.execute()
        if hasattr(response, "error") and response.error:
            return False, f"Error: {response.error.message}", None
        return True, "Consulta exitosa", response.data
    except Exception as e:
        return False, f"Excepción al consultar: {e}", None

def getDataFromTable(tableName, filters=None):
    try:
        query = supabase.table(tableName).select("*")
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        response = query.execute()
        if hasattr(response, "error") and response.error:
            return False, f"Error: {response.error.message}", None
        return True, "Consulta exitosa", response.data
    except Exception as e:
        return False, f"Excepción al consultar: {e}", None


def insertDataToBD(tableName, registro):
    if not registro:
        return False, "El registro está vacío", None
    try:
        response = supabase.table(tableName).insert(registro).execute()
        # Revisamos si hubo error
        if hasattr(response, "error") and response.error:
            return False, f"Error: {response.error.message}", None
        return True, "Registro insertado correctamente", response.data
    except Exception as e:
        return False, f"Excepción al insertar: {e}", None

def test_connection():
    try:
        # Pide la información de tu proyecto (no depende de tablas)
        response = supabase.auth.get_session()
        return True, "Conexión exitosa ✅ Supabase respondió correctamente"
    except Exception as e:
        return False, f"Error de conexión: {e}"

def renderDataframe(tableName):
    ok, msg, data = getDataFromTable(tableName)
    if ok and data:
        # Convertimos a DataFrame solo con columnas que quieres mostrar
        df = pd.DataFrame(data)[["id_alumno", "nombre_alumno"]]
        df.columns = ["ID", "Nombre"]  # Renombrar columnas
        # Mostrar data_editor
        edited_df = st.data_editor(df)
        # Ejemplo: seleccionar el alumno cuyo nombre es mayor alfabéticamente (solo como ejemplo lógico)
        if not edited_df.empty:
            selected_id = edited_df.loc[edited_df["Nombre"].idxmax()]["ID"]
    else:
        st.error(f"No se pudo obtener la información: {msg}")

def layout():
    st.title("Control escolar")
    subtab1, subtab2, subtab3 = st.tabs(["Medicina 1A", "Medicina 1B", "Nutricion 4C"])
    with subtab1:
        opciones = ["-- Selecciona --", "Agregar alumn@", "Crear actividad", "Revisar actividad"]
        # --- Selector principal ---
        opcion = st.selectbox(
            "¿Qué deseas hacer?",
            opciones,
            index=0,
            key="accion"
        )
        # Guardamos en session_state qué modal abrir
        if opcion != opciones[0]:
            st.session_state["modal"] = opcion
        # Abrimos el modal correspondiente
        if st.session_state.get("modal") == "Agregar alumn@":
            insertar_alumno(opciones)
        elif st.session_state.get("modal") == "Crear actividad":
            agregar_actividad(opciones)
        elif st.session_state.get("modal") == "Revisar actividad":
            revisar_actividad(opciones)
        renderDataframe('alumno')
    with subtab2:
        st.write("Estadistica Medica")
    with subtab3:
        st.write("Estadistica Medica")

layout()
