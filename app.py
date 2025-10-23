# app.py

# 🧱 Importamos las librerías necesarias para construir el microservicio
from flask import Flask, request, jsonify         # Para crear la API y manejar las solicitudes/respuestas
from flask_cors import CORS                       # Para permitir peticiones desde otros dominios (como APEX)
import openai                                     # Cliente oficial de OpenAI para conectarse con su API
import base64                                     # Para codificar archivos en base64 (necesario para enviar imágenes)
import os                                         # Para acceder a variables del sistema (como la API Key)
from pdf2image import convert_from_bytes          # Para convertir archivos PDF a imágenes
from io import BytesIO                            # Para manipular archivos en memoria como si fueran archivos reales
from PIL import Image                             # Librería para trabajar con imágenes (aunque aquí no editamos)
import re                                         # Para limpiar texto con expresiones regulares
import json                                       # Para convertir respuestas en formato JSON

# 🚀 Inicializamos la app Flask
app = Flask(__name__)
CORS(app)  # Habilitamos CORS para aceptar llamadas desde otros orígenes (como apex.oracle.com)

# 🔐 Cargamos la clave de la API de OpenAI desde una variable de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

# 📌 Ruta principal de la API
@app.route('/ocr-curp', methods=['POST'])
def ocr_curp():
    # Verificamos que se haya enviado un archivo
    if 'file' not in request.files:
        return jsonify({"error": "No se envió un archivo"}), 400

    file = request.files['file']
    content_type = file.content_type  # Obtenemos el tipo MIME (ej: image/jpeg o application/pdf)
    images_base64 = []  # Lista para guardar imágenes codificadas en base64

    try:
        if content_type == "application/pdf":
            # Si es PDF, convertimos la primera página a imagen JPEG
            pages = convert_from_bytes(file.read())  # Convierte a lista de páginas (imágenes)
            img_io = BytesIO()
            pages[0].save(img_io, format="JPEG")     # Guardamos la primera página en formato JPEG
            img_data = base64.b64encode(img_io.getvalue()).decode("utf-8")  # Convertimos a base64
            images_base64.append(img_data)
        else:
            # Si es imagen (JPG o PNG), simplemente la codificamos
            img_data = base64.b64encode(file.read()).decode("utf-8")
            images_base64.append(img_data)
    except Exception as e:
        # Error al procesar el archivo (formato no compatible, dañado, etc.)
        return jsonify({"error": f"Error procesando archivo: {str(e)}"}), 500

    # 🧠 Instrucción que se le enviará a OpenIA para extraer los datos del CURP
    content = [
        {
        "type": "text",
        "text": (
            "Este es un documento de datos personales. Extrae los campos y responde "
            "solo con un JSON plano, sin comillas triples ni texto adicional. El formato es:\n\n"
            "{\n"
            "  \"nombre\": \"\",\n"
            "  \"apellido_paterno\": \"\",\n"
            "  \"apellido_materno\": \"\",\n"
            "  \"fecha\": \"DD/MM/YYYY\",\n"
            "  \"calle_y_numero\": \"\",\n"
            "  \"colonia\": \"\",\n"
            "  \"ciudad_municipio\": \"\",\n"
            "  \"estado\": \"\",\n"
            "  \"codigo_postal\": \"\",\n"
            "  \"pais_nacimiento\": \"\",\n"
            "  \"nacionalidad\": \"\",\n"
            "  \"fecha_nacimiento\": \"DD/MM/YYYY\",\n"
            "  \"rfc\": \"\",\n"
            "  \"correo_electronico\": \"\",\n"
            "  \"telefono\": \"\",\n"
            "  \"ocupacion\": \"\",\n"
            "  \"origen_recursos\": \"\",\n"
            "  \"ha_desempenado_cargo_en_gobierno\": \"Sí\" o \"No\"\n"
            "}"
        )
        }
    ]

    # Agregamos cada imagen (convertida o enviada) como parte del mensaje
    for img in images_base64:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img}"
            }
        })

    try:
        # Llamamos a la API de OpenAI usando el modelo GPT-4o
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}],
            max_tokens=300
        )

        # Tomamos el texto generado por GPT y lo limpiamos
        raw_result = response.choices[0].message.content.strip()

        # Eliminamos posibles comillas triples ```json que podrían venir en la respuesta
        cleaned = re.sub(r"^```json|```$", "", raw_result.strip(), flags=re.MULTILINE).strip()

        # Convertimos el texto limpio a JSON (verifica que sea un formato válido)
        parsed = json.loads(cleaned)

        # Devolvemos el JSON como respuesta al cliente
        return jsonify(parsed)

    except json.JSONDecodeError as e:
        # Si el modelo devolvió un JSON mal formado, avisamos con el contenido original
        return jsonify({
            "error": "Respuesta JSON inválida",
            "detalle": str(e),
            "raw": raw_result
        }), 500
    except Exception as e:
        # Otro tipo de errores (fallo en la API, conexión, etc.)
        return jsonify({"error": str(e)}), 500

# 🖥️ Ejecutamos el servidor localmente solo si corremos el script directamente
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

