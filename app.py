from flask import Flask, request, jsonify
import openai
import base64
import os

# Cargar clave desde variable de entorno
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

@app.route('/ocr-curp', methods=['POST'])
def ocr_curp():
    if 'file' not in request.files:
        return jsonify({"error": "No se envió un archivo"}), 400

    file = request.files['file']
    image_data = base64.b64encode(file.read()).decode("utf-8")

    # Instrucciones y formato esperados para la extracción
    prompt_text = (
        "Este es un CURP mexicano. Extrae los siguientes campos del documento y responde "
        "solo en JSON válido con este formato exacto:\n\n"
        "{\n"
        "  \"nombre\": \"\",\n"
        "  \"apellido_paterno\": \"\",\n"
        "  \"apellido_materno\": \"\",\n"
        "  \"fecha_nacimiento\": \"DD/MM/YYYY\",\n"
        "  \"genero\": \"M\" o \"F\"\n"
        "}\n\n"
        "No incluyas ningún comentario ni explicación adicional."
    )

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt_text},
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
        return resultado, 200, {'Content-Type': 'application/json'}
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

