import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# 📁 Ruta del proyecto Flask (misma carpeta que app.py)
PROJECT_PATH = "./"

# 🔹 Solo archivos Python
VALID_EXTENSIONS = (".py",)

# 🔹 Carpetas a ignorar
IGNORE_DIRS = {"maas-env"}


def obtener_archivos(directorio):
    """Recorre el directorio de forma recursiva y obtiene todos los archivos .py, ignorando carpetas especificadas."""
    archivos_validos = []
    for raiz, subdirs, archivos in os.walk(directorio):
        # Filtrar subdirectorios que queremos ignorar
        subdirs[:] = [d for d in subdirs if d not in IGNORE_DIRS]

        for archivo in archivos:
            if archivo.endswith(VALID_EXTENSIONS):
                archivos_validos.append(os.path.join(raiz, archivo))
    return archivos_validos


def escribir_pdf(nombre_pdf, titulo, archivos):
    """Genera un PDF con el contenido de los archivos Python."""
    pdf = canvas.Canvas(nombre_pdf, pagesize=A4)
    ancho, alto = A4

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawCentredString(ancho / 2, alto - 30, f"🐍 {titulo}")
    pdf.setFont("Helvetica", 10)
    pdf.drawString(30, alto - 50, f"Total de archivos: {len(archivos)}")

    for i, ruta in enumerate(archivos, 1):
        pdf.showPage()
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(30, alto - 40, f"Archivo {i}: {ruta}")
        pdf.setFont("Courier", 8)

        try:
            with open(ruta, "r", encoding="utf-8", errors="ignore") as f:
                contenido = f.readlines()
        except Exception as e:
            contenido = [f"⚠️ No se pudo leer el archivo: {e}"]

        y = alto - 60
        for linea in contenido:
            if y < 40:  # Salto de página si se acaba el espacio
                pdf.showPage()
                y = alto - 40
                pdf.setFont("Courier", 8)
            pdf.drawString(30, y, linea[:130])  # Cortar líneas largas
            y -= 10

    pdf.save()
    print(f"✅ PDF generado: {nombre_pdf}")


def main():
    archivos = obtener_archivos(PROJECT_PATH)
    mitad = (len(archivos) + 1) // 2
    primera_mitad = archivos[:mitad]
    segunda_mitad = archivos[mitad:]

    escribir_pdf("Proyecto_Flask_Backend_Parte1.pdf",
                 "Proyecto Flask - Código Python (Parte 1)", primera_mitad)
    escribir_pdf("Proyecto_Flask_Backend_Parte2.pdf",
                 "Proyecto Flask - Código Python (Parte 2)", segunda_mitad)


if __name__ == "__main__":
    main()
