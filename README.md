# SchoolManager

## Descripción
SchoolManager es una aplicación web desarrollada con Streamlit para la gestión escolar. Permite administrar grupos, alumnos y actividades, así como registrar revisiones y calificaciones. Utiliza Supabase como backend para el almacenamiento de datos y ofrece generación de códigos de barras y reportes en PDF.

## Características principales
- Gestión de grupos, alumnos y actividades.
- Registro y revisión de actividades por alumno.
- Calificación automática basada en aciertos.
- Generación de códigos de barras para alumnos.
- Exportación de reportes en PDF.
- Interfaz interactiva y fácil de usar con Streamlit.

## Requisitos
- Python 3.12+
- Streamlit
- pandas
- supabase
- nanoid
- python-barcode
- reportlab

Instala los requisitos con:
```bash
pip install -r requirements.txt
```

## Configuración
Debes configurar las credenciales de Supabase en los secretos de Streamlit:
```toml
[supabase]
url = "TU_SUPABASE_URL"
key = "TU_SUPABASE_KEY"
```

## Uso
Ejecuta la aplicación con:
```bash
streamlit run app.py
```

## Funcionalidades
- **Crear grupo:** Permite registrar nuevos grupos escolares.
- **Agregar alumn@:** Añade estudiantes a un grupo, generando un código único.
- **Crear actividad:** Registra actividades (exámenes, trabajos, etc.) asociadas a un grupo.
- **Revisar actividad:** Marca actividades como entregadas y registra revisiones.
- **Calificar actividad:** Asigna calificaciones automáticas según aciertos obtenidos.
- **Generar PDF:** Descarga un PDF con los códigos de barras de los alumnos.

## Estructura principal
- `app.py`: Código fuente principal de la aplicación.
- `requirements.txt`: Dependencias necesarias.

## Licencia
Este proyecto es de uso educativo y puede ser modificado libremente.
