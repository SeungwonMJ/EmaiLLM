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
from datetime import datetime, timedelta
import spacy
from spacy.lang.en.stop_words import STOP_WORDS
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
import io

# Google Gemini imports
from google import genai
from google.genai import types

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.urandom(24)  # for session management

# Increase session lifetime and size limit
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Global variable to store emails (as a backup for session)
DATA_FILE = os.path.join('data', 'qtm_email.json')
_EMAILS_CACHE = []

@app.before_request
def make_session_permanent():
    session.permanent = True

def load_and_cache_emails():
    """Load emails and store them in both session and cache"""
    global _EMAILS_CACHE

    print("Attempting to load and cache emails...")

    # Try to get emails from cache first
    if _EMAILS_CACHE:
        print("Using cached emails")
        print(f"Cache contains {len(_EMAILS_CACHE)} emails.")
        return _EMAILS_CACHE

    print("Cache is empty. Attempting to load from JSON files...")
    # Load emails from common paths
    emails = None
    possible_paths = [
        os.path.join(os.path.dirname(__file__), '..', 'data', 'qtm_email.json'),
        # os.path.join(os.path.dirname(__file__), '..', 'data', 'emailGroup1.json'),
        os.path.join(os.path.dirname(__file__), 'data', 'qtm_email.json'),
        os.path.join(os.path.dirname(__file__), 'qtm_email.json'),
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'qtm_email.json')
    ]

    for path in possible_paths:
        print(f"Checking for emails at: {path}")
        if os.path.exists(path):
            print(f"File found at: {path}")
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    emails = json.load(f)
                print(f"Loaded emails successfully from {path}")
                break  # Stop after successfully loading from one file
            except json.JSONDecodeError:
                print(f"Error loading JSON from {path} - Invalid JSON format.")
                continue
        else:
            print(f"File not found at: {path}")

    # Fall back to sample emails if none found
    if not emails:
        print("No email data found from JSON files, using sample data.")
        emails = load_emails_from_json()
        print(f"Loaded {len(emails)} emails from sample data.")

    # Add tags field if not present
    for email in emails:
        if 'tags' not in email:
            email['tags'] = []

    # Store in cache
    _EMAILS_CACHE = emails
    print(f"Loaded and cached {len(emails)} emails.")
    if _EMAILS_CACHE:
        print(f"First email in cache: {_EMAILS_CACHE[0].get('subject', 'No Subject')}")
    else:
        print("Cache is empty after loading attempt.")
    return emails

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# ============ Model Configuration ============

def setup_gemini_client():
    """Configure and return the Gemini API client."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY is not set. Please set it in your .env file.")
        return None
    
    try:
        # genai.configure(api_key=api_key)
        # client = genai.GenerativeModel('gemini-2.0-flash')
        client = genai.Client(api_key=api_key)
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

def call_llm(client, content: str, instruction: str, model: str = "gemini-2.0-flash") -> str:
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
        print(f"Calling LLM with {len(content)} characters of content")
        response = client.models.generate_content(
        model=model,
        contents=[content], # here should the content of email be
        config=types.GenerateContentConfig(
            max_output_tokens=1024,
            temperature=0.1,
            system_instruction= instruction,
        )
        )
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'candidates') and response.candidates:
            return response.candidates[0].content.parts[0].text
        else:
            print("Unexpected response format:", response)
            return str(response)
    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        return f"Error: {str(e)}"

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
            os.path.join(os.path.dirname(__file__), 'data', 'qtm_email.json'),
            os.path.join(os.path.dirname(__file__), 'qtm_email.json')
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

def load_emails():
    global _EMAILS_CACHE
    try:
        with open(DATA_FILE, 'r') as f:
            _EMAILS_CACHE = json.load(f)
    except FileNotFoundError:
        print(f"Warning: {DATA_FILE} not found. Starting with empty email cache.")
        _EMAILS_CACHE = {}  # Initialize as empty dictionary
    except json.JSONDecodeError:
        print(f"Error: {DATA_FILE} is not valid JSON.  Starting with empty email cache.")
        _EMAILS_CACHE = {}

def save_emails():
    """Save the current email data to the JSON file, with new emails at the front."""
    try:
        # Create a temporary file
        temp_file_path = DATA_FILE + ".tmp"
        with open(temp_file_path, 'w', encoding='utf-8') as f:
            # Ensure the newest emails (from _EMAILS_CACHE) are written first
            json.dump(_EMAILS_CACHE, f, indent=4)

        # Rename the temporary file to the original file
        os.replace(temp_file_path, DATA_FILE)
        print(f"Successfully saved email data to {DATA_FILE} with new emails at the front.")

    except Exception as e:
        print(f"Error saving email data to {DATA_FILE}: {e}")
        # Consider more robust error handling

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
    
    instruction = """You are an AI assistant helping a user understand and manage their email. 
    Respond to their questions about the email content in a helpful, concise way."""
    
    try:
        return call_llm(client, content=prompt, instruction=instruction)
    except Exception as e:
        print(f"Error processing chat query: {str(e)}")
        return f"Sorry, I encountered an error while processing your query: {str(e)}"

# ============ Flask Routes ============

@app.route('/')
def home():
    """
    Render the home page with email list, optionally filtered by keyword.
    """
    emails = _EMAILS_CACHE
    keywords = session.get('keywords', [])
    selected_keyword = request.args.get('keyword', None)
    search_query = request.args.get('q', '')
    
    total_emails = len(emails)  # Calculate the total number of emails

    emails_by_keyword = {keyword: [] for keyword in keywords}
    untagged_count = 0
    for email in emails:
        if not email['tags']:
            untagged_count += 1
            emails_by_keyword['untagged'] = emails_by_keyword.get('untagged', []) + [email]
        else:
            for tag in email['tags']:
                if tag in emails_by_keyword:
                    emails_by_keyword[tag].append(email)

    filtered_emails = []
    if selected_keyword == 'untagged':
        filtered_emails = [email for email in emails if not email['tags']]
    elif selected_keyword:
        filtered_emails = [
            email for email in emails if selected_keyword in email['tags']
        ]
    elif search_query:
        terms = search_query.lower().split()
        for email in emails:
            subject = email.get('subject', '').lower()
            content = email.get('content', '').lower()
            sender = email.get('sender_name', '').lower()
            if any(term in subject or term in content or term in sender for term in terms):
                filtered_emails.append(email)
    else:
        filtered_emails = emails

    return render_template(
        'index.html',
        emails=filtered_emails,
        keywords=keywords,
        search_query=search_query,
        selected_keyword=selected_keyword,
        emails_by_keyword=emails_by_keyword,
        untagged_count=untagged_count,
        total_emails=total_emails,
        current_step=4,
    )

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
    print(f"Received classify request with data: {data}")
    
    if not data or 'email_id' not in data:
        return jsonify({'error': 'Invalid request. Email ID required.'}), 400
    
    # Convert email_id to integer since it comes as string from JSON
    try:
        email_id = int(data['email_id'])
    except ValueError:
        return jsonify({'error': 'Invalid email ID format.'}), 400
    
    # Get emails from cache instead of session
    emails = _EMAILS_CACHE
    print(f"Found {len(emails)} emails in cache")
    
    # Find the email by ID
    try:
        if email_id < 0 or email_id >= len(emails):
            return jsonify({'error': f'Email ID {email_id} out of range.'}), 404
        
        email = emails[email_id]
        print(f"Found email: {email.get('subject', 'No subject')}")
    except Exception as e:
        print(f"Error finding email: {str(e)}")
        return jsonify({'error': f'Email with ID {email_id} not found. Error: {str(e)}'}), 404
    
    # Get keywords
    keywords = session.get('keywords', [])
    print(f"Keywords from session: {keywords}")
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
    print(f"Classifying email with content length: {len(email_content)}")
    classification_result = classify_email(email_content, keywords, client)
    print(f"Classification result: {classification_result}")
    
    # Update the email's tags
    email['tags'] = classification_result.get('relevant_keywords', [])
    
    # Update cache
    _EMAILS_CACHE[email_id] = email
    
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

@app.route('/process-untagged')
def process_untagged():
    """Downloads untagged emails and then deletes them."""
    global _EMAILS_CACHE  # Declare _EMAILS_CACHE as global

    untagged_emails = [email for email in _EMAILS_CACHE if not email['tags']]

    if untagged_emails:
        # Prepare content for download
        file_content = ""
        for email in untagged_emails:
            file_content += f"Subject: {email.get('subject', 'No Subject')}\n"
            file_content += f"Sender: {email.get('sender_email', 'No Sender')}\n"
            file_content += f"Date: {email.get('date', 'No Date')}\n"
            file_content += f"Content:\n{email.get('content', 'No Content')}\n\n"

        mem = io.BytesIO()
        mem.write(file_content.encode('utf-8'))
        mem.seek(0)

        # Simulate deletion
        _EMAILS_CACHE = [email for email in _EMAILS_CACHE if email['tags']]

        return send_file(
            mem,
            mimetype='text/plain',
            as_attachment=True,
            download_name='untagged_emails.txt'
        )
    else:
        # If no untagged emails, just redirect back to inbox
        return redirect(url_for('home'))

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

@app.route('/create-email', methods=['POST'])
def create_email():
    """
    Handles the creation of a new email and adds it to the JSON file.
    """
    try:
        email_data = request.get_json()
        if not all(k in email_data for k in ('sender_name', 'sender_email', 'recipients', 'subject', 'content')):
            return jsonify({'error': 'Missing required fields'}), 400

        global _EMAILS_CACHE
        email_data['date'] = datetime.now().strftime('%b %d, %Y %H:%M:%S')
        email_data['tags'] = []
        _EMAILS_CACHE.insert(0, email_data)  # Insert at the beginning of the list

        save_emails() # Ensure save_emails writes a list to JSON
        return jsonify({'success': True}), 200
    except Exception as e:
        print(f"Error creating email: {e}")
        return jsonify({'error': str(e)}), 500

# ============ Main Application Entry ============

if __name__ == '__main__':
    # Load emails into cache on application startup
    load_and_cache_emails()
    
    # Default keywords if not set in environment
    if not os.getenv("USER_KEYWORDS"):
        default_keywords = "networking,internship,club events"
        os.environ["USER_KEYWORDS"] = default_keywords
        print(f"USER_KEYWORDS not set. Using default: {default_keywords}")
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 7747))
    
    # Start the Flask application
    app.run(host='0.0.0.0', port=port, debug=True)    
    
    
