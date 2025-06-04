from flask import Flask, request, send_file, jsonify
from docxtpl import DocxTemplate
import tempfile
import os

app = Flask(__name__)

# === Endpoint ===
@app.route('/generate-cv', methods=['POST'])
def generate_cv():
    try:
        # --- 1️⃣ Get the JSON payload ---
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received"}), 400

        if isinstance(data, list) and len(data) > 0:
            data = data[0]

        # --- 2️⃣ Load the DOCX template ---
        template_path = template_path = "CV_Template_Placeholders.docx"
        
        if not os.path.exists(template_path):
            return jsonify({"error": f"Template not found at {template_path}"}), 500

        doc = DocxTemplate(template_path)

        # --- 3️⃣ Render the data into the template ---
        doc.render(data)
        print("=== Final Data Passed to Template ===")
        print(data)

        # --- 4️⃣ Save the generated CV to Downloads ---
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        output_path = os.path.join(downloads_folder, "Generated_CV.docx")
        doc.save(output_path)

        # --- 5️⃣ Send the file as response ---
        return send_file(output_path, as_attachment=True, download_name='Generated_CV.docx')

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500


# === Run App ===
if __name__ == '__main__':
    app.run(debug=True)
