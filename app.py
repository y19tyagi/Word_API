from flask import Flask, request, send_file, jsonify
from docxtpl import DocxTemplate, InlineImage
import os
import base64
from docx.shared import Cm
import io
import json

app = Flask(__name__)

# Directory where your .docx templates are stored (matches your GitHub folder name)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'Templates')  # note capital 'T'

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "API is live"}), 200

@app.route('/qtc', methods=['POST'])
def generate_qtc_report():
    """
    Takes the JSON from n8n 'Get Full Data' node,
    fills the QTC-Progress_Report Word Jinja template, and returns the generated DOCX.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Updated template name
        template_name = 'QTC-Progress_Report.docx'
        template_path = os.path.join(TEMPLATES_DIR, template_name)
        if not os.path.exists(template_path):
            return jsonify({"error": f"Template not found: {template_name}"}), 404

        # Load template
        doc = DocxTemplate(template_path)

        # Prepare context for Jinja rendering
        context = data.copy()

        # Handle Base64 chart image if present
        if 'chart' in context and context['chart']:
            try:
                decoded = base64.b64decode(context['chart'])
                image_stream = io.BytesIO(decoded)
                context['chart'] = InlineImage(doc, image_stream, width=Cm(12))
            except Exception as img_err:
                app.logger.warning(f"Chart image decode error: {img_err}")
                context['chart'] = None

        # Render the template with context
        doc.render(context)

        # Return generated document
        output_stream = io.BytesIO()
        doc.save(output_stream)
        output_stream.seek(0)

        return send_file(
            output_stream,
            as_attachment=True,
            download_name="Progress report - Summary 22_08.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        app.logger.error(f"Error generating QTC-Progress report: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/generate-document', methods=['POST'])
def generate_document():
    try:
        # Load and unwrap JSON payload
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Unwrap OpenAI chat-completion wrapper if present
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict) and 'choices' in first:
                try:
                    content = first['choices'][0]['message']['content']
                    if isinstance(content, str):
                        content = json.loads(content)
                    data = content
                except Exception as unwrap_err:
                    app.logger.warning(f"Failed to unwrap chat completion payload: {unwrap_err}")
                    data = first
            else:
                # Generic list: use first element
                data = first

        # Determine template name
        template_name = data.get('template_name', 'CV_Template_Placeholders.docx')
        if os.path.sep in template_name or not template_name.lower().endswith('.docx'):
            return jsonify({"error": "Invalid template name, must be a .docx file"}), 400

        # Check template exists
        template_path = os.path.join(TEMPLATES_DIR, template_name)
        if not os.path.exists(template_path):
            return jsonify({"error": f"Template not found: {template_name}"}), 404

        # Use full data dict as context; templates can access nested fields directly
        context = data

        # Load and render template
        doc = DocxTemplate(template_path)

        # Insert image if provided
        if 'photo' in context and context['photo']:
            try:
                decoded = base64.b64decode(context['photo'])
                image_stream = io.BytesIO(decoded)
                context['photo'] = InlineImage(doc, image_stream, width=Cm(4))
            except Exception as img_err:
                app.logger.warning(f"Image decode error: {img_err}")
                context['photo'] = None

        doc.render(context)

        # Return generated document
        output_stream = io.BytesIO()
        doc.save(output_stream)
        output_stream.seek(0)
        # Get a custom name (fallback to template if missing)
        person = data.get('persoonlijkeGegevens', {})
        naam = person.get('naamVoorletters', '').strip().replace(" ", "_") or "CV"
        vacature = data.get('vacature',{})
        meeting = vacature.get("functie_naam",'') or "Meeting"
        if template_name == "CV_Template_Placeholders.docx":
            custom_name = f"{naam}_Aim4.docx"
        else: 
            custom_name = f"{meeting}_Aim4.docx"
        return send_file(
            output_stream,
            as_attachment=True,
            download_name=f"{custom_name}",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        app.logger.error(f"Error generating document: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if not os.path.isdir(TEMPLATES_DIR):
        raise RuntimeError(f"Templates folder not found at {TEMPLATES_DIR}")
    app.run(host='0.0.0.0', port=5000)
