import streamlit as st
import pandas as pd
import datetime
import time
import os
from nanoid import generate
from supabase import create_client
from numpy.random import default_rng as rng
from src.barcode_manager import BarcodePDFGenerator

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

@st.dialog("Imprimir barcode")
def imprimir_barcode(opciones, barcodes_file):
    st.pdf(barcodes_file)

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
    if not ok or not data:
        st.error(f"❌ Error al obtener actividades: {msg}")
        return
    # Diccionario nombre → id
    activity_dict = {a['nombre_actividad']: a['id_actividad'] for a in data}
    # Crear formulario
    with st.form("form_revisar_actividad"):
        selected_name = st.selectbox("Selecciona la actividad", list(activity_dict.keys()))
        student_id = st.text_input("Código del estudiante (escaneado o manual)")
        submit = st.form_submit_button("Guardar revisión")
        if submit:
            if not student_id.strip():
                st.warning("⚠️ Ingresa un código de estudiante válido.")
            else:
                st.session_state.revision = {
                    "id_actividad": activity_dict[selected_name],
                    "id_alumno": student_id.strip(),
                    "entregado": True,
                    "aciertos_obtenidos": 1,
                    "calificacion": 10,
                    "fecha": datetime.datetime.now().isoformat()
                }
                st.session_state["modal"] = None  # Si estás usando esto para controlar visibilidad
                st.session_state["accion"] = opciones[0]
                ok, msg, data = insertDataToBD('revision', st.session_state.revision)
                if ok:
                    st.success(msg)
                else:
                    st.warning(msg)

def getActivityData():
    tableName = 'actividad'
    try:
        query = supabase.table(tableName).select("id_actividad, nombre_actividad")
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

def renderDataframe():
    data = getGroupWork()

    if data:
        # Paso 1: Desanidar los datos
        flat_data = []
        for item in data:
            flat_data.append({
                "id_alumno": item["alumno"]["id_alumno"],
                "nombre_alumno": item["alumno"]["nombre_alumno"],
                "nombre_actividad": item["actividad"]["nombre_actividad"],
                "entregado": item["entregado"]
            })

        # Paso 2: Crear DataFrame
        df = pd.DataFrame(flat_data)

        # Paso 3: Pivotear el DataFrame (una fila por alumno, columnas por actividad)
        df_pivot = df.pivot_table(
            index=["id_alumno", "nombre_alumno"],
            columns="nombre_actividad",
            values="entregado",
            aggfunc="first"  # Si hay múltiples entregas, tomar la primera
        ).reset_index()

        # Paso 4: Limpiar y renombrar columnas
        df_pivot = df_pivot.fillna("").replace({True: "Entregado", False: ""})
        df_pivot = df_pivot.rename(columns={"id_alumno": "ID", "nombre_alumno": "Nombre"})

        # Paso 5: Mostrar en Streamlit
        edited_df = st.data_editor(df_pivot)

        # Paso 6: Ejemplo lógico: seleccionar el alumno con nombre más largo
        if not edited_df.empty:
            selected_id = edited_df.loc[edited_df["Nombre"].idxmax()]["ID"]
    else:
        st.error("No se pudo obtener la información.")

def getGroupWork():
    response = supabase.from_("revision").select("""
        id_revision,
        entregado,
        alumno (
            id_alumno,
            nombre_alumno
        ),
        actividad (
            id_actividad,
            nombre_actividad
        )
    """).execute()
    data = response.data
    return data

def layout():
    st.title("Control escolar")
    subtab1, subtab2, subtab3 = st.tabs(["Medicina 1A", "Medicina 1B", "Nutricion 4C"])
    with subtab1:
        opciones = ["-- Selecciona --", "Agregar alumn@", "Crear actividad", "Revisar actividad", "Imprimir codigos de barras"]
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
        elif st.session_state.get("modal") == "Imprimir codigos de barras":      
            barcodes_file = os.path.join(os.path.join(os.getcwd(), 'src', 'codigos_estadistica.pdf'))    
            if os.path.exists(barcodes_file):
                pass
            else:
                ok, msg, data = getDataFromTable('alumno')
                if not ok or not data:
                    st.error(f"❌ Error al obtener actividades: {msg}")
                    return
                # Diccionario nombre → id
                datos_alumnos = {a['id_alumno']: a['nombre_alumno'] for a in data}
                #datos_alumnos = { "ALU001": "Juan Pérez", "ALU002": "María López", "ALU003": "Carlos Sánchez"}
                genBarcode = BarcodePDFGenerator()
                genBarcode.ejecutar(datos_alumnos)
            imprimir_barcode(opciones, barcodes_file)
        renderDataframe()
    with subtab2:
        st.write("Estadistica Medica")
    with subtab3:
        st.write("Estadistica Medica")

layout()
