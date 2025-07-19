from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import base64
import os
import json  # para validar JSON antes de enviarlo

app = Flask(__name__)
CORS(app)

# Clave API
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/ocr-curp', methods=['POST'])
def ocr_curp():
    if 'file' not in request.files:
        return jsonify({"error": "No se envió un archivo"}), 400

    file = request.files['file']
    image_data = base64.b64encode(file.read()).decode("utf-8")

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Este es un CURP mexicano. Extrae los siguientes campos y responde "
                        "solo en JSON con este formato:\n"
                        "{\n"
                        "  \"nombre\": \"\",\n"
                        "  \"apellido_paterno\": \"\",\n"
                        "  \"apellido_materno\": \"\",\n"
                        "  \"fecha_nacimiento\": \"DD/MM/YYYY\",\n"
                        "  \"genero\": \"M\" o \"F\"\n"
                        "}"
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_data}"
                    }
                }
            ]
        }
    ]

    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=300
        )
        raw = response.choices[0].message.content.strip()

        # Eliminar comillas markdown (```)
        cleaned = raw.replace("```json", "").replace("```", "").strip()

        # Asegurar que es un JSON válido
        data = json.loads(cleaned)

        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

