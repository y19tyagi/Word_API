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

@app.route('/generate-document', methods=['POST'])
def generate_document():
    try:
        # Load JSON payload
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        # Unwrap if it's the OpenAI chat-completion structure
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict) and 'choices' in first:
                try:
                    content = first['choices'][0]['message']['content']
                    # If content is string of JSON, parse it
                    if isinstance(content, str):
                        content = json.loads(content)
                    data = content
                except Exception as unwrap_err:
                    app.logger.warning(f"Failed to unwrap chat completion payload: {unwrap_err}")
                    data = first
            else:
                # generic list: pick first element
                data = first

        # Determine which template to use; default to CV_Template_Placeholders.docx
        template_name = data.get('template_name', 'CV_Template_Placeholders.docx')

        # Security: basic sanitization to prevent path traversal
        if os.path.sep in template_name or not template_name.lower().endswith('.docx'):
            return jsonify({"error": "Invalid template name, must be a .docx file"}), 400

        # Resolve template path and check existence
        template_path = os.path.join(TEMPLATES_DIR, template_name)
        if not os.path.exists(template_path):
            return jsonify({"error": f"Template not found: {template_name}"}), 404

        # Prepare rendering context
        context = dict(data)
        persoons = context.pop('persoonlijkeGegevens', None)
        if isinstance(persoons, dict):
            context.update(persoons)

        # Load and render the DOCX template
        doc = DocxTemplate(template_path)

        # Handle base64 photo if provided
        if 'photo' in context and context['photo']:
            try:
                decoded = base64.b64decode(context['photo'])
                image_stream = io.BytesIO(decoded)
                context['photo'] = InlineImage(doc, image_stream, width=Cm(4))
            except Exception as img_err:
                app.logger.warning(f"Image decode error: {img_err}")
                context['photo'] = None

        # Render with context
        doc.render(context)

        # Save to a BytesIO buffer and send as a file response
        output_stream = io.BytesIO()
        doc.save(output_stream)
        output_stream.seek(0)

        return send_file(
            output_stream,
            as_attachment=True,
            download_name=f"{os.path.splitext(template_name)[0]}_filled.docx",
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        app.logger.error(f"Error generating document: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Sanity check: ensure the Templates directory exists
    if not os.path.isdir(TEMPLATES_DIR):
        raise RuntimeError(f"Templates folder not found at {TEMPLATES_DIR}")
    app.run(host='0.0.0.0', port=5000)
