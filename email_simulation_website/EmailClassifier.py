import os
import re
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from google import genai

from datetime import datetime

class EmailClassifier:
    def __init__(self, root):
        self.root = root
        self.root.title("Email Classification System")
        self.root.geometry("900x700")
        
        # Configure Google Gemini API
        self.api_key = "AIzaSyBcKKSaLvN0yN6ZHMG41Npew5gLiqbesqs"
        self.configure_gemini()
        
        # Email data
        self.emails = []
        self.categories = {}
        self.classified_emails = {}
        self.uncategorized_emails = []
        
        # Create tabs
        self.tab_control = ttk.Notebook(root)
        
        # Tab 1: Email Selection and Category Definition
        self.input_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.input_tab, text="Input Configuration")
        
        # Tab 2: Classification Results
        self.output_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.output_tab, text="Classification Results")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Setup input interface
        self.setup_input_interface()
        
        # Setup output interface
        self.setup_output_interface()
    
    def configure_gemini(self):
        """Configure the Gemini API."""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            messagebox.showerror("API Error", f"Failed to configure Gemini API: {str(e)}")
    
    def setup_input_interface(self):
        """Create the input interface."""
        # File selection section
        file_frame = ttk.LabelFrame(self.input_tab, text="Email Source Selection")
        file_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(file_frame, text="Select Email Source File:").pack(side=tk.LEFT, padx=5, pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=50).pack(side=tk.LEFT, padx=5, pady=5)
        
        ttk.Button(file_frame, text="Browse", command=self.browse_file).pack(side=tk.LEFT, padx=5, pady=5)
        ttk.Button(file_frame, text="Load Emails", command=self.load_emails).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Categories section
        categories_frame = ttk.LabelFrame(self.input_tab, text="Category Management")
        categories_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Left side - Category inputs
        left_frame = ttk.Frame(categories_frame)
        left_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=5, pady=5)
        
        ttk.Label(left_frame, text="Category Name:").pack(anchor="w", padx=5, pady=2)
        self.category_name_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.category_name_var, width=30).pack(anchor="w", padx=5, pady=2)
        
        ttk.Label(left_frame, text="Keywords (comma separated):").pack(anchor="w", padx=5, pady=2)
        self.keywords_var = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.keywords_var, width=50).pack(anchor="w", padx=5, pady=2)
        
        button_frame = ttk.Frame(left_frame)
        button_frame.pack(anchor="w", padx=5, pady=5)
        ttk.Button(button_frame, text="Add Category", command=self.add_category).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_category).pack(side=tk.LEFT, padx=5)
        
        # Right side - Categories list
        right_frame = ttk.Frame(categories_frame)
        right_frame.pack(side=tk.RIGHT, fill="both", expand=True, padx=5, pady=5)
        
        ttk.Label(right_frame, text="Defined Categories:").pack(anchor="w", padx=5, pady=2)
        
        # Category Treeview
        columns = ("Category", "Keywords")
        self.category_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=10)
        
        for col in columns:
            self.category_tree.heading(col, text=col)
            self.category_tree.column(col, width=150)
        
        self.category_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Classification button
        action_frame = ttk.Frame(self.input_tab)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(action_frame, text="Classify Emails", command=self.classify_emails).pack(pady=10)
    
    def setup_output_interface(self):
        """Create the output interface."""
        # Results section
        results_frame = ttk.LabelFrame(self.output_tab, text="Classification Results")
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Notebook for categories
        self.results_notebook = ttk.Notebook(results_frame)
        self.results_notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Uncategorized emails frame and download button
        uncategorized_frame = ttk.Frame(self.output_tab)
        uncategorized_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(uncategorized_frame, text="Download Uncategorized Emails", 
                  command=self.download_uncategorized).pack(pady=5)
    
    def browse_file(self):
        """Open file dialog to select email source file."""
        filepath = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            self.file_path_var.set(filepath)
    
    def load_emails(self):
        """Load emails from the selected file."""
        filepath = self.file_path_var.get()
        if not filepath:
            messagebox.showwarning("File Error", "Please select an email source file.")
            return
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split emails using the stopword
            stopword = "Caleb_Kairos_Michael_Nate_STOP_EMAIL"
            raw_emails = content.split(stopword)
            
            # Clean and process emails
            self.emails = [email.strip() for email in raw_emails if email.strip()]
            
            messagebox.showinfo("Success", f"Loaded {len(self.emails)} emails from file.")
        except Exception as e:
            messagebox.showerror("File Error", f"Failed to load emails: {str(e)}")
    
    def add_category(self):
        """Add a new category with keywords."""
        category_name = self.category_name_var.get().strip()
        keywords = self.keywords_var.get().strip()
        
        if not category_name:
            messagebox.showwarning("Input Error", "Category name cannot be empty.")
            return
        
        if not keywords:
            messagebox.showwarning("Input Error", "Please enter at least one keyword.")
            return
        
        # Split keywords and clean them
        keyword_list = [k.strip().lower() for k in keywords.split(',') if k.strip()]
        
        # Add to categories dictionary
        self.categories[category_name] = keyword_list
        
        # Update category tree
        self.category_tree.insert("", "end", values=(category_name, ", ".join(keyword_list)))
        
        # Clear inputs
        self.category_name_var.set("")
        self.keywords_var.set("")
    
    def remove_category(self):
        """Remove selected category."""
        selected_item = self.category_tree.selection()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a category to remove.")
            return
        
        category_name = self.category_tree.item(selected_item[0])['values'][0]
        
        # Remove from dictionary
        if category_name in self.categories:
            del self.categories[category_name]
        
        # Remove from tree
        self.category_tree.delete(selected_item[0])
    
    def classify_emails(self):
        """Send emails to Gemini for classification."""
        if not self.emails:
            messagebox.showwarning("Input Error", "No emails loaded. Please load emails first.")
            return
        
        if not self.categories:
            messagebox.showwarning("Input Error", "No categories defined. Please add at least one category.")
            return
        
        # Clear previous classifications
        self.classified_emails = {category: [] for category in self.categories}
        self.uncategorized_emails = []
        
        # Reset results tabs
        for tab in self.results_notebook.tabs():
            self.results_notebook.forget(tab)
        
        # Create a prompt for Gemini
        prompt = self._create_classification_prompt()
        
        try:
            # Send to Gemini and get response
            response = self.model.generate_content(prompt)
            
            # Parse the results
            self._parse_classification_results(response.text)
            
            # Update the output interface
            self._update_results_display()
            
            # Switch to output tab
            self.tab_control.select(self.output_tab)
            
            messagebox.showinfo("Classification Complete", 
                               f"Emails classified. {len(self.uncategorized_emails)} emails are uncategorized.")
            
        except Exception as e:
            messagebox.showerror("Classification Error", f"Error during classification: {str(e)}")
    
    def _create_classification_prompt(self):
        """Create the prompt for Gemini to classify emails."""
        prompt = "Please classify the following emails into these categories based on these keywords:\n\n"
        
        # Add categories and keywords
        for category, keywords in self.categories.items():
            prompt += f"Category '{category}': Keywords = {', '.join(keywords)}\n"
        
        prompt += "\nIf an email doesn't fit any category, mark it as 'UNCATEGORIZED'.\n"
        prompt += "Please respond with each email's classification in this format:\n"
        prompt += "EMAIL #1: [CATEGORY_NAME]\nEMAIL #2: [CATEGORY_NAME]\n...\n\n"
        
        # Add emails with numbers
        for i, email in enumerate(self.emails, 1):
            # Only include the first 500 characters of each email to avoid large prompts
            email_preview = email[:500] + ("..." if len(email) > 500 else "")
            prompt += f"--- EMAIL #{i} ---\n{email_preview}\n\n"
        
        return prompt
    
    def _parse_classification_results(self, result_text):
        """Parse Gemini's classification results."""
        lines = result_text.strip().split('\n')
        pattern = re.compile(r'EMAIL #(\d+):\s*(\w+)')
        
        for line in lines:
            match = pattern.search(line)
            if match:
                email_num = int(match.group(1))
                category = match.group(2).strip()
                
                if 0 < email_num <= len(self.emails):
                    email_content = self.emails[email_num-1]
                    
                    if category.upper() == 'UNCATEGORIZED':
                        self.uncategorized_emails.append(email_content)
                    elif category in self.categories:
                        self.classified_emails[category].append(email_content)
                    else:
                        # If category not found, treat as uncategorized
                        self.uncategorized_emails.append(email_content)
    
    def _update_results_display(self):
        """Update the results tabs with classified emails."""
        # Create a tab for each category
        for category, emails in self.classified_emails.items():
            tab_frame = ttk.Frame(self.results_notebook)
            self.results_notebook.add(tab_frame, text=f"{category} ({len(emails)})")
            
            # Create text widget to display emails
            text_widget = tk.Text(tab_frame, wrap=tk.WORD, height=25, width=80)
            text_widget.pack(fill="both", expand=True, padx=5, pady=5)
            
            # Insert emails
            for i, email in enumerate(emails, 1):
                text_widget.insert(tk.END, f"--- Email #{i} ---\n{email}\n\n")
            
            text_widget.config(state=tk.DISABLED)  # Make read-only
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(tab_frame, command=text_widget.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text_widget.config(yscrollcommand=scrollbar.set)
        
        # Create tab for uncategorized
        uncategorized_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(uncategorized_frame, text=f"Uncategorized ({len(self.uncategorized_emails)})")
        
        unc_text = tk.Text(uncategorized_frame, wrap=tk.WORD, height=25, width=80)
        unc_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        for i, email in enumerate(self.uncategorized_emails, 1):
            unc_text.insert(tk.END, f"--- Email #{i} ---\n{email}\n\n")
        
        unc_text.config(state=tk.DISABLED)  # Make read-only
        
        # Add scrollbar
        unc_scrollbar = ttk.Scrollbar(uncategorized_frame, command=unc_text.yview)
        unc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        unc_text.config(yscrollcommand=unc_scrollbar.set)
    
    def download_uncategorized(self):
        """Download uncategorized emails to a local file."""
        if not self.uncategorized_emails:
            messagebox.showinfo("Download", "No uncategorized emails to download.")
            return
        
        # Get save file location
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile=f"uncategorized_emails_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        
        if not filename:
            return  # User cancelled
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for i, email in enumerate(self.uncategorized_emails, 1):
                    f.write(f"--- Email #{i} ---\n{email}\n\n")
            
            messagebox.showinfo("Download Complete", 
                              f"Successfully saved {len(self.uncategorized_emails)} uncategorized emails to {filename}")
        except Exception as e:
            messagebox.showerror("Download Error", f"Failed to save file: {str(e)}")


def main():
    root = tk.Tk()
    app = EmailClassifier(root)
    root.mainloop()


if __name__ == "__main__":
    main()
