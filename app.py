from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import base64
import os
import json

# Inicializar app Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para todas las rutas

# Cargar clave desde variable de entorno
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
                        "solo en JSON con este formato:\n\n"
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
        resultado = response.choices[0].message.content.strip()

        # Intenta limpiar el resultado en caso de que venga con triple backticks
        if resultado.startswith("```"):
            resultado = resultado.strip("`").strip("json").strip()

        # Intenta convertirlo a JSON real
        parsed_json = json.loads(resultado)
        return jsonify(parsed_json)

    except json.JSONDecodeError as je:
        return jsonify({"error": "La respuesta del modelo no es un JSON válido", "raw": resultado}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

