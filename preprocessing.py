import spacy
from spacy.lang.en.stop_words import STOP_WORDS
import string

# Load spaCy's English language model
nlp = spacy.load("en_core_web_sm")

# Define separation keyword
SEPARATOR_KEYWORD = "Caleb_Kairos_Michael_Nate_STOP_EMAIL"

# Simulating the downloaded email content
emails = [
    "From: 'Flood, Brid' <brigid.noelle.flood@emory.edu>\nSubject: CS Topics Courses, Fall 25\nDate: March 24, 2025\nDear CS Students,\n\nWith registration just around the corner, I am writing to you with an overview of the topics courses (CS 485) that we have on offer for Fall 25. These are the only undergraduate courses that require permission codes for the coming semester, and you can request codes during the appropriate timeslot (see my email from 14 March entitled 'PLEASE READ CAREFULLY: Permission Code Distribution Schedule and Registration Info, Fall 25 Pre-Registration').\n\nCS 485/1: Spatial Computing\n- Prerequisite: CS 253\n- Spatial data is ubiquitous in many applications, e.g., map applications, agriculture, health, and transportation, and in different scientific disciplines, e.g., geographic information sciences, environmental sciences, and behavioral sciences. This course covers the main concepts behind the existing technologies in spatial computing and explores future directions where spatial data is driving innovations. The course starts by introducing spatial computing and geometric algorithms to handle spatial data including points, lines, and polygons.\n\nBest,\nBrid Flood\nSr. Undergraduate Coordinator - Department of Computer Science\nEmory University\n",
    "From: 'Smith, John' <john.smith@emory.edu>\nSubject: Internship Opportunity for CS Majors\nDate: March 25, 2025\nDear CS Majors,\n\nWe are excited to announce a paid internship opportunity with TechCorp for the Summer 2025. TechCorp is looking for talented Computer Science students to join their team and work on cutting-edge software development projects. The internship will provide hands-on experience in machine learning, cloud computing, and software engineering.\n\nThe internship will run for 12 weeks, from June 1st to August 31st, 2025. Applicants should have experience in Python, Java, and machine learning frameworks. Interested candidates should submit their resumes to john.smith@techcorp.com by April 15, 2025.\n\nBest regards,\nJohn Smith\nRecruiter - TechCorp",
    "From: 'University CS Club' <csclub@emory.edu>\nSubject: Join Us for the CS Club Spring Event!\nDate: March 25, 2025\nDear CS Students,\n\nThe Computer Science Club is hosting its Spring 2025 networking event next Friday, April 2nd, 2025. We will have a panel discussion with industry professionals from top tech companies like Google and Microsoft. Afterward, there will be a casual networking session with pizza and drinks.\n\nThis is a great opportunity to learn more about the tech industry, connect with professionals, and hear about internship and full-time opportunities. We hope to see you there!\n\nEvent Details:\n- Date: April 2nd, 2025\n- Time: 6:00 PM to 9:00 PM\n- Location: CS Department Lounge, Room 101\n\nPlease RSVP via the link below:\n[RSVP Link]\n\nBest regards,\nCS Club President"
]

# Filepath to store the emails
email_file_path = "emails_with_separator.txt"

# Filepath to store the processed emails
processed_email_file_path = "processed_emails.txt"

# Function to download emails and add separator after each email
def download_emails_with_separator(emails, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        for email in emails:
            # Write the email content to the file
            file.write(email + "\n")
            # Write the stop keyword after each email
            file.write(SEPARATOR_KEYWORD + "\n")

# Download emails and save them to the file
download_emails_with_separator(emails, email_file_path)

# Reading and processing the file later
def process_downloaded_emails(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Split emails using the stop keyword separator
    emails = content.split(SEPARATOR_KEYWORD)
    
    # Process each email individually
    processed_emails = []
    for email in emails:
        if email.strip():  # Avoid empty segments
            processed_email = preprocess_email(email)
            processed_emails.append(processed_email)
    
    return processed_emails

# Preprocess function
def preprocess_email(email_text):
    # Convert emails to lower case
    email_text = email_text.lower()
    
    # Tokenize the email text
    doc = nlp(email_text)
    
    # Lemmatize, remove stopwords, and punctuation
    lemmatized_tokens = [token.lemma_ for token in doc if token.text not in STOP_WORDS and token.text not in string.punctuation]
    
    # Join the lemmatized tokens back into a string
    processed_text = " ".join(lemmatized_tokens)
    
    return processed_text

# Process the downloaded emails with separators
processed_emails = process_downloaded_emails(email_file_path)

# Save processed emails to a new file
with open(processed_email_file_path, 'w', encoding='utf-8') as file:
    for processed_email in processed_emails:
        file.write(processed_email + "\n" + SEPARATOR_KEYWORD + "\n")

# Output the processed emails
for i, email in enumerate(processed_emails, 1):
    print(f"Processed Email {i}:\n{email}\n")
