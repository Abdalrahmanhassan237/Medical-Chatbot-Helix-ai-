import os
import json
from flask import Flask, request, jsonify
from openai import OpenAI

app = Flask(__name__)

# تهيئة الاتصال بـ AgentRouter باستخدام مكتبة OpenAI
try:
    client = OpenAI(
        base_url="https://agentrouter.org/v1",
        api_key=os.environ.get("sk-M5F1mfNt6999DO5d5ysAOmUquASAcOMTjVpYEuypI4X93uXc"),
    )
except Exception as e:
    print("Error initializing AgentRouter client. Please check your API key.")
    exit(1)

# قراءة الملف الطبي عند تشغيل السيرفر
try:
    with open("medical_guidelines.txt", "r", encoding="utf-8") as file:
        medical_guidelines = file.read()
    print("تم تحميل الملف الطبي بنجاح.")
except FileNotFoundError:
    print("تنبيه: ملف medical_guidelines.txt غير موجود. تأكد من وضعه في نفس المجلد.")
    medical_guidelines = "استخدم معلوماتك الطبية العامة."

@app.route('/triage', methods=['POST'])
def ai_triage():
    data = request.get_json()
    if not data or 'message' not in data:
        return jsonify({"error": "Message is required"}), 400

    patient_message = data['message']

    system_prompt = f"""
    أنت طبيب فرز ذكي لنظام Helix Health AI. التزم حصرياً بالمعلومات الطبية التالية لتقييم حالة المريض:

    {medical_guidelines}

    إذا لم تجد إجابة، قم بتصنيف الخطورة كـ "تحتاج استشارة طبيب".
    ردك يجب أن يكون بصيغة JSON فقط بدون أي نصوص إضافية، بهذا الشكل تماماً:
    {{
      "extracted_symptoms": ["عرض1", "عرض2"],
      "urgency_level": "مستوى الخطورة",
      "chat_response": "ردك الودود"
    }}
    """

    try:
        # إرسال الطلب عبر AgentRouter
        # يمكنك تغيير 'gpt-4o-mini' لأي موديل آخر تدعمه منصة AgentRouter
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": patient_message}
            ],
            response_format={"type": "json_object"}
        )

        # استخراج النتيجة وتنظيفها
        response_text = response.choices[0].message.content.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]

        result_json = json.loads(response_text)

        return jsonify(result_json)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    return "Helix Health AI Server is Running with AgentRouter! 🚀"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
