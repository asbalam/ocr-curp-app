from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import base64
import os
from pdf2image import convert_from_bytes
from io import BytesIO
from PIL import Image

app = Flask(__name__)
CORS(app)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/ocr-curp', methods=['POST'])
def ocr_curp():
    if 'file' not in request.files:
        return jsonify({"error": "No se envió un archivo"}), 400

    file = request.files['file']
    content_type = file.content_type

    images_base64 = []

    try:
        if content_type == "application/pdf":
            # Convertir PDF a lista de imágenes (una por página)
            pages = convert_from_bytes(file.read())
            # Solo tomamos la primera página para OCR (opcionalmente, puedes recorrer todas)
            img_io = BytesIO()
            pages[0].save(img_io, format="JPEG")
            img_data = base64.b64encode(img_io.getvalue()).decode("utf-8")
            images_base64.append(img_data)
        else:
            # Imagen (JPG/PNG)
            img_data = base64.b64encode(file.read()).decode("utf-8")
            images_base64.append(img_data)
    except Exception as e:
        return jsonify({"error": f"Error procesando archivo: {str(e)}"}), 500

    # Construcción del mensaje
    content = [
        {
            "type": "text",
            "text": (
                "Este es un CURP mexicano. Extrae los siguientes campos y responde "
                "solo en JSON con este formato:\n\n"
                "{\n"
                "  \"nombre\": \"\",\n"
                "  \"apellido_paterno\": \"\",\n"
                "  \"apellido_materno\": \"\",\n"
                "  \"fecha_nacimiento\": \"DD/MM/YYYY\",\n"
                "  \"genero\": \"M\" o \"F\"\n"
                "}"
            )
        }
    ]

    for img in images_base64:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img}"
            }
        })

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": content}],
            max_tokens=300
        )
        resultado = response.choices[0].message.content.strip()
        return resultado, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
