import fs from "fs";
import path from "path";
import PDFDocument from "pdfkit";

const projectPath = "./src"; // o "./backend" si deseas generar el PDF del backend

// 🔹 Obtener lista completa de archivos del proyecto (recursivo)
function obtenerArchivos(dir) {
  let lista = [];
  const archivos = fs.readdirSync(dir);

  for (const archivo of archivos) {
    const rutaCompleta = path.join(dir, archivo);
    const info = fs.statSync(rutaCompleta);

    if (info.isDirectory()) {
      lista = lista.concat(obtenerArchivos(rutaCompleta));
    } else if (/\.(js|jsx|ts|tsx|json|css|html)$/.test(archivo)) {
      lista.push(rutaCompleta);
    }
  }
  return lista;
}

// 🔹 Generar un PDF con una lista específica de archivos
function generarPDF(nombreArchivo, titulo, archivos) {
  const doc = new PDFDocument({ margin: 30, size: "A4" });
  doc.pipe(fs.createWriteStream(nombreArchivo));

  doc.fontSize(16).text(`📘 ${titulo}`, { align: "center" });
  doc.moveDown();

  archivos.forEach((rutaCompleta) => {
    doc.addPage();
    doc.fontSize(12).text(`Ruta: ${rutaCompleta}`, { underline: true });
    doc.moveDown();

    const contenido = fs.readFileSync(rutaCompleta, "utf8");
    doc.fontSize(8).text(contenido);
    doc.moveDown();
  });

  doc.end();
  console.log(`✅ PDF generado: ${nombreArchivo}`);
}

// 🔹 1. Obtener todos los archivos
const todosLosArchivos = obtenerArchivos(projectPath);

// 🔹 2. Dividir la lista en dos mitades
const mitad = Math.ceil(todosLosArchivos.length / 2);
const primeraMitad = todosLosArchivos.slice(0, mitad);
const segundaMitad = todosLosArchivos.slice(mitad);

// 🔹 3. Generar los dos PDF
generarPDF(
  "Proyecto_React_CodigoFrontend_Parte1.pdf",
  "Proyecto React - Código Fuente (Frontend - Parte 1)",
  primeraMitad
);

generarPDF(
  "Proyecto_React_CodigoFrontend_Parte2.pdf",
  "Proyecto React - Código Fuente (Frontend - Parte 2)",
  segundaMitad
);
