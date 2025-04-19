"""
EmaiLLM - AI-Powered Email Classification System
(CS 329 Project EmaiLLM: Bulk Cleanser)

This application provides a Flask-based web interface for email management
with on-demand AI classification based on user-defined keywords.
"""

import os
import sys
import json
import string
import re
from typing import List, Dict, Any
from datetime import datetime

import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

# Google Gemini imports
from google import genai
from google.genai import types

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)  # for session management

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ============ Model Configuration ============

def setup_gemini_client():
    """Configure and return the Gemini API client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set. Please set it in your .env file.")
        return None
    
    try:
        genai.configure(api_key=api_key)
        client = genai.GenerativeModel('gemini-pro')
        return client
    except Exception as e:
        print(f"Failed to configure Gemini API: {str(e)}")
        return None

# ============ Text Processing Functions ============

# Load spaCy's English language model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def preprocess_email(email_text: str) -> str:
    """
    Preprocess email text by tokenizing, lemmatizing, and removing stopwords.
    
    Args:
        email_text: The raw email text
        
    Returns:
        Preprocessed email text
    """
    # Convert emails to lower case
    email_text = email_text.lower()
    
    # Tokenize the email text
    doc = nlp(email_text)
    
    # Lemmatize, remove stopwords, and punctuation
    lemmatized_tokens = [token.lemma_ for token in doc if token.text not in STOP_WORDS and token.text not in string.punctuation]
    
    # Join the lemmatized tokens back into a string
    processed_text = " ".join(lemmatized_tokens)
    
    return processed_text

def keyword_preprocessing(keywords: str) -> List[str]:
    """
    Preprocess the user-defined keywords into a list.
    
    Args:
        keywords: Comma-separated string of keywords
        
    Returns:
        List of cleaned keywords
    """
    return [keyword.strip() for keyword in keywords.lower().split(",")]

def retrieve_user_keywords() -> List[str]:
    """
    Retrieve user-defined keywords from the environment variable.
    
    Returns:
        List of user keywords
    """
    # Only use the environment variable value, not a default fallback
    keywords = os.getenv("USER_KEYWORDS", "")
    return keyword_preprocessing(keywords)

# ============ Email Classification Functions ============

def call_llm(client, content: str, instruction: str, model: str = "gemini-pro") -> str:
    """
    Call the language model to generate a response based on the content and instruction.
    
    Args:
        client: The generative AI client
        content: The email content to be classified
        instruction: The system instruction for the model
        model: The model to use for generation
        
    Returns:
        The model's response text
    """
    try:
        response = client.generate_content(
            contents=[content],  # Email content goes here
            generation_config=types.GenerationConfig(
                max_output_tokens=1024,
                temperature=0.1,
            ),
            system_instruction=instruction
        )
        return response.text
    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return ""

def classify_email(email_content: str, keywords: List[str], client) -> Dict[str, Any]:
    """
    Classify an email based on its content and user-defined keywords.
    
    Args:
        email_content: The preprocessed email content
        keywords: List of user-defined keywords
        client: The generative AI client
        
    Returns:
        Classification result dictionary
    """
    KEYWORDS = ", ".join(keywords)

    PROMPT_CLASSIFICATION = f"""
    You are an email classification assistant. Your task is to analyze the content of emails and identify which of the following keywords are relevant to the email:

    [{KEYWORDS}] 
    
    Instructions:
    1. Analyze the full email content provided
    2. Identify any keywords from the list that are relevant to the email
    3. Return ONLY the relevant keywords
    4. If no keywords match, return "NONE"

    Return your classification in this format:
    KEYWORDS: <relevant keywords (separated by commas) or NONE>
    
    Example:
    
    Email Content:
    "Join us for a networking event this Friday! Meet industry professionals and explore internship opportunities."
    
    Output:
    KEYWORDS: networking, internship
    

    Do not include any additional explanation or analysis in your response.
    """
    response = call_llm(client, content=email_content, instruction=PROMPT_CLASSIFICATION)
    
    # Parse the result
    try:
        keywords_line = next((line for line in response.strip().split('\n') if line.startswith('KEYWORDS:')), '')
        found_keywords = keywords_line.replace('KEYWORDS:', '').strip()
        
        if found_keywords.upper() == 'NONE':
            return {
                'relevant_keywords': [],
                'raw_result': response
            }
        else:
            return {
                'relevant_keywords': [kw.strip().lower() for kw in found_keywords.split(',')],
                'raw_result': response
            }
    except Exception as e:
        print(f"Error parsing classification result: {str(e)}")
        return {
            'relevant_keywords': [],
            'raw_result': response,
            'error': str(e)
        }

# ============ Email Loading Functions ============

def load_emails_from_json(filepath: str = None) -> List[Dict[str, Any]]:
    """
    Load emails from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        List of email dictionaries
    """
    # If no filepath is provided, use a hard-coded sample
    if not filepath:
        # Try common locations
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'data', 'qtm_emails.json'),
            os.path.join(os.path.dirname(__file__), 'qtm_emails.json')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                filepath = path
                break
    
    # If we still don't have a valid filepath, return sample data
    if not filepath or not os.path.exists(filepath):
        return [
            {
                "sender_name": "Hannans, Sadie Marie",
                "sender_email": "sadie.marie.hannans@EMORY.EDU",
                "subject": "More Announcements to consider - time sensitive",
                "date": "March 28, 2025 06:12:21 PM GMT",
                "recipients": "QSSMAJORS@LISTSERV.CC.EMORY.EDU",
                "reply_to": "sadie.marie.hannans@EMORY.EDU",
                "content": "On behalf of Emory's Women in STEM organization, You are invited to their annual Networking Night.",
                "tags": []
            },
            {
                "sender_name": "Hannans, Sadie Marie",
                "sender_email": "sadie.marie.hannans@EMORY.EDU",
                "subject": "APPLICATION DEADLINE EXTENDED",
                "date": "March 27, 2025 06:29:15 PM GMT",
                "recipients": "QSSMAJORS@LISTSERV.CC.EMORY.EDU",
                "reply_to": "sadie.marie.hannans@EMORY.EDU",
                "content": "APPLICATION DEADLINE EXTENDED - MARCH 31ST IT IS NOT TOO LATE TO JOIN!!!\n \nLEARN MORE ABOUT...",
                "tags": []
            }
        ]
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            emails = json.load(f)
            
        # Add tags field if not present
        for email in emails:
            if 'tags' not in email:
                email['tags'] = []
                
        return emails
    except Exception as e:
        print(f"Error loading emails from JSON: {str(e)}")
        return []

# ============ Chat Processing ============

def process_chat_query(query: str, email_data: Dict[str, Any]) -> str:
    """
    Process a chat query about an email.
    
    Args:
        query: User's chat query
        email_data: The email data
        
    Returns:
        AI response
    """
    client = setup_gemini_client()
    if not client:
        return "Sorry, I can't process your query right now. The AI service is unavailable."
    
    prompt = f"""
    You are an AI assistant helping with email management. 
    
    Here is information about an email:
    
    Sender: {email_data.get('sender_name', '')} <{email_data.get('sender_email', '')}>
    Subject: {email_data.get('subject', '')}
    Date: {email_data.get('date', '')}
    Content: {email_data.get('content', '')}
    
    User's question: {query}
    
    Please provide a helpful response to the user's question about this email.
    Keep your response concise and relevant to the question.
    """
    
    try:
        response = client.generate_content(
            contents=[prompt],
            generation_config=types.GenerationConfig(
                max_output_tokens=1024,
                temperature=0.2,
            )
        )
        return response.text
    except Exception as e:
        print(f"Error processing chat query: {str(e)}")
        return f"Sorry, I encountered an error while processing your query: {str(e)}"

# ============ Flask Routes ============

@app.route('/')
def home():
    """
    Render the home page with email list.
    """
    # Load emails
    emails = load_emails_from_json()
    
    # Get user keywords
    keywords = retrieve_user_keywords()
    
    # Store emails in session
    session['emails'] = emails
    session['keywords'] = keywords
    
    # Get search query if any
    search_query = request.args.get('q', '')
    
    # Filter emails if search query provided
    if search_query:
        filtered_emails = []
        terms = search_query.lower().split()
        for email in emails:
            subject = email.get('subject', '').lower()
            content = email.get('content', '').lower()
            sender = email.get('sender_name', '').lower()
            
            if any(term in subject or term in content or term in sender for term in terms):
                filtered_emails.append(email)
        emails = filtered_emails
    
    return render_template('index.html', 
                          emails=emails, 
                          keywords=keywords,
                          search_query=search_query,
                          current_step=1)

@app.route('/process-emails', methods=['POST'])
def process_emails():
    """
    Process and analyze emails for keywords (step 2).
    """
    emails = session.get('emails', [])
    keywords = session.get('keywords', [])
    
    # In a real app, this would trigger the actual processing
    # For demo, we just pass to the next step
    
    return render_template('index.html', 
                          emails=emails, 
                          keywords=keywords,
                          current_step=2)

@app.route('/tag-emails', methods=['POST'])
def tag_emails():
    """
    Tag emails with identified keywords (step 3).
    """
    emails = session.get('emails', [])
    keywords = session.get('keywords', [])
    
    # In a production app, this would retrieve processing results
    # For demo, we'll simulate by randomly assigning tags
    
    import random
    for email in emails:
        # Randomly assign 0-2 tags from keywords
        email['tags'] = random.sample(keywords, random.randint(0, min(2, len(keywords)))) if keywords else []
    
    # Update session
    session['emails'] = emails
    
    return render_template('index.html', 
                          emails=emails, 
                          keywords=keywords, 
                          current_step=3)

@app.route('/final-result', methods=['POST'])
def final_result():
    """
    Show final result with emails organized by keywords (step 4).
    """
    emails = session.get('emails', [])
    keywords = session.get('keywords', [])
    
    # Organize emails by keyword for the UI
    emails_by_keyword = {keyword: [] for keyword in keywords}
    emails_by_keyword['untagged'] = []
    
    for email in emails:
        if not email['tags']:
            emails_by_keyword['untagged'].append(email)
        else:
            for tag in email['tags']:
                if tag in emails_by_keyword:
                    emails_by_keyword[tag].append(email)
    
    return render_template('index.html', 
                          emails=emails, 
                          keywords=keywords,
                          emails_by_keyword=emails_by_keyword,
                          current_step=4)

@app.route('/classify-email', methods=['POST'])
def classify_single_email():
    """
    API endpoint to classify a single email on demand.
    """
    data = request.get_json()
    
    if not data or 'email_id' not in data:
        return jsonify({'error': 'Invalid request. Email ID required.'}), 400
    
    email_id = data['email_id']
    emails = session.get('emails', [])
    
    # Find the email by ID
    email = next((e for i, e in enumerate(emails) if i == email_id), None)
    if not email:
        return jsonify({'error': f'Email with ID {email_id} not found.'}), 404
    
    # Get keywords
    keywords = session.get('keywords', [])
    if not keywords:
        return jsonify({'error': 'No keywords defined.'}), 400
    
    # Initialize Gemini client
    client = setup_gemini_client()
    if not client:
        return jsonify({
            'status': 'error',
            'message': 'AI service is currently unavailable.'
        }), 500
    
    # Classify the email
    email_content = email.get('content', '')
    classification_result = classify_email(email_content, keywords, client)
    
    # Update the email's tags
    email['tags'] = classification_result.get('relevant_keywords', [])
    
    # Update session
    emails[email_id] = email
    session['emails'] = emails
    
    return jsonify({
        'status': 'success',
        'email_id': email_id,
        'tags': email['tags']
    })

@app.route('/chat', methods=['POST'])
def chat():
    """
    API endpoint for the chat interface.
    """
    data = request.get_json()
    
    if not data or 'query' not in data or 'email_id' not in data:
        return jsonify({'error': 'Invalid request. Query and email ID required.'}), 400
    
    query = data['query']
    email_id = data['email_id']
    emails = session.get('emails', [])
    
    # Find the email by ID
    email = next((e for i, e in enumerate(emails) if i == email_id), None)
    if not email:
        return jsonify({'error': f'Email with ID {email_id} not found.'}), 404
    
    # Process the chat query
    response = process_chat_query(query, email)
    
    return jsonify({
        'status': 'success',
        'response': response
    })

@app.route('/search', methods=['GET'])
def search():
    """
    Search emails by keyword.
    """
    query = request.args.get('q', '')
    return redirect(url_for('home', q=query))

@app.route('/reset', methods=['GET'])
def reset():
    """
    Reset the application state.
    """
    session.clear()
    return redirect(url_for('home'))

@app.route('/add-category', methods=['POST'])
def add_category():
    """Add a new category keyword to the .env file"""
    try:
        data = request.json
        category = data.get('category', '').strip().lower()
        
        if not category:
            return jsonify({'status': 'error', 'message': 'Empty category name'})
        
        # Get current keywords
        current_keywords = retrieve_user_keywords()
        
        # Check if keyword already exists
        if category in current_keywords:
            return jsonify({'status': 'error', 'message': 'Category already exists'})
        
        # Add the new keyword
        current_keywords.append(category)
        
        # Update the .env file
        update_env_file("USER_KEYWORDS", ",".join(current_keywords))
        
        # Update session with new keywords
        session['keywords'] = current_keywords
        
        return jsonify({
            'status': 'success', 
            'message': 'Category added successfully',
            'keywords': current_keywords
        })
    except Exception as e:
        print(f"Error adding category: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/delete-category', methods=['POST'])
def delete_category():
    """Delete a category keyword from the .env file"""
    try:
        data = request.json
        category = data.get('category', '').strip().lower()
        
        if not category:
            return jsonify({'status': 'error', 'message': 'Empty category name'})
        
        # Get current keywords directly from the .env file (not cache)
        # Force reload from .env by reloading dotenv
        load_dotenv(override=True)
        current_keywords = retrieve_user_keywords()
        
        # Check if keyword exists
        if category not in current_keywords:
            return jsonify({'status': 'error', 'message': 'Category does not exist'})
        
        # Remove the keyword
        current_keywords.remove(category)
        
        # Update the .env file
        update_env_file("USER_KEYWORDS", ",".join(current_keywords))
        
        # Update session with new keywords
        session['keywords'] = current_keywords
        
        # Also reload os.environ with the new value to ensure it's available
        os.environ["USER_KEYWORDS"] = ",".join(current_keywords)
        
        return jsonify({
            'status': 'success', 
            'message': 'Category removed successfully',
            'keywords': current_keywords
        })
    except Exception as e:
        print(f"Error removing category: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)})

def update_env_file(key, value):
    """Update a specific key in the .env file"""
    env_path = '.env'
    
    # Read the current .env file
    try:
        with open(env_path, 'r') as file:
            lines = file.readlines()
        
        # Find and update the key
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                updated = True
                break
        
        # If key doesn't exist, add it
        if not updated:
            lines.append(f"{key}={value}\n")
        
        # Write back to the .env file
        with open(env_path, 'w') as file:
            file.writelines(lines)
            
        # Also update the environment variable in the current process
        os.environ[key] = value
        
        # Force reload dotenv to ensure changes are reflected
        load_dotenv(override=True)
        
        print(f"Updated {key} in .env to: {value}")
    except Exception as e:
        print(f"Error updating .env file: {str(e)}")
        raise

# ============ Main Application Entry ============

if __name__ == '__main__':
    # Default keywords if not set in environment
    if not os.getenv("USER_KEYWORDS"):
        default_keywords = "networking,internship,club events"
        os.environ["USER_KEYWORDS"] = default_keywords
        print(f"USER_KEYWORDS not set. Using default: {default_keywords}")
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 7747))
    
    # Start the Flask application
    app.run(host='0.0.0.0', port=port, debug=True)