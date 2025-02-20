# AI PDF to PPT Generator with Slide Edit & PPT Download

This project is a Flask-based application that generates presentations from documents with the help of AI. It's a simple setup, and it does all the heavy lifting for you. You just provide the document, and the app creates a presentation based on the content. If you're looking to automate your slideshows, this could be a fun project for you to try out too!

![AI PDF to PPT Generator](https://miro.medium.com/v2/resize:fit:2000/format:webp/1*jwt_PvUh_NBvmRCn0U_dMg.png)

Want to try? Demo link is in the article  
[Transform PDFs into Professional Presentations with AI](https://medium.com/@lesteroliver911/transform-pdfs-into-professional-presentations-with-ai-key-insights-from-building-this-app-d8ff1535ecb0)

## Features

- Generate presentations from uploaded PDF documents.
- Customize the style of the presentation.
- Uses OpenAI's GPT-4o to help analyze documents and summarize content.
- Automatically creates an executive summary.
- All files are saved in a temporary folder for easy retrieval.

## Requirements

You'll need a few Python libraries to get this up and running. Here's a list of dependencies:

```bash
pip install -r requirements.txt
```

Also, make sure to set up your environment variables. You can add your OpenAI and Pexels API keys in a `.env` file like so:

```
OPENAI_API_KEY=your-openai-api-key
PEXELS_API_KEY=your-pexels-api-key
FLASK_SECRET_KEY=your-flask-secret-key
LLAMA_PARSE_API_KEY=your-llama-parse-api-key
```

## How to Run

1. Clone the repository or download the code.
2. Install the dependencies with `pip install -r requirements.txt`.
3. Add your API keys to the `.env` file as shown above.
4. Run the Flask app using the following command:

```bash
python main.py
```

5. Open your browser and go to `http://0.0.0.0:5000/`. You'll see a page where you can upload your document to generate a presentation.

## Structure

- `main.py`: The main Flask application.
- `utils/`: A folder with utilities for document processing, presentation generation, and more.
- `config.py`: Handles configuration like API keys and model settings.
- `templates/`: HTML templates for the frontend of the app.

## Notes

I'm still learning, so the code might not be perfect, but it's functional and gets the job done! Feel free to poke around, try it out, and even make improvements if you're up for it.

If you get stuck or have any questions, I used a lot of AI assistance to help me out, and it's a great way to figure things out if you're just starting.

## Have fun with it! 🎉
