from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import base64
import os
from pdf2image import convert_from_bytes
from io import BytesIO
from PIL import Image
import re
import json

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
            pages = convert_from_bytes(file.read())
            img_io = BytesIO()
            pages[0].save(img_io, format="JPEG")
            img_data = base64.b64encode(img_io.getvalue()).decode("utf-8")
            images_base64.append(img_data)
        else:
            img_data = base64.b64encode(file.read()).decode("utf-8")
            images_base64.append(img_data)
    except Exception as e:
        return jsonify({"error": f"Error procesando archivo: {str(e)}"}), 500

    content = [
        {
            "type": "text",
            "text": (
                "Este es un CURP mexicano. Extrae los siguientes campos y responde "
                "solo con un JSON plano, sin comillas triples ni texto adicional. El formato es:\n\n"
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
        raw_result = response.choices[0].message.content.strip()

        # Limpieza de posibles comillas triples u otros envoltorios
        cleaned = re.sub(r"^```json|```$", "", raw_result.strip(), flags=re.MULTILINE).strip()

        parsed = json.loads(cleaned)  # Verifica que sea JSON válido
        return jsonify(parsed)

    except json.JSONDecodeError as e:
        return jsonify({
            "error": "Respuesta JSON inválida",
            "detalle": str(e),
            "raw": raw_result
        }), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
