from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Database setup (SQLite for simplicity)
#DO YOU SEE THIS?
def init_db():
    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS emails 
                 (id INTEGER PRIMARY KEY, sender TEXT, recipient TEXT, subject TEXT, date TEXT, body TEXT)''')
    conn.commit()
    conn.close()

# Route for the inbox
@app.route('/')
def inbox():
    conn = sqlite3.connect('emails.db')
    c = conn.cursor()
    c.execute("SELECT * FROM emails ORDER BY date DESC")
    emails = c.fetchall()
    conn.close()
    return render_template('home.html', emails=emails)

# Route for composing an email
@app.route('/compose', methods=['GET', 'POST'])
def compose():
    if request.method == 'POST':
        sender = request.form['sender']
        recipient = request.form['recipient']
        subject = request.form['subject']
        body = request.form['body']
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save to the database
        conn = sqlite3.connect('emails.db')
        c = conn.cursor()
        c.execute("INSERT INTO emails (sender, recipient, subject, date, body) VALUES (?, ?, ?, ?, ?)", 
                  (sender, recipient, subject, date, body))
        conn.commit()
        conn.close()
        
        return redirect(url_for('inbox'))
    
    return render_template('compose.html')

# Route for user login (simple demo)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        # For simplicity, assuming login is always successful
        return redirect(url_for('inbox'))
    return render_template('login.html')

if __name__ == '__main__':
    init_db()  # Initialize the database on app startup
    app.run(debug=True)
