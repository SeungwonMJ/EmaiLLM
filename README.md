# EmaiLLM
CS 329 Project EmaiLLM: Bulk Cleanser

EmailLLM: Bulk Cleanser is a project developed as part of the CS 329 course. It utilizes AI and Natural Language Processing (NLP) techniques to create an intelligent email filtering system. This project aims to classify and filter emails based on user-defined keywords and content relevance. Unwanted or irrelevant emails (bulk emails) are automatically stored in a separate folder to help reduce clutter in the inbox.

The project aims to improve email organization, save storage space, and reduce the time spent manually sorting unwanted emails.


Features

Bulk Email Detection: Filters mass or bulk emails by analyzing content, subject, and sender.

Custom Keywords: Allows users to define custom keywords or phrases to filter emails.

Preprocessing: Utilizes NLP techniques to process email text (lemmatization, stopword removal).

User-Friendly Interface: Simple interface to upload and manage emails.

Seamless Integration: Can be integrated with existing email platforms for automated processing (future implementation).


Technologies Used

Python: Programming language for backend and AI logic.

Flask: Web framework to create the frontend for interacting with the email system.

spaCy: NLP library for text processing, including tokenization, lemmatization, and stopword removal.

SQLite: Database (if required) for storing user preferences and filtered emails.

HTML/CSS: Frontend for displaying the email simulation and processing results.
