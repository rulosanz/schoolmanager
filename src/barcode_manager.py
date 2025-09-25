import os
import shutil
import barcode
from barcode.writer import ImageWriter
from reportlab.pdfgen import canvas

TABLOID = (792, 1224)  # 11x17 pulgadas en puntos


class BarcodePDFGenerator:
    def __init__(self):
        self.output_pdf = "src/codigos_estadistica.pdf"
        self.barcode_folder = "barcodes"
        self.canvas = None
        self.page_width, self.page_height = TABLOID

        self.cell_width = 113.4     # 4 cm en puntos
        self.cell_height = 56.7     # 2 cm en puntos

        self.margin_x = 36          # media pulgada ≈ 1.27 cm
        self.margin_y = 36

        self.cols = int((self.page_width - 2 * self.margin_x) // self.cell_width)
        self.rows = int((self.page_height - 2 * self.margin_y) // self.cell_height)

    def generar_codigos(self):
        os.makedirs(self.barcode_folder, exist_ok=True)
        for codigo in self.datos:
            path_sin_extension = os.path.join(self.barcode_folder, codigo)
            code128 = barcode.get('code128', codigo, writer=ImageWriter())
            code128.save(path_sin_extension)

    def crear_pdf(self):
        self.canvas = canvas.Canvas(self.output_pdf, pagesize=TABLOID)

        col = 0
        row = 0

        for index, (codigo, nombre) in enumerate(self.datos.items()):
            barcode_file = os.path.join(self.barcode_folder, f"{codigo}.png")

            if not os.path.exists(barcode_file):
                raise FileNotFoundError(f"No se encontró la imagen generada: {barcode_file}")

            # Posición (x, y) de la celda
            x = self.margin_x + col * self.cell_width
            y = self.page_height - self.margin_y - (row + 1) * self.cell_height

            # Dibujar imagen del código de barras
            self.canvas.drawImage(
                barcode_file,
                x,
                y + 10,  # subimos un poco la imagen
                width=self.cell_width - 10,
                height=self.cell_height - 20
            )

            # Texto personalizado
            texto = f"{nombre}"
            self.canvas.setFont("Helvetica", 6)

            # Medir el ancho del texto
            text_width = self.canvas.stringWidth(texto, "Helvetica", 6)

            # Calcular X para centrar el texto
            text_x = x + (self.cell_width - text_width) / 2

            # Dibujar texto debajo de la imagen
            self.canvas.drawString(text_x, y, texto)

            # Avanzar en la grilla
            col += 1
            if col >= self.cols:
                col = 0
                row += 1

            # Salto de página si se llena
            if row >= self.rows:
                self.canvas.showPage()
                row = 0
                col = 0
        self.canvas.save()
        print(f"✅ PDF generado: {self.output_pdf}")

    def limpiar_temporales(self):
        shutil.rmtree(self.barcode_folder)
        print("🧹 Archivos temporales eliminados.")

    def ejecutar(self, datos):
        #datos = datos_alumnos = {
        #    f"ALU{i:03d}": f"Estudiante {i}" for i in range(1, 121)
        #}
        self.datos = datos
        self.generar_codigos()
        self.crear_pdf()
        self.limpiar_temporales()
