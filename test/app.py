import os
import json
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    # Load the emails from the JSON file
    with open('emails_data/001.json', 'r', encoding='utf-8') as file:
        emails = json.load(file)
    return render_template('home.html', emails=emails)


@app.route('/email/<int:email_id>')
def email_details(email_id):
    # Load the emails from the JSON file
    with open('emails_data/001.json', 'r', encoding='utf-8') as file:
        emails = json.load(file)
    
    # Get the email details based on the email_id (index in the list)
    selected_email = emails[email_id]
    
    return render_template('home.html', emails=emails, selected_email=selected_email)


if __name__ == '__main__':
    app.run(debug=True)