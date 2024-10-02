from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
import os
import time
from typing import List, Dict
from utils.document_processing import load_and_analyze_document
from utils.retrieval import create_retriever, rrf_retriever
from utils.presentation import generate_presentation_content, customize_presentation_style, generate_executive_summary, create_presentation
from dotenv import load_dotenv
import uuid
import traceback
import logging
from config import FLASK_SECRET_KEY, LLM_MODEL_OPENAI
import io
import json
import threading

load_dotenv()

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Log environment variables (excluding sensitive information)
logger.info(f"FLASK_SECRET_KEY set: {bool(FLASK_SECRET_KEY)}")
logger.info(f"LLM_MODEL_OPENAI: {LLM_MODEL_OPENAI}")

# Create a temporary folder for storing presentations
TEMP_FOLDER = os.path.join(os.path.dirname(__file__), 'temp_presentations')
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Function to clean up old files
def cleanup_old_files():
    while True:
        current_time = time.time()
        for filename in os.listdir(TEMP_FOLDER):
            file_path = os.path.join(TEMP_FOLDER, filename)
            if os.path.isfile(file_path):
                file_age = current_time - os.path.getmtime(file_path)
                if file_age > 120:  # 60sec
                    os.remove(file_path)
                    logger.info(f"Deleted old file: {filename}")
        time.sleep(120)  # Check every 60 sec

# Start the cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        pdf_file = request.files.get('pdf_file')
        topic = request.form.get('topic')
        presenter = request.form.get('presenter')
        template = request.form.get('template')
        insert_images = 'insert_images' in request.form
        style = request.form.get('style')
        audience = request.form.get('audience')
        user_instructions = request.form.get('user_instructions')
        include_executive_summary = 'include_executive_summary' in request.form
        num_slides = int(request.form.get('num_slides', 10))

        if not pdf_file or not topic or not presenter:
            return jsonify({"error": "Please provide all required fields."}), 400

        try:
            logger.info(f"Processing request: topic={topic}, presenter={presenter}, template={template}")
            documents, analysis = load_and_analyze_document(pdf_file)
            logger.info("Document loaded and analyzed")

            # Check if documents were successfully created
            if not documents:
                return jsonify({"error": "Failed to process the PDF file. Please try again with a different file."}), 400

            retriever = create_retriever(documents)
            logger.info("Retriever created")
            instructions = f"Create a presentation about {topic}\n\nUser Instructions: {user_instructions}"
            retrieved_docs = rrf_retriever(instructions, retriever)
            logger.info("Documents retrieved")
            information = "\n".join([doc.page_content for doc in retrieved_docs])

            # Generate presentation content
            logger.info("Generating presentation content")
            slides = generate_presentation_content(topic, information, user_instructions, num_slides)
            slides = customize_presentation_style(slides, style, audience)

            if include_executive_summary:
                logger.info("Generating executive summary")
                executive_summary = generate_executive_summary(slides)
                slides['slides'].insert(1, executive_summary)

            # Generate a unique identifier for the presentation
            presentation_id = str(uuid.uuid4())

            # Save the presentation data
            presentation_data = {
                'slides': slides,
                'topic': topic,
                'presenter': presenter,
                'template': template,
                'insert_images': insert_images,
                'num_slides': num_slides
            }

            with open(os.path.join(TEMP_FOLDER, f"{presentation_id}.json"), 'w') as f:
                json.dump(presentation_data, f)

            logger.info(f"Presentation content generated successfully: id={presentation_id}")
            return jsonify({"message": "Presentation content generated successfully!", "id": presentation_id}), 200

        except Exception as e:
            logger.error(f"Error generating presentation content: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({"error": f"An error occurred while generating the presentation content: {str(e)}"}), 500

    return render_template('index.html')

@app.route('/edit/<presentation_id>')
def edit_presentation(presentation_id):
    file_path = os.path.join(TEMP_FOLDER, f"{presentation_id}.json")
    if not os.path.exists(file_path):
        logger.error(f"No presentation content available for editing: id={presentation_id}")
        flash("No presentation content available for editing.", "error")
        return redirect(url_for('index'))

    with open(file_path, 'r') as f:
        presentation_data = json.load(f)

    return render_template('edit_presentation.html', presentation_id=presentation_id, slides=presentation_data['slides']['slides'])

@app.route('/generate/<presentation_id>', methods=['POST'])
def generate_presentation(presentation_id):
    file_path = os.path.join(TEMP_FOLDER, f"{presentation_id}.json")
    if not os.path.exists(file_path):
        logger.error(f"No presentation content available for generation: id={presentation_id}")
        return jsonify({"error": "No presentation content available for generation."}), 404

    with open(file_path, 'r') as f:
        presentation_data = json.load(f)

    edited_slides = request.json.get('slides')

    if not edited_slides:
        return jsonify({"error": "No edited slides content provided."}), 400

    try:
        # Update the slides content with the edited version
        presentation_data['slides']['slides'] = edited_slides

        # Create the presentation
        logger.info("Creating presentation")
        pptx_io = create_presentation(
            presentation_data['slides'],
            presentation_data['template'],
            presentation_data['topic'],
            presentation_data['presenter'],
            presentation_data['insert_images'],
            presentation_data['num_slides']
        )

        # Store the presentation
        pptx_path = os.path.join(TEMP_FOLDER, f"{presentation_id}.pptx")
        with open(pptx_path, 'wb') as f:
            f.write(pptx_io.getvalue())

        logger.info(f"Presentation created successfully: id={presentation_id}")
        return jsonify({"message": "Presentation created successfully!", "id": presentation_id}), 200

    except Exception as e:
        logger.error(f"Error creating presentation: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"An error occurred while creating the presentation: {str(e)}"}), 500

@app.route('/download/<presentation_id>')
def download(presentation_id):
    file_path = os.path.join(TEMP_FOLDER, f"{presentation_id}.pptx")
    if not os.path.exists(file_path):
        logger.error(f"No presentation available for download: id={presentation_id}")
        flash("No presentation available for download.", "error")
        return redirect(url_for('index'))

    logger.info(f"Sending file for download: id={presentation_id}")
    return send_file(
        file_path,
        as_attachment=True,
        download_name="presentation.pptx",
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

if __name__ == "__main__":
    app.run(debug=False, port=5000)