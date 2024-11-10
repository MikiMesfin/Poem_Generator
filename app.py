from flask import Flask, render_template, request, redirect, url_for, send_file
from dotenv import load_dotenv
import google.generativeai as genai
import os
from flask_sqlalchemy import SQLAlchemy
from models import db, Poem
from io import StringIO

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure Gemini with safety settings at the model level
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro', safety_settings=[
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
])

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///poems.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

# Create the database tables
with app.app_context():
    db.create_all()

def generate_poem(name, relationship):
    prompt = f"""
    Write a heartfelt, family-friendly poem about {relationship}s for someone named {name}. 
    The poem should celebrate the beauty of {relationship}, expressing warmth, love, and appreciation. 
    Keep it between 6-8 lines.
    """
    
    generation_config = {
        "temperature": 0.7,
        "max_output_tokens": 200,  # Increased to allow for longer poems
        "top_k": 40,
        "top_p": 0.8
    }
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        if response.text:
            return response.text.strip()
        return "I'm sorry, I couldn't generate a poem at this time. Please try again."
    except ValueError as e:
        if "finish_reason" in str(e) and "safety_ratings" in str(e):
            return "I apologize, but I cannot generate that poem as it may contain inappropriate content. Please try again with a different topic or wording."
        else:
            return f"An error occurred while generating the poem: {str(e)}"

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    name = request.form['name']
    relationship = request.form['relationship']
    
    poem_text = generate_poem(name, relationship)
    
    # Save the poem to the database
    new_poem = Poem(
        creator_name=name,
        recipient_relationship=relationship,
        poem_text=poem_text
    )
    db.session.add(new_poem)
    db.session.commit()
    
    return render_template('result.html', poem=poem_text, name=name)

@app.route('/my-poems')
def my_poems():
    poems = Poem.query.order_by(Poem.created_at.desc()).all()
    return render_template('my_poems.html', poems=poems)

@app.route('/download_poem')
def download_poem():
    poem_text = request.args.get('poem')
    creator = request.args.get('creator', 'Unknown')
    relationship = request.args.get('relationship', '')
    
    # Create the full poem text with metadata
    full_text = f"Poem for {relationship}\nBy {creator}\n\n{poem_text}"
    
    # Create a StringIO object to hold the text
    text_io = StringIO(full_text)
    
    # Return the file for download
    return send_file(
        text_io,
        mimetype='text/plain',
        as_attachment=True,
        download_name='poem.txt'
    )

if __name__ == '__main__':
    app.run(debug=True)
