from flask import Flask, request, send_file, jsonify
from docxtpl import DocxTemplate
import tempfile
import os

app = Flask(__name__)

@app.route('/generate-cv', methods=['POST'])
def generate_cv():
    try:
        # 1️⃣ Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        if isinstance(data, list) and len(data) > 0:
            data = data[0]  # Support for list-wrapped payloads

        # 2️⃣ Load template from current directory
        template_path = os.path.join(os.path.dirname(__file__), "CV_Template_Placeholders.docx")
        if not os.path.exists(template_path):
            return jsonify({"error": "Template file not found"}), 500

        doc = DocxTemplate(template_path)
        doc.render(data)

        # 3️⃣ Use a temporary file to save the output
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            temp_path = tmp.name
            doc.save(temp_path)

        # 4️⃣ Send file back to client
        return send_file(temp_path, as_attachment=True, download_name="Generated_CV.docx")

    except Exception as e:
        return jsonify({"error": str(e)}), 500
