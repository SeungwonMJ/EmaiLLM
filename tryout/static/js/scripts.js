// Current selected email
let currentEmailId = 0;

// Global map to store colors for category names
const categoryColors = {};

// --- Notification Function (moved to global scope) ---
function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Add to body
    document.body.appendChild(notification);
    
    // Show with animation
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Auto-remove after delay
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300); // Match animation duration
    }, 3000);
}
// --- End Notification Function ---

// Select email function
function selectEmail(emailId) {
    console.log(`Selecting email with ID: ${emailId}`); // Log selection

    if (!initialEmails || emailId < 0 || emailId >= initialEmails.length) {
        console.error(`Invalid emailId: ${emailId} or initialEmails not loaded properly.`);
        return;
    }

    // Update current email ID
    currentEmailId = emailId;
    
    // Remove selected class from all emails
    document.querySelectorAll('.email-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selected class to clicked email
    const selectedEmailElement = document.querySelector(`.email-item[data-id="${emailId}"]`);
    if (selectedEmailElement) {
        selectedEmailElement.classList.add('selected');
    } else {
        console.warn(`Could not find email item element with data-id: ${emailId}`);
    }
    
    // Get email data
    const email = initialEmails[emailId];
    console.log("Selected email data:", email); // Log email data
    
    // Update details pane elements safely
    const subjectEl = document.getElementById('email-subject');
    const senderNameEl = document.getElementById('email-sender-name'); // Correct ID
    const toEl = document.getElementById('email-to');
    const dateEl = document.getElementById('email-date');
    const contentEl = document.getElementById('email-content');

    if (subjectEl) subjectEl.textContent = email.subject || 'No Subject';
    // Update sender name/email using the correct ID
    if (senderNameEl) senderNameEl.textContent = email.sender_name || email.sender_email || 'No Sender'; 
    if (toEl) toEl.textContent = email.recipients || 'No Recipients';
    if (dateEl) dateEl.textContent = email.date || 'No Date';
    if (contentEl) contentEl.innerHTML = email.content || 'No Content'; // Use innerHTML if content can be HTML
    
    // Clear chat messages
    const chatMessagesEl = document.getElementById('chat-messages');
    if (chatMessagesEl) {
        chatMessagesEl.innerHTML = `
            <div class="ai-message message">
                Hi there! Ask me anything about the selected email.
            </div>
        `;
    } else {
        console.warn("Chat messages element not found.");
    }
    
    // Clear classification result
    const resultElement = document.getElementById('classification-result');
    if (resultElement) {
        resultElement.innerHTML = '';
    }
}

// Function to classify a specific email by its ID
async function classifyEmailById(emailId) {
    console.log(`Attempting to classify email ID: ${emailId}`);
    const emailItem = document.querySelector(`.email-item[data-id="${emailId}"]`);
    const resultContainer = emailItem ? emailItem.querySelector('.email-tags') : null; // Target tags within the item
    const classifyButton = document.querySelector(`.email-item[data-id="${emailId}"] .btn-classify`); // Maybe add specific btn later

    if (!emailItem) {
        console.error(`Email item not found for ID: ${emailId}`);
        return { status: 'error', message: 'Email item not found in UI.' };
    }

    // Optional: Add a temporary loading state to the specific email item
    emailItem.classList.add('classifying');
    // You might add a spinner icon to the tags area or disable its classify button
    
    try {
        const response = await fetch('/classify-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email_id: emailId // Use the passed emailId
            }),
        });

        const data = await response.json();
        console.log(`Classification response for ID ${emailId}:`, data);

        emailItem.classList.remove('classifying'); // Remove loading state

        if (data.status === 'success') {
            let tagsHtml = '';
            if (data.tags && data.tags.length > 0) {
                tagsHtml = ''; // Start fresh for the tags div content
                data.tags.forEach(tag => {
                    // Use getTagIcon helper if you want icons here too
                    tagsHtml += `
                        <span class="tag tag-${tag.replace(/\s+/g, '-').toLowerCase()}">
                           ${getTagIcon(tag)} ${tag}
                        </span>
                    `;
                });
                
                let tagsElement = emailItem.querySelector('.email-tags');
                if (!tagsElement) {
                    tagsElement = document.createElement('div');
                    tagsElement.className = 'email-tags';
                    const previewElement = emailItem.querySelector('.email-preview');
                    if (previewElement) {
                         previewElement.insertAdjacentElement('afterend', tagsElement);
                    } else {
                        emailItem.appendChild(tagsElement);
                    }
                }
                tagsElement.innerHTML = tagsHtml;
                applyColorsToTags(tagsElement); // Apply colors to the new tags
                
                // Update client-side data store
                if (initialEmails[emailId]) {
                    initialEmails[emailId].tags = data.tags;
                    console.log(`Updated initialEmails[${emailId}] tags:`, initialEmails[emailId].tags);
                }
                
                return { status: 'success', emailId: emailId, tags: data.tags };
            } else {
                // Handle case where classification is successful but finds no tags
                 let tagsElement = emailItem.querySelector('.email-tags');
                 if (tagsElement) tagsElement.innerHTML = '<span class="text-muted small">No relevant tags found.</span>'; // Clear or update UI
                 
                 // Update client-side data store (empty tags)
                 if (initialEmails[emailId]) {
                    initialEmails[emailId].tags = [];
                     console.log(`Updated initialEmails[${emailId}] tags to empty`);
                 }
                 
                 return { status: 'success', emailId: emailId, tags: [] };
            }
        } else {
            // Handle classification error for this specific email
             let tagsElement = emailItem.querySelector('.email-tags');
             if (tagsElement) tagsElement.innerHTML = '<span class="text-danger small">Classification failed.</span>'; // Update UI
            console.error(`Classification failed for email ${emailId}: ${data.message}`);
            return { status: 'error', emailId: emailId, message: data.message || 'Classification failed.' };
        }
    } catch (error) {
        console.error(`Fetch error during classification for email ${emailId}:`, error);
        emailItem.classList.remove('classifying'); // Ensure loading state removed on error
        let tagsElement = emailItem.querySelector('.email-tags');
        if (tagsElement) tagsElement.innerHTML = '<span class="text-danger small">Network error.</span>'; // Update UI
        return { status: 'error', emailId: emailId, message: error.message };
    }
}

// Classify *currently selected* email function (now uses the refactored function)
function classifyCurrentEmail() {
    const resultElement = document.getElementById('classification-result'); // Detail pane result area
    
    if (!resultElement) {
        console.error("Classification result element in detail pane not found.");
        return;
    }
    
    // Show loading in the *details pane*
    resultElement.innerHTML = `
        <div class="alert alert-info d-flex align-items-center" role="alert">
            <i class="fas fa-spinner fa-spin mr-2"></i> Classifying email...
        </div>
    `;
    
    classifyEmailById(currentEmailId).then(result => {
        // Update the details pane based on the result
        if (result.status === 'success') {
             if (result.tags.length > 0) {
                 let tagsHtml = '<div class="mt-2">';
                 result.tags.forEach(tag => {
                     tagsHtml += `
                        <span class="tag tag-${tag.replace(/\s+/g, '-').toLowerCase()}">
                            ${getTagIcon(tag)} ${tag}
                        </span>
                    `;
                 });
                 tagsHtml += '</div>';
                 // Apply colors here too
                 const tempDiv = document.createElement('div');
                 tempDiv.innerHTML = tagsHtml;
                 applyColorsToTags(tempDiv);
                 tagsHtml = tempDiv.innerHTML;
                 
                 resultElement.innerHTML = `
                    <div class="alert alert-success mt-2" role="alert">
                        <strong>Classification complete!</strong> Tags applied to email list item.
                        ${tagsHtml}
                    </div>
                 `;
             } else {
                  resultElement.innerHTML = `
                    <div class="alert alert-info mt-2" role="alert">
                        <strong>Classification complete!</strong> No relevant tags found for this email.
                    </div>
                 `;
             }
        } else {
             resultElement.innerHTML = `
                <div class="alert alert-danger mt-2" role="alert">
                    <strong>Error:</strong> ${result.message || 'Failed to classify email.'}
                </div>
            `;
        }
    });
}

// Send chat message function
function sendChatMessage() {
    const inputField = document.getElementById('chat-input-field');
    const message = inputField.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.innerHTML += `
        <div class="user-message message">
            ${message}
        </div>
    `;
    
    // Add loading indicator
    chatMessages.innerHTML += `
        <div class="ai-message message" id="ai-typing">
            <div class="loading-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Clear input field
    inputField.value = '';
    
    // Simulate API call
    setTimeout(() => {
        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                query: message,
                email_id: currentEmailId
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Remove loading indicator
            document.getElementById('ai-typing').remove();
            
            if (data.status === 'success') {
                chatMessages.innerHTML += `
                    <div class="ai-message message">
                        ${data.response}
                    </div>
                `;
            } else {
                chatMessages.innerHTML += `
                    <div class="ai-message message">
                        I'm sorry, I encountered an error while processing your request.
                    </div>
                `;
            }
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => {
            // Remove loading indicator
            document.getElementById('ai-typing').remove();
            
            chatMessages.innerHTML += `
                <div class="ai-message message">
                    I'm sorry, I encountered an error: ${error.message}
                </div>
            `;
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        });
    }, 1000); // Simulate network delay
}

// Helper function to get tag icon
function getTagIcon(tag) {
    switch(tag) {
        case 'networking':
            return '<i class="fas fa-network-wired"></i>';
        case 'internship':
            return '<i class="fas fa-briefcase"></i>';
        case 'club events':
            return '<i class="fas fa-calendar-alt"></i>';
        default:
            return '<i class="fas fa-tag"></i>';
    }
}

// Add event listener for chat input
document.getElementById('chat-input-field')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendChatMessage();
    }
});

// Helper function to generate a random light HSL color
function getRandomLightColor() {
    const hue = Math.floor(Math.random() * 360);
    const saturation = Math.floor(Math.random() * 20) + 60; // 60-80% saturation
    const lightness = Math.floor(Math.random() * 10) + 88; // 88-98% lightness
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

// Helper function to get a contrasting text color (simple version)
function getContrastTextColor(hslColor) {
    // Basic check: for very light backgrounds, use dark text
    // A more sophisticated check would analyze the actual RGB values
    const lightness = parseInt(hslColor.split(',')[2]); // Get lightness value
    return lightness > 65 ? 'var(--text-primary)' : 'white'; // Use theme variable or white
}

// Function to get or generate color for a category
function getColorForCategory(categoryName) {
    // Normalize category name (lowercase, trim)
    const normalizedName = categoryName.trim().toLowerCase();
    
    // Skip color generation for predefined keywords with specific styles
    const predefinedKeywords = ['networking', 'internship', 'club events', 'deadlines', 'academic']; 
    if (predefinedKeywords.includes(normalizedName)) {
        return null; // Indicate no custom color needed
    }

    if (!categoryColors[normalizedName]) {
        categoryColors[normalizedName] = getRandomLightColor();
    }
    return categoryColors[normalizedName];
}

// Function to apply stored/generated colors to tags within an element
function applyColorsToTags(containerElement) {
    if (!containerElement) return;
    
    const tags = containerElement.querySelectorAll('.tag');
    tags.forEach(tag => {
        // Extract category name from the tag's text content or a data attribute if available
        // Simple extraction based on text, assuming icon is first child
        const categoryName = tag.textContent.trim().toLowerCase(); 
        
        const bgColor = getColorForCategory(categoryName);
        
        if (bgColor) { // Only apply if a color was generated (i.e., not predefined)
            const textColor = getContrastTextColor(bgColor);
            tag.style.backgroundColor = bgColor;
            tag.style.color = textColor;
            // Ensure icon color contrasts too if it doesn't have its own class
            const icon = tag.querySelector('i');
            if (icon && !icon.className.includes('text-')) { // Don't override specific text colors
                icon.style.color = textColor;
            }
        }
    });
}

// Add these category management functions 
function initCategoryManagement() {
    const addButton = document.getElementById('add-category-btn');
    const categoryInput = document.getElementById('category-input');
    const categoryShowcase = document.getElementById('category-showcase');
    
    if (!addButton || !categoryInput || !categoryShowcase) {
        console.warn("Category management elements not found. Skipping initialization.");
        return;
    }

    // Setup event listeners
    addButton.addEventListener('click', addCategory);
    categoryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addCategory();
        }
    });
    
    // Setup delete button listeners for existing categories
    setupDeleteButtons();
    
    // Apply random colors to existing generic badges on load
    applyRandomColorsToExistingBadges();

    function addCategory() {
        const categoryName = categoryInput.value.trim().toLowerCase();
        if (!categoryName) return;
        
        // Check if category already exists
        const existingCategories = getExistingCategories();
        if (existingCategories.includes(categoryName)) {
            showNotification('Category already exists', 'warning');
            return;
        }
        
        // Create new category badge
        const categoryBadge = document.createElement('span');
        categoryBadge.className = 'category-badge';
        
        // Add icon based on category name (keep specific icons)
        let iconHtml = '<i class="fas fa-tag"></i>'; // Default icon
        let specificClass = ''; // Flag for specific keywords

        if (categoryName === 'networking') {
            iconHtml = '<i class="fas fa-network-wired text-warning"></i>';
            specificClass = 'tag-networking'; // Add specific class if needed
        } else if (categoryName === 'internship') {
            iconHtml = '<i class="fas fa-briefcase text-primary"></i>';
             specificClass = 'tag-internship';
        } else if (categoryName === 'club events') {
            iconHtml = '<i class="fas fa-calendar-alt text-success"></i>';
            specificClass = 'tag-club-events';
        } // Add more specific cases if needed
        
        categoryBadge.innerHTML = `
            ${iconHtml}
            ${categoryName}
            <button class="delete-category" data-category="${categoryName}" title="Delete category">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Apply random colors ONLY if it's not a specifically styled keyword
        if (!specificClass) {
             const bgColor = getColorForCategory(categoryName); // Use the getter function
             if (bgColor) { // Check if color should be applied
                 const textColor = getContrastTextColor(bgColor);
                 categoryBadge.style.backgroundColor = bgColor;
                 categoryBadge.style.color = textColor;
                 // Adjust delete button color for contrast if needed
                 const deleteBtn = categoryBadge.querySelector('.delete-category');
                 if (deleteBtn) deleteBtn.style.color = textColor;
             }
        } else {
             // Optionally add the specific class back if you have CSS for it
             // categoryBadge.classList.add(specificClass);
        }
        
        // Add to showcase
        categoryShowcase.appendChild(categoryBadge);
        
        // Clear input
        categoryInput.value = '';
        
        // Add delete listener to new badge
        setupDeleteButtons(); // Call setup for the *new* button
        
        // Save to backend
        saveCategoryToBackend(categoryName);
    }
    
    function setupDeleteButtons() {
        // Detach existing listeners before re-attaching to prevent duplicates
        const buttons = categoryShowcase.querySelectorAll('.delete-category');
        buttons.forEach(button => {
            const newButton = button.cloneNode(true); // Clone to remove old listeners
            button.parentNode.replaceChild(newButton, button);
            newButton.addEventListener('click', handleDeleteCategory);
        });
    }

    function handleDeleteCategory(event) {
        const button = event.currentTarget;
        const categoryToDelete = button.getAttribute('data-category');
        const badgeElement = button.parentElement;
        
        // Optimistically remove the badge from the UI
        badgeElement.remove();
        
        // Call backend to delete
        deleteCategoryFromBackend(categoryToDelete).then(success => {
            if (success) {
                // Backend confirmed deletion, now remove tag from email list UI
                console.log(`Backend confirmed deletion of ${categoryToDelete}, removing from email list UI.`);
                document.querySelectorAll('.email-item .email-tags').forEach(tagsContainer => {
                    // Find tags within this container that match the deleted category
                    tagsContainer.querySelectorAll('.tag').forEach(tagElement => {
                        // Be careful with text matching; consider adding a data-category attribute to tags if possible
                        const tagName = tagElement.textContent.trim().toLowerCase();
                        if (tagName === categoryToDelete) {
                            console.log(`Removing tag element for ${categoryToDelete} from email item.`);
                            tagElement.remove();
                        }
                    });
                    // If the container is now empty, maybe remove it or add a placeholder
                    if (tagsContainer.children.length === 0 && tagsContainer.parentNode) {
                         // Optional: remove the empty .email-tags div
                         // tagsContainer.remove(); 
                    }
                });
                
                // Update the initialEmails array to reflect the change
                initialEmails.forEach(email => {
                    if (email.tags && email.tags.includes(categoryToDelete)) {
                        email.tags = email.tags.filter(tag => tag !== categoryToDelete);
                    }
                });
                console.log("initialEmails updated after tag removal.");

                // If the currently selected email was affected, update the details pane? (Optional)
                // This is complex as details pane might not directly show tags

            } else {
                // Deletion failed, add the badge back?
                console.error(`Backend failed to delete category: ${categoryToDelete}. Re-adding badge (or handle differently).`);
                // Re-adding might be complex, maybe just notify user
                showNotification(`Failed to delete category ${categoryToDelete} on server.`, 'error');
                // Re-append badgeElement if needed (might require storing it)
            }
        });
    }
    
    function getExistingCategories() {
        const categories = [];
        document.querySelectorAll('.category-badge').forEach(badge => {
            // Extract text content without the delete button text
            const categoryText = badge.textContent.trim().split('\n')[0].trim();
            categories.push(categoryText.toLowerCase());
        });
        return categories;
    }
    
    // New function to apply colors to existing badges on load
    function applyRandomColorsToExistingBadges() {
        const existingBadges = categoryShowcase.querySelectorAll('.category-badge');
        existingBadges.forEach(badge => {
            const categoryName = badge.textContent.trim().split('\n')[0].trim().toLowerCase();
            const bgColor = getColorForCategory(categoryName); // Use the getter
            
            // Apply only if color exists (not predefined) and no inline style already
            if (bgColor && !badge.getAttribute('style')) {
                 const textColor = getContrastTextColor(bgColor);
                 badge.style.backgroundColor = bgColor;
                 badge.style.color = textColor;
                 const deleteBtn = badge.querySelector('.delete-category');
                 if (deleteBtn) deleteBtn.style.color = textColor;
            }
        });
    }

    function saveCategoryToBackend(category) {
        // New implementation goes here (replace existing function)
        // Call API to save category to .env
        fetch('/add-category', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                category: category
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showNotification('Category added successfully', 'success');
                
                // Update the sidebar keyword folders
                updateSidebarKeywords(data.keywords);
            } else {
                showNotification('Failed to add category', 'error');
            }
        })
        .catch(error => {
            console.error('Error saving category:', error);
            showNotification('Error saving category', 'error');
        });
    }
    
    function deleteCategoryFromBackend(category) {
        // New implementation goes here (replace existing function)
        // Call API to remove category from .env
        console.log(`Sending request to delete category: ${category}`);
        return fetch('/delete-category', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                category: category
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showNotification('Category removed', 'success');
                // Update the sidebar keyword folders
                updateSidebarKeywords(data.keywords || []); // Use updated keywords from response
                return true; // Indicate success
            } else {
                showNotification(`Failed to remove category: ${data.message || 'Unknown error'}`, 'error');
                return false; // Indicate failure
            }
        })
        .catch(error => {
            console.error('Error removing category:', error);
            showNotification('Error removing category', 'error');
            return false; // Indicate failure
        });
    }
    
    function updateSidebarKeywords(keywords) {
        const keywordFoldersContainer = document.querySelector('.sidebar .section-header + div'); // Target container more reliably
        if (!keywordFoldersContainer) return;

        const sectionHeader = keywordFoldersContainer.closest('.sidebar').querySelector('.section-header'); // Find header relative to sidebar
        if (!sectionHeader) return;

        // Clear existing keyword folders (more robust selector)
        const existingFolders = keywordFoldersContainer.parentElement.querySelectorAll('.folder.keyword-folder');
        existingFolders.forEach(folder => folder.remove());
        
        // Add new folders based on keywords
        let folderHTML = '';
        keywords.forEach(keyword => {
            let iconClass = 'fa-tag';
            let colorClass = ''; // Color class for icon
            
            // Match keyword styling from template
            if (keyword === 'networking') {
                iconClass = 'fa-network-wired';
                colorClass = 'text-warning'; 
            } else if (keyword === 'internship') {
                iconClass = 'fa-briefcase';
                colorClass = 'text-primary';
            } else if (keyword === 'club events') {
                iconClass = 'fa-calendar-alt';
                colorClass = 'text-success';
            } // Add other specific icons if needed
            
            // Add a specific class to identify these dynamic folders
            folderHTML += `
                <div class="folder keyword-folder">
                    <a href="/?keyword=${encodeURIComponent(keyword)}" class="folder-link">
                        <span>
                            <i class="fas ${iconClass} ${colorClass}"></i>
                            ${keyword.charAt(0).toUpperCase() + keyword.slice(1)}
                        </span>
                        <span class="folder-count">0</span> 
                    </a>
                </div>
            `;
            // Note: Count for dynamic folders is initially 0, needs update logic if required
        });
        
        // Insert after section header
        sectionHeader.insertAdjacentHTML('afterend', folderHTML);
    }
}

// Add notification styles
document.addEventListener('DOMContentLoaded', function() {
    // Initialize category management
    initCategoryManagement();
    
    // Add notification styles dynamically
    const style = document.createElement('style');
    style.textContent = `
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 4px;
            color: white;
            z-index: 1000;
            opacity: 0;
            transform: translateY(-20px);
            transition: all 0.3s ease;
        }
        
        .notification.show {
            opacity: 1;
            transform: translateY(0);
        }
        
        .notification-success {
            background-color: #52c41a;
        }
        
        .notification-warning {
            background-color: #faad14;
        }
        
        .notification-error {
            background-color: #f5222d;
        }
    `;
    document.head.appendChild(style);
});

// Initialize all functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Debug logs for initialization
    console.log("DOM fully loaded");
    console.log("Initial emails data:", initialEmails ? initialEmails.length : "Not loaded");
    
    // Add a document-level click handler (keep for debugging if needed)
    // document.addEventListener('click', function(event) { ... });
    
    // Initialize category management (which now includes coloring badges)
    initCategoryManagement();

    // Apply colors to all email tags initially present on the page
    document.querySelectorAll('.email-item').forEach(item => {
        applyColorsToTags(item.querySelector('.email-tags'));
    });
    
    // Initialize dark mode
    const darkModeToggle = document.getElementById('darkmode-toggle');
    if (darkModeToggle) {
        // Check for saved theme preference or use preferred color scheme
        const savedTheme = localStorage.getItem('theme');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        // Apply theme
        if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
            document.body.classList.add('dark-theme');
            darkModeToggle.checked = true;
        }
        
        // Toggle theme when switch is clicked
        darkModeToggle.addEventListener('change', function() {
            if (this.checked) {
                document.body.classList.add('dark-theme');
                localStorage.setItem('theme', 'dark');
            } else {
                document.body.classList.remove('dark-theme');
                localStorage.setItem('theme', 'light');
            }
        });
    }
    
    // Initialize process untagged button
    const processUntaggedButton = document.getElementById('process-untagged');
    if (processUntaggedButton) {
        processUntaggedButton.addEventListener('click', function(event) {
            event.preventDefault();
            if (confirm("You are about to download and then delete all untagged emails. Are you sure you want to proceed?")) {
                window.location.href = '/process-untagged';
            }
        });
    }
    
    // Initialize new email functionality
    const newEmailButton = document.getElementById('new-email-button');
    const newEmailModal = document.getElementById('newEmailModal');
    const sendNewEmailButton = document.getElementById('sendNewEmailButton');
    const newEmailForm = document.getElementById('newEmailForm');

    if (newEmailButton && newEmailModal && sendNewEmailButton && newEmailForm) {
        newEmailButton.addEventListener('click', function() {
            $(newEmailModal).modal('show');
        });

        sendNewEmailButton.addEventListener('click', function(event) {
            event.preventDefault();
            const formData = new FormData(newEmailForm);
            const emailData = {};
            formData.forEach((value, key) => {
                emailData[key] = value;
            });

            if (!emailData.sender_name || !emailData.sender_email || !emailData.recipients || !emailData.subject || !emailData.content) {
                alert("Please fill in all required fields.");
                return;
            }

            fetch('/create-email', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(emailData),
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert("Email sent successfully!");
                    $(newEmailModal).modal('hide');
                    newEmailForm.reset();
                } else {
                    alert('Error sending email: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Error sending email:', error);
                alert("Error communicating with the server.");
            });
        });
    }

    // --- Select All Checkbox Logic --- 
    const selectAllCheckbox = document.getElementById('select-all-emails');
    const emailListContainer = document.querySelector('.email-list');

    if (selectAllCheckbox && emailListContainer) {
        // Function to get all individual email checkboxes currently visible
        const getIndividualCheckboxes = () => emailListContainer.querySelectorAll('.email-item .email-select input[type="checkbox"]');

        // Listener for the main "select all" checkbox
        selectAllCheckbox.addEventListener('change', function() {
            const isChecked = this.checked;
            getIndividualCheckboxes().forEach(checkbox => {
                checkbox.checked = isChecked;
            });
        });

        // Function to update the main checkbox based on individual ones
        const updateSelectAllCheckbox = () => {
            const individualCheckboxes = getIndividualCheckboxes();
            const allChecked = individualCheckboxes.length > 0 && Array.from(individualCheckboxes).every(cb => cb.checked);
            const someChecked = Array.from(individualCheckboxes).some(cb => cb.checked);
            
            if (allChecked) {
                 selectAllCheckbox.checked = true;
                 selectAllCheckbox.indeterminate = false;
            } else if (someChecked) {
                 selectAllCheckbox.checked = false;
                 selectAllCheckbox.indeterminate = true; // Show indeterminate state
            } else {
                 selectAllCheckbox.checked = false;
                 selectAllCheckbox.indeterminate = false;
            }
        };

        // Add listeners to individual checkboxes (using event delegation on the list)
        emailListContainer.addEventListener('change', function(event) {
            if (event.target.matches('.email-item .email-select input[type="checkbox"]')) {
                updateSelectAllCheckbox();
            }
        });
        
        // Initial check in case the page loads with some items pre-selected
        updateSelectAllCheckbox(); 
        
    } else {
        console.warn("Select-all checkbox or email list container not found. Skipping select-all initialization.");
    }
    // --- End Select All Checkbox Logic ---

    // --- Batch Classify Button Logic ---
    const batchClassifyButton = document.getElementById('batch-classify-btn');
    const emailListContainerForBatch = document.querySelector('.email-list'); // Use the same container as select-all

    if (batchClassifyButton && emailListContainerForBatch) {
        batchClassifyButton.addEventListener('click', async function() {
            console.log("Batch Classify button clicked."); // <-- Log click

            const checkedCheckboxes = emailListContainerForBatch.querySelectorAll('.email-item .email-select input[type="checkbox"]:checked');
            console.log(`Found ${checkedCheckboxes.length} checked checkboxes.`); // <-- Log checkbox count
            
            if (checkedCheckboxes.length === 0) {
                showNotification('Please select emails to classify.', 'warning');
                return;
            }

            const emailIdsToClassify = Array.from(checkedCheckboxes).map(cb => {
                const emailItem = cb.closest('.email-item');
                return emailItem ? parseInt(emailItem.getAttribute('data-id'), 10) : null;
            }).filter(id => id !== null && !isNaN(id));

            console.log("Email IDs to classify:", emailIdsToClassify); // <-- Log extracted IDs

            if (emailIdsToClassify.length === 0) {
                showNotification('Could not find valid email IDs for selected items.', 'error');
                return;
            }

            showNotification(`Starting batch classification for ${emailIdsToClassify.length} emails...`, 'info');
            this.disabled = true; // Disable button during processing
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Classifying...';

            console.log("Mapping classification promises..."); // <-- Log before promises
            const classificationPromises = emailIdsToClassify.map(id => {
                 console.log(`Creating promise for ID: ${id}`); // <-- Log each ID being mapped
                 return classifyEmailById(id);
            });
            
            try {
                console.log("Awaiting Promise.allSettled..."); // <-- Log before await
                const results = await Promise.allSettled(classificationPromises);
                console.log("Promise.allSettled finished. Results:", results); // <-- Log results
                
                const successfulCount = results.filter(r => r.status === 'fulfilled' && r.value.status === 'success').length;
                const failedCount = results.length - successfulCount;
                
                let message = `Batch classification complete. ${successfulCount} successful`;
                if (failedCount > 0) {
                    message += `, ${failedCount} failed.`;
                    showNotification(message, 'warning');
                } else {
                    showNotification(message, 'success');
                }
                console.log("Batch classification results:", results);

            } catch (error) {
                // This catch is unlikely with Promise.allSettled but good practice
                console.error("Error during batch classification execution:", error);
                showNotification('An unexpected error occurred during batch classification.', 'error');
            } finally {
                 // Re-enable button and restore text
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-tags"></i> Batch Classify';
            }
        });
    } else {
         console.warn("Batch classify button or email list container not found. Skipping batch classify initialization.");
    }
    // --- End Batch Classify Button Logic ---

    // --- Event Listeners for Details Actions ---
    const detailsPane = document.querySelector('.email-details-pane');
    if (detailsPane) {
        detailsPane.addEventListener('click', function(event) {
            const button = event.target.closest('.details-action-btn');
            if (!button) return;

            if (button.id === 'untag-btn') {
                handleUntagClick();
            } else if (button.id === 'highlight-btn') {
                handleHighlightClick();
            } else if (button.id === 'delete-btn') {
                handleDeleteClick();
            }
        });
    } else {
        console.warn("Details pane not found, cannot attach action button listeners.");
    }
    // --- End Event Listeners ---
});

// --- Action Button Handlers (defined globally) ---

async function handleUntagClick() {
    if (currentEmailId === null || currentEmailId < 0) return;
    console.log(`Untag button clicked for email ID: ${currentEmailId}`);
    
    const untagButton = document.getElementById('untag-btn');
    if (untagButton) untagButton.disabled = true;

    try {
        const response = await fetch(`/untag-email/${currentEmailId}`, { method: 'POST' });
        const data = await response.json();

        if (data.status === 'success') {
            showNotification('Email untagged.', 'success');
            const emailItem = document.querySelector(`.email-item[data-id="${currentEmailId}"]`);
            const tagsContainer = emailItem ? emailItem.querySelector('.email-tags') : null;
            if (tagsContainer) {
                tagsContainer.innerHTML = '';
            }
            if (initialEmails[currentEmailId]) {
                initialEmails[currentEmailId].tags = [];
            }
        } else {
            showNotification(`Untag failed: ${data.message}`, 'error');
        }
    } catch (error) {
        console.error("Error during untag request:", error);
        showNotification('Error untagging email.', 'error');
    } finally {
        if (untagButton) untagButton.disabled = false;
    }
}

function handleHighlightClick() {
    if (currentEmailId === null || currentEmailId < 0) return;
    console.log(`Highlight button clicked for email ID: ${currentEmailId}`);
    
    const emailItem = document.querySelector(`.email-item[data-id="${currentEmailId}"]`);
    if (emailItem) {
        emailItem.classList.toggle('highlighted');
        const isHighlighted = emailItem.classList.contains('highlighted');
        showNotification(`Email ${isHighlighted ? 'highlighted' : 'unhighlighted'}.`, 'info'); 
    }
}

async function handleDeleteClick() {
    if (currentEmailId === null || currentEmailId < 0) return;
    console.log(`Delete button clicked for email ID: ${currentEmailId}`);
    
    if (confirm('Are you sure you want to delete this email permanently?')) {
        const deleteButton = document.getElementById('delete-btn');
        if (deleteButton) deleteButton.disabled = true;

        try {
            const response = await fetch(`/delete-email/${currentEmailId}`, { method: 'DELETE' });
            const data = await response.json();

            if (data.status === 'success') {
                showNotification('Email deleted.', 'success');
                const emailItem = document.querySelector(`.email-item[data-id="${currentEmailId}"]`);
                if (emailItem) {
                    emailItem.remove();
                }
                const deletedIndex = currentEmailId; // Store index before splicing
                initialEmails.splice(deletedIndex, 1);
                console.log(`Removed email at index ${deletedIndex} from initialEmails`);
                
                // Update data-id and onclick for subsequent items
                document.querySelectorAll('.email-item').forEach(item => {
                    let currentId = parseInt(item.getAttribute('data-id'), 10);
                    if (currentId > deletedIndex) {
                        let newIndex = currentId - 1;
                        item.setAttribute('data-id', newIndex);
                        // Re-attach listener correctly (avoiding direct onclick if possible)
                        item.onclick = () => selectEmail(newIndex); 
                    }
                 });
                
                // Clear details or select next
                const detailsSubjectEl = document.getElementById('email-subject');
                const detailsSenderEl = document.getElementById('email-sender-name');
                const detailsToEl = document.getElementById('email-to');
                const detailsDateEl = document.getElementById('email-date');
                const detailsContentEl = document.getElementById('email-content');
                const classificationResultEl = document.getElementById('classification-result');
                const chatMessagesEl = document.getElementById('chat-messages');

                if (detailsSubjectEl) detailsSubjectEl.textContent = 'Email Deleted';
                if (detailsSenderEl) detailsSenderEl.textContent = '';
                if (detailsToEl) detailsToEl.textContent = '';
                if (detailsDateEl) detailsDateEl.textContent = '';
                if (detailsContentEl) detailsContentEl.innerHTML = '<p class="text-muted p-3">Email has been deleted.</p>';
                if (classificationResultEl) classificationResultEl.innerHTML = '';
                if (chatMessagesEl) chatMessagesEl.innerHTML = ''; 
                
                currentEmailId = null; 
                 if (document.querySelectorAll('.email-item').length > 0) {
                     // Select the email that is now at the deleted index, or the last one if deleting last
                     let nextIndex = Math.min(deletedIndex, initialEmails.length - 1);
                     if (nextIndex >= 0) {
                        selectEmail(nextIndex); 
                     } else {
                        // Handle case where list becomes empty - clear details further?
                     }
                 } else {
                     // Handle empty list case
                 }
            } else {
                showNotification(`Delete failed: ${data.message}`, 'error');
            }
        } catch (error) {
            console.error("Error during delete request:", error);
            showNotification('Error deleting email.', 'error');
        } finally {
             if (deleteButton) deleteButton.disabled = false;
        }
    }
}
// --- End Action Button Handlers ---