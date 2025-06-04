from flask import Flask, request, send_file, jsonify
from docxtpl import DocxTemplate
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "API is live"}), 200

@app.route('/generate-cv', methods=['POST'])
def generate_cv():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        template_path = os.path.join(os.path.dirname(__file__), "CV_Template_Placeholders.docx")
        if not os.path.exists(template_path):
            return jsonify({"error": f"Template not found at {template_path}"}), 500

        doc = DocxTemplate(template_path)
        doc.render(data)

        output_path = "/tmp/Generated_CV.docx"
        doc.save(output_path)

        return send_file(output_path, as_attachment=True, download_name="Generated_CV.docx")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
