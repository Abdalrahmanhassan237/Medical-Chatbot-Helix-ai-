import os
import json
from pathlib import Path
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)

# ── Configuration ──
API_KEY = os.environ.get("OPENROUTER_API_KEY") #
MODEL = "anthropic/claude-3-haiku"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# ── تحميل الملف الطبي ──
def load_medical_guidelines():
    path = Path("medical_guidelines.txt")
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return ""

GUIDELINES = load_medical_guidelines()

# The API Endpoint
@app.route('/triage', methods=['POST'])
def triage():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400

    patient_message = data['message']


    system_prompt = (
        "You are Helix Health AI, a strict medical triage assistant.\n"
        "### Medical Guidelines (Arabic)\n"
        f"{GUIDELINES}\n\n"
        "### Rules\n"
        "1. Analyze the patient's input and extract all mentioned symptoms.\n"
        "2. Assess urgency using the guidelines above: Low, Medium, High, or Critical.\n"
        "3. Respond ONLY with a valid JSON object. No markdown fences.\n"
        "4. The 'chat_response' field must be a short, empathetic message in Arabic.\n\n"
        "### Required JSON Schema\n"
        '{\n'
        '  "extracted_symptoms": ["symptom1"],\n'
        '  "urgency_level": "Low | Medium | High | Critical",\n'
        '  "recommended_specialty": "اسم التخصص الطبي باللغة العربية",\n'
        '  "chat_response": "ردك باللغة العربية"\n'
        '}'
    )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": patient_message}
        ]
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        raw_content = response.json()["choices"][0]["message"]["content"].strip()

        # تنظيف الـ JSON لو الموديل حط علامات Markdown
        if raw_content.startswith("```"):
            raw_content = raw_content.split("\n", 1)[-1]
            raw_content = raw_content.replace("```", "").strip()

        result = json.loads(raw_content)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ── نقطة فحص السيرفر ──
@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "Helix Health AI API is running perfectly! 🚀"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
