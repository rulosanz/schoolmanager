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
    # Leer el archivo como bytes
    with open(barcodes_file, "rb") as f:
        pdf_bytes = f.read()
    # Agregar botón para descargar
    st.download_button(
        label="📥 Descargar PDF",
        data=pdf_bytes,
        file_name="barcodes.pdf",
        mime="application/pdf"
    )

@st.dialog("Agregar alumn@")
def insertar_alumno(opciones, grupo_id):
    id_student = generate('0123456789abcdefghijklmnopqrstuvwxyz', 12)
    name_student = st.text_input("Nombre")
    phone_student = st.text_input("Teléfono")
    email_student = st.text_input("Email")
    if st.button("Guardar"):
        st.session_state.alumno = {
            "id_alumno": id_student,
            "id_grupo": grupo_id,
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
                f"✅ Alumno creado correctamente"
            )
        time.sleep(1)
        st.rerun()

@st.dialog("Crear actividad")
def agregar_actividad(opciones, grupo_id):
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
            "id_grupo": grupo_id,
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
        time.sleep(1)
        st.rerun()

@st.dialog("Revisar actividad")
def revisar_actividad(opciones, grupo_id):
    ok, msg, data = getDataFromTable('actividad', filters={"id_grupo": grupo_id})
    if not ok or not data:
        st.error(f"❌ Error al obtener actividades: {msg}")
        return

    activity_dict = {a['nombre_actividad']: a['id_actividad'] for a in data}

    # Inicializa la variable en session_state si no existe
    if "student_id_input" not in st.session_state:
        st.session_state.student_id_input = ""

    with st.form("form_revisar_actividad"):
        selected_name = st.selectbox("Selecciona la actividad", list(activity_dict.keys()))
        
        # Usamos st.session_state.student_id_input como valor y key para sincronizar
        student_id = st.text_input(
            "Código del estudiante (escaneado o manual)",
            value=st.session_state.student_id_input,
            key="student_id_input"
        )

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

                st.session_state["accion"] = opciones[0]
                ok, msg, data = insertDataToBD('revision', st.session_state.revision)

                if ok:
                    st.success(msg)
                    # Limpiar el input sin cerrar diálogo
                    st.session_state.student_id_input = ""
                    st.experimental_rerun()  # Para que la UI se refresque y el input se limpie
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

def renderDataframe(grupo_id):
    data = getGroupWork(grupo_id)  # Por ejemplo, id_grupo=1

    if data:
        flat_data = []

        for alumno in data:
            id_alumno = alumno["id_alumno"]
            nombre_alumno = alumno["nombre_alumno"]
            revisiones = alumno.get("revision", [])

            if revisiones:
                for rev in revisiones:
                    flat_data.append({
                        "id_alumno": id_alumno,
                        "nombre_alumno": nombre_alumno,
                        "nombre_actividad": rev["actividad"]["nombre_actividad"],
                        "entregado": rev["entregado"]
                    })
            else:
                # Alumno sin revisiones, agregar con actividad vacía y entregado vacío
                flat_data.append({
                    "id_alumno": id_alumno,
                    "nombre_alumno": nombre_alumno,
                    "nombre_actividad": "",
                    "entregado": ""
                })

        df = pd.DataFrame(flat_data)

        if "nombre_actividad" in df.columns and df["nombre_actividad"].eq("").all():
            # No hay actividades, mostrar lista simple
            df_simple = df[["id_alumno", "nombre_alumno"]].drop_duplicates()
            df_simple = df_simple.rename(columns={"id_alumno": "ID", "nombre_alumno": "Nombre"})
            edited_df = st.data_editor(df_simple)
        else:
            # Calculamos cuántas actividades revisadas tiene cada alumno
            # Filtramos sólo revisiones entregadas (o si quieres todas, quita esta condición)
            revisiones_por_alumno = df[df["entregado"] == True].groupby("id_alumno").size().reset_index(name="Actividades revisadas")

            # Pivotamos como antes
            df_pivot = df.pivot_table(
                index=["id_alumno", "nombre_alumno"],
                columns="nombre_actividad",
                values="entregado",
                aggfunc="first"
            ).reset_index()

            # Unimos el conteo al df_pivot
            df_pivot = df_pivot.merge(revisiones_por_alumno, on="id_alumno", how="left")

            # Rellenamos NaN en conteo con 0
            df_pivot["Actividades revisadas"] = df_pivot["Actividades revisadas"].fillna(0).astype(int)

            df_pivot = df_pivot.fillna("").replace({True: "Entregado", False: ""})

            # Reordenamos columnas para que "Actividades revisadas" quede justo después de "nombre_alumno"
            cols = df_pivot.columns.tolist()
            # Quitar y luego insertar en la posición deseada
            cols.remove("Actividades revisadas")
            idx_nombre = cols.index("nombre_alumno")
            cols.insert(idx_nombre + 1, "Actividades revisadas")
            df_pivot = df_pivot[cols]

            df_pivot = df_pivot.rename(columns={"id_alumno": "ID", "nombre_alumno": "Nombre"})

            edited_df = st.data_editor(df_pivot)

        if not edited_df.empty:
            selected_id = edited_df.loc[edited_df["Nombre"].idxmax()]["ID"]

    else:
        st.error("No se pudo obtener la información.")

def getGroupWork(id_grupo):
    response = supabase.from_("alumno").select("""
        id_alumno,
        nombre_alumno,
        revision (
            id_revision,
            entregado,
            actividad (
                id_actividad,
                nombre_actividad
            )
        )
    """).eq("id_grupo", id_grupo).execute()

    data = response.data
    return data

def sidebarCreateGroup():
    grupo = st.text_input("Grupo")
    carrera = st.text_input("Carrera")
    semestre = st.text_input("Semestre")
    if st.button("Guardar"):
        st.session_state.grupo = {
            "grupo": grupo,
            "carrera": carrera,
            "semestre": semestre,
        }
        if "grupo" in st.session_state:
            ok, msg, data = insertDataToBD('grupo', st.session_state.grupo)
            if ok:
                st.success(
                    f"✅ Grupo creado correctamente"
                )
            else:
                st.warning(msg)

def genBarcodePDF():
    ok, msg, data = getDataFromTable('alumno')
    if not ok or not data:
        st.error(f"❌ Error al obtener actividades: {msg}")
        return
    # Diccionario nombre → id
    datos_alumnos = {a['id_alumno']: a['nombre_alumno'] for a in data}
    genBarcode = BarcodePDFGenerator()
    pdf_bytes = genBarcode.ejecutar(datos_alumnos)
    return pdf_bytes

def layout():
    st.title("")
    st.sidebar.title("Opciones")
    with st.sidebar.expander("Crear grupo"):
        sidebarCreateGroup()
    if st.sidebar.button("Generar PDF"):
        pdf_bytes = genBarcodePDF()  # llama a ejecutar() y devuelve bytes
        if pdf_bytes:
            st.sidebar.download_button("Descargar PDF", data=pdf_bytes, file_name="codigos.pdf", mime="application/pdf")
    ok_group, msg_group, data_group = getDataFromTable('grupo')
    # Diccionario de nombre → id
    grupo_dict = {g['grupo']: g['id_grupo'] for g in data_group}
    # Lista de nombres visibles
    nombres_grupos = list(grupo_dict.keys())
    if len(nombres_grupos) == 0:
        st.warning('No hay datos, favor de crear un grupo')
    else:
        seleccionado = st.selectbox("Selecciona un grupo", nombres_grupos)
        # Obtener el id correspondiente
        id_grupo = str(grupo_dict.get(seleccionado, None))
        opcs_grupo = nombres_grupos
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
            insertar_alumno(opciones, id_grupo)
        elif st.session_state.get("modal") == "Crear actividad":
            agregar_actividad(opciones, id_grupo)
        elif st.session_state.get("modal") == "Revisar actividad":
            revisar_actividad(opciones, id_grupo)
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
                genBarcode = BarcodePDFGenerator()
                genBarcode.ejecutar(datos_alumnos)
            imprimir_barcode(opciones, barcodes_file)
        if id_grupo is not None:
            renderDataframe(int(id_grupo))
        else:
            st.warning('No hay datos')
        
if __name__ == "__main__":
    layout()
