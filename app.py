import streamlit as st
import pandas as pd
import datetime
import time
import os
import io
import barcode
from nanoid import generate
from supabase import create_client
from barcode.writer import ImageWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)
TABLOID = (792, 1224)  # 11x17 pulgadas en puntos
CELL_WIDTH = 180
CELL_HEIGHT = 120
MARGIN_X = 36
MARGIN_Y = 36
COLS = int((TABLOID[0] - 2 * MARGIN_X) // CELL_WIDTH)  # Será 4
ROWS = int((TABLOID[1] - 2 * MARGIN_Y) // CELL_HEIGHT)

@st.dialog("Agregar alumn@")
def insertar_alumno(opciones, grupo_id):
    id_student = st.text_input("Matrícula")
    name_student = st.text_input("Nombre")
    if st.button("Guardar"):
        st.session_state.alumno = {
            "id_alumno": id_student,
            "id_grupo": grupo_id,
            "nombre_alumno": name_student
        }
        st.session_state["modal"] = None
        st.session_state["accion"] = opciones[0] 
        if "alumno" in st.session_state:
            ok, msg, data = insertDataToBD('alumno', st.session_state.alumno)
            if ok:
                st.success(
                    f"✅ Alumno creado correctamente"
                )
            else:
                st.warning(msg)
        time.sleep(1)
        st.rerun()

@st.dialog("Agregar alumn@s masivo")
def insertar_alumnos_masivo(opciones, grupo_id):
    uploaded_files = st.file_uploader(
        "Sube uno o más archivos Excel", accept_multiple_files=True, type="xlsx"
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            xls = pd.ExcelFile(uploaded_file)

            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                key = f"{uploaded_file.name} - {sheet_name}"

                st.markdown(f"### 📄 Hoja: `{sheet_name}` del archivo `{uploaded_file.name}`")
                st.dataframe(df)

                boton_id = f"importar_{uploaded_file.name}_{sheet_name}"
                if st.button(f"📥 Importar hoja: {sheet_name}", key=boton_id):
                    total_filas = len(df)
                    if total_filas == 0:
                        st.warning(f"La hoja '{sheet_name}' está vacía.")
                        continue

                    alumnos_insertados = []

                    progress_text = f"Iniciando inserción de alumnos de '{sheet_name}' al grupo {grupo_id}..."
                    my_bar = st.progress(0, text=progress_text)

                    for i, fila in df.iterrows():
                        time.sleep(0.5)  # Simula procesamiento

                        nombre_alumno = fila["Nombre"] if "Nombre" in fila else "Desconocido"

                        # Aquí podrías insertar el alumno en la BD:
                        st.session_state.alumno = {
                            "id_alumno": fila['Matrícula'] if 'Matrícula' in fila else generate('0123456789abcdefghijklmnopqrstuvwxyz', 12),
                            "id_grupo": grupo_id,
                            "nombre_alumno": nombre_alumno
                        }
                        if "alumno" in st.session_state:
                            ok, msg, data = insertDataToBD('alumno', st.session_state.alumno)
                            if ok:
                                progress_text = f"Insertando alumno {nombre_alumno} al grupo {grupo_id}..."
                                progreso = int(((i + 1) / total_filas) * 100)
                                my_bar.progress(progreso, text=progress_text)
                            else:
                                progress_text = f"Error al insertar alumno {nombre_alumno} al grupo {grupo_id}..."
                                progreso = int(((i + 1) / total_filas) * 100)
                                my_bar.progress(progreso, text=progress_text)
                    my_bar.empty()
                    st.success(f"✅ Hoja '{sheet_name}' importada correctamente al grupo {grupo_id}.")

                    # Guardar en sesión (opcional, según uso posterior)
                    st.session_state["accion"] = opciones[0]
                    st.session_state["alumnos_masivos"] = alumnos_insertados
                    st.session_state["modal"] = None

                    # Esperar para mostrar mensaje final
                    time.sleep(1)
                    st.rerun()

@st.dialog("Crear actividad")
def agregar_actividad(opciones, grupo_id):
    activity_type = st.selectbox(
        "Tipo de actividad",
        ("Examen", "Trabajo con rubrica", "Actividad Libro", "Exposicion", "Trabajo en clase", "Otra"),
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
def revisar_actividad_original(opciones, grupo_id):
    ok, msg, data = getDataFromTable('actividad', filters={"id_grupo": grupo_id})
    if not ok or not data:
        st.error(f"❌ Error al obtener actividades: {msg}")
        return

    activity_dict = {a['nombre_actividad']: a['id_actividad'] for a in data}
    aciertos_posibles_dict = {a['id_actividad']: a['aciertos_posibles'] for a in data}

    # Inicializar estados si no existen
    if "student_id_input" not in st.session_state:
        st.session_state.student_id_input = ""
    if "reset_input" not in st.session_state:
        st.session_state.reset_input = False

    # Limpiar el input si fue solicitado anteriormente
    if st.session_state.reset_input:
        st.session_state.student_id_input = ""
        st.session_state.reset_input = False

    with st.form("form_revisar_actividad"):
        selected_name = st.selectbox("Selecciona la actividad", list(activity_dict.keys()))

        # El valor se toma de session_state pero respetando si se reinició
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
                aciertos_obtenidos = aciertos_posibles_dict[activity_dict[selected_name]]
                calif = 10  # Aquí puedes calcular la calificación real si lo deseas

                st.session_state.revision = {
                    "id_actividad": activity_dict[selected_name],
                    "id_alumno": student_id.strip(),
                    "entregado": True,
                    "aciertos_obtenidos": aciertos_obtenidos,
                    "calificacion": calif,
                    "fecha": datetime.datetime.now().isoformat()
                }

                st.session_state["accion"] = opciones[0]

                ok, msg, data = getDataFromTable('revision', filters={"id_alumno": student_id.strip()})
                ya_revisado = False

                if data:
                    for elemento in data:
                        if elemento['id_actividad'] == activity_dict[selected_name]:
                            ya_revisado = True
                            break

                if ya_revisado:
                    st.warning(f'Ya fue revisada la actividad {selected_name} para {student_id.strip()}')
                else:
                    ok, msg, data = insertDataToBD('revision', st.session_state.revision)
                    if ok:
                        # Solicitar que se limpie el input en el próximo render
                        st.success(f'Actividad {selected_name} revisada correctamente a {student_id.strip()}')
                        time.sleep(1)
                        st.session_state.reset_input = True
                        st.rerun()
                    else:
                        st.warning(msg)                    

@st.dialog("Revisar actividad")
def revisar_actividad(opciones, grupo_id):
    ok, msg, data = getDataFromTable('actividad', filters={"id_grupo": grupo_id})
    if not ok or not data:
        st.error(f"❌ Error al obtener actividades: {msg}")
        return

    activity_dict = {a['nombre_actividad']: a['id_actividad'] for a in data}
    aciertos_posibles_dict = {a['id_actividad']: a['aciertos_posibles'] for a in data}

    # Inicializar estados si no existen
    if "student_id_input" not in st.session_state:
        st.session_state.student_id_input = ""
    if "reset_input" not in st.session_state:
        st.session_state.reset_input = False

    # Limpiar el input si fue solicitado anteriormente
    if st.session_state.reset_input:
        st.session_state.student_id_input = ""
        st.session_state.reset_input = False

    with st.form("form_revisar_actividad"):
        selected_names = st.multiselect(
            "Selecciona la actividad",
            list(activity_dict.keys()),
            accept_new_options=True,
        )

        # El valor se toma de session_state pero respetando si se reinició
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
                st.session_state.revision = []
                ok, msg, data = getDataFromTable('revision', filters={"id_alumno": student_id.strip()})
                revisados = []
                tmp_dict = {
                        "id_actividad": '',
                        "id_alumno": student_id.strip(),
                        "entregado": True,
                        "aciertos_obtenidos": 0,
                        "calificacion": 10,
                        "fecha": datetime.datetime.now().isoformat()
                    }
                for name in selected_names:
                    aciertos_obtenidos = aciertos_posibles_dict[activity_dict[name]]
                    tmp_dict["id_actividad"] = activity_dict[name]
                    tmp_dict["aciertos_obtenidos"] = aciertos_obtenidos
                    if data:
                        for elemento in data:
                            if elemento['id_actividad'] == activity_dict[name]:
                                revisados.append(name)
                                break
                            else:
                                st.session_state.revision.append(tmp_dict.copy())
                    else:
                        st.session_state.revision.append(tmp_dict.copy())
                st.session_state["accion"] = opciones[0]
                if len(revisados) == len(selected_names) and len(revisados) > 0:
                    st.warning(f'Ya fue revisadas todas las actividades seleccionadas para {student_id.strip()}')
                elif len(revisados) > 0:
                    st.warning(f'Ya fue revisadas las actividades {", ".join(revisados)} para {student_id.strip()}')
                elif len(st.session_state.revision) > 0:
                    ok, msg, data = insertDataToBD('revision', st.session_state.revision)
                    if ok:
                        # Solicitar que se limpie el input en el próximo render
                        st.success(f'Actividades {", ".join([n for n in selected_names if n not in revisados])} revisadas correctamente a {student_id.strip()}')
                        time.sleep(1)
                        st.session_state.reset_input = True
                        st.rerun()
                    else:
                        st.warning(msg)
                                   
@st.dialog("Calificar actividad")
def calificar_actividad(opciones, grupo_id):
    ok, msg, data = getDataFromTable('actividad', filters={"id_grupo": grupo_id})
    if not ok or not data:
        st.error(f"❌ Error al obtener actividades: {msg}")
        return
    activity_dict = {a['nombre_actividad']: a['id_actividad'] for a in data}
    aciertos_posibles_dict = {a['id_actividad']: a['aciertos_posibles'] for a in data}
    # Inicializa la variable en session_state si no existe
    if "student_id_input" not in st.session_state:
        st.session_state.student_id_input = ""

    with st.form("form_revisar_actividad"):
        selected_name = st.selectbox("Selecciona la actividad", list(activity_dict.keys()))
        # Usamos st.session_state.student_id_input como valor y key para sincronizar
        aciertos_obtenidos = st.text_input('Aciertos Obtenidos')
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
                #calif = (aciertos_obtenidos / aciertos_posibles_dict[activity_dict[selected_name]]) * 10
                calif = 0
                st.session_state.revision = {
                    "id_actividad": activity_dict[selected_name],
                    "id_alumno": student_id.strip(),
                    "entregado": True,
                    "aciertos_obtenidos": aciertos_obtenidos,
                    "calificacion": calif,
                    "fecha": datetime.datetime.now().isoformat()
                }

                st.session_state["accion"] = opciones[0]
                ok, msg, data = getDataFromTable('revision', filters={"id_alumno": student_id, "id_actividad": activity_dict[selected_name]})
                ok_actividad, msg_actividad, data_actividad = getDataFromTable('actividad', filters={"id_actividad": activity_dict[selected_name]})
                if ok and data:
                    registro_actual = data[0]  
                    # Modificamos solo el campo calificacion
                    registro_actual['aciertos_obtenidos'] = aciertos_obtenidos  # nuevo valor que quieres poner
                    registro_actual['calificacion'] = (int(aciertos_obtenidos) / int(data_actividad[0]['aciertos_posibles'])) * 10
                    ok_update, msg_update, data_update = updateDataInBD("revision", registro_actual, "id_revision", registro_actual['id_revision'])
                    if ok_update:
                        st.success(data)
                        # Limpiar el input sin cerrar diálogo
                        st.session_state.student_id_input = ""
                        st.experimental_rerun()  # Para que la UI se refresque y el input se limpie
                    else:
                        st.warning(msg)
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
    
def updateDataInBD(tableName, registro, filtro_campo, filtro_valor):
    """
    Actualiza un registro en la tabla `tableName`.
    `registro` es el diccionario con los datos completos para actualizar.
    `filtro_campo` y `filtro_valor` se usan para filtrar qué fila actualizar.
    """
    if not registro:
        return False, "El registro está vacío", None
    try:
        response = (
            supabase
            .table(tableName)
            .update(registro)
            .eq(filtro_campo, filtro_valor)
            .execute()
        )
        if hasattr(response, "error") and response.error:
            return False, f"Error: {response.error.message}", None
        return True, "Registro actualizado correctamente", response.data
    except Exception as e:
        return False, f"Excepción al actualizar: {e}", None

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

def generar_codigos_en_memoria(datos):
    """Genera códigos de barras como imágenes en memoria y las devuelve como dict"""
    codigos_imagenes = {}
    for codigo in datos:
        barcode_obj = barcode.get('code128', codigo, writer=ImageWriter())
        buffer = io.BytesIO()
        barcode_obj.write(buffer)
        buffer.seek(0)
        codigos_imagenes[codigo] = buffer
    return codigos_imagenes

def crear_pdf_en_memoria(datos, codigos_imagenes):
    """Crea un PDF en memoria usando las imágenes recibidas"""
    buffer_pdf = io.BytesIO()
    c = canvas.Canvas(buffer_pdf, pagesize=TABLOID)
    col = 0
    row = 0

    for index, (codigo, nombre) in enumerate(datos.items()):
        barcode_image_buffer = codigos_imagenes[codigo]
        barcode_image = ImageReader(barcode_image_buffer)

        # Coordenadas base de la celda
        x = MARGIN_X + col * CELL_WIDTH
        y = TABLOID[1] - MARGIN_Y - (row + 1) * CELL_HEIGHT

        # 🔲 Dibujar el contorno (grid)
        c.setLineWidth(0.3)  # grosor del borde
        c.setStrokeColorRGB(0.8, 0.8, 0.8)  # gris claro
        c.rect(x, y, CELL_WIDTH, CELL_HEIGHT, stroke=1, fill=0)

        # 🖼️ Dibujar imagen centrada verticalmente (dejando poco espacio al texto)
        c.drawImage(
            barcode_image,
            x + 5,                # margen izquierdo
            y + 6,                # un poco más arriba para dejar espacio al texto
            width=CELL_WIDTH - 10,
            height=CELL_HEIGHT - 16
        )

        # 🏷️ Dibujar texto centrado horizontalmente
        texto = f"{nombre}"
        c.setFont("Helvetica", 6)
        text_width = c.stringWidth(texto, "Helvetica", 6)
        text_x = x + (CELL_WIDTH - text_width) / 2
        text_y = y + 3  # 🔽 más cerca de la imagen
        c.drawString(text_x, text_y, texto)

        # 📄 Control de columnas y filas
        col += 1
        if col >= COLS:
            col = 0
            row += 1
        if row >= ROWS:
            c.showPage()
            row = 0
            col = 0

    c.save()
    buffer_pdf.seek(0)
    return buffer_pdf.read()

def generar_pdf_codigos(datos):
    """Función principal que genera el PDF con códigos de barras"""
    codigos_imagenes = generar_codigos_en_memoria(datos)
    pdf_bytes = crear_pdf_en_memoria(datos, codigos_imagenes)
    return pdf_bytes

def genBarcodePDF():
    ok, msg, data = getDataFromTable('alumno')
    if not ok or not data:
        st.error(f"❌ Error al obtener actividades: {msg}")
        return
    # Diccionario nombre → id
    datos_alumnos = {a['id_alumno']: a['nombre_alumno'] for a in data}
    pdf_bytes = generar_pdf_codigos(datos_alumnos)
    return pdf_bytes

def importAlumnos():
    pass

def login(email, password):
    try:
        # Usar el método correcto para iniciar sesión
        user = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        return user
    except Exception as e:
        st.error(f"Error al iniciar sesión: {str(e)}")
        return None

def layout():
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
        opciones = ["-- Selecciona --", "Agregar alumn@", "Agregar alumn@s masivo", "Crear actividad", "Revisar actividad", "Calificar actividad"]
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
        elif st.session_state.get("modal") == "Agregar alumn@s masivo":
            insertar_alumnos_masivo(opciones, id_grupo)
        elif st.session_state.get("modal") == "Crear actividad":
            agregar_actividad(opciones, id_grupo)
        elif st.session_state.get("modal") == "Revisar actividad":
            revisar_actividad(opciones, id_grupo)
        elif st.session_state.get("modal") == "Calificar actividad":
            calificar_actividad(opciones, id_grupo)
        if id_grupo is not None:
            renderDataframe(int(id_grupo))
        else:
            st.warning('No hay datos')
        
def loginManager():
    # Inicializar variable en session_state para controlar si está logueado
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        email = st.text_input("Correo electrónico")
        password = st.text_input("Contraseña", type="password")

        if st.button("Iniciar sesión"):
            if email and password:
                user = login(email, password)
                if user:
                    st.success("Inicio de sesión exitoso")
                    st.session_state.logged_in = True
                    st.rerun()  # Forzar recarga para mostrar el layout
                else:
                    st.error("Credenciales incorrectas")
            else:
                st.error("Por favor, ingresa tu correo y contraseña")
    else:
        # Mostrar layout tras login
        pass

if __name__ == "__main__":
    st.title("School Manager")
    layout()
