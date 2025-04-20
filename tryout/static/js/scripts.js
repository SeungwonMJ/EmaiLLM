// Current selected email
let currentEmailId = 0;

// Select email function
function selectEmail(emailId) {
    // Update current email ID
    currentEmailId = emailId;
    
    // Remove selected class from all emails
    document.querySelectorAll('.email-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Add selected class to clicked email
    document.querySelectorAll('.email-item')[emailId].classList.add('selected');
    
    // Get email data
    const emails = initialEmails;
    const email = emails[emailId];
    
    // Update details pane
    document.getElementById('email-subject').textContent = email.subject;
    document.getElementById('email-from').textContent = `${email.sender_name} <${email.sender_email}>`;
    document.getElementById('email-to').textContent = email.recipients;
    document.getElementById('email-date').textContent = email.date;
    document.getElementById('email-content').textContent = email.content;
    
    // Clear chat messages
    document.getElementById('chat-messages').innerHTML = `
        <div class="ai-message message">
            Hi there! I can help you analyze and understand this email. What would you like to know?
        </div>
    `;
    
    // Clear classification result
    const resultElement = document.getElementById('classification-result');
    if (resultElement) {
        resultElement.innerHTML = '';
    }
}

// Classify current email function
function classifyCurrentEmail() {
    const resultElement = document.getElementById('classification-result');
    resultElement.innerHTML = `
        <div class="alert alert-info">
            <i class="fas fa-spinner fa-spin"></i> Classifying email...
        </div>
    `;
    
    // Simulate API call with fetch
    setTimeout(() => {
        fetch('/classify-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email_id: currentEmailId
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Generate tag HTML
                let tagsHtml = '';
                if (data.tags.length > 0) {
                    tagsHtml = '<div class="mt-2">';
                    data.tags.forEach(tag => {
                        tagsHtml += `
                            <span class="tag tag-${tag.replace(' ', '-')}">
                                ${getTagIcon(tag)} ${tag}
                            </span>
                        `;
                    });
                    tagsHtml += '</div>';
                    
                    resultElement.innerHTML = `
                        <div class="alert alert-success">
                            <strong>Classification complete!</strong><br>
                            This email has been tagged with:${tagsHtml}
                        </div>
                    `;
                    
                    // Update tags in the email list item
                    const emailItem = document.querySelectorAll('.email-item')[currentEmailId];
                    let tagsElement = emailItem.querySelector('.email-tags');
                    if (!tagsElement) {
                        tagsElement = document.createElement('div');
                        tagsElement.className = 'email-tags';
                        emailItem.appendChild(tagsElement);
                    }
                    tagsElement.innerHTML = tagsHtml;
                } else {
                    resultElement.innerHTML = `
                        <div class="alert alert-info">
                            <strong>Classification complete!</strong><br>
                            No relevant tags found for this email.
                        </div>
                    `;
                }
            } else {
                resultElement.innerHTML = `
                    <div class="alert alert-danger">
                        <strong>Error:</strong> ${data.message || 'Failed to classify email.'}
                    </div>
                `;
            }
        })
        .catch(error => {
            resultElement.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error:</strong> ${error.message}
                </div>
            `;
        });
    }, 1500); // Simulate network delay
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
document.getElementById('chat-input-field').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        sendChatMessage();
    }
});

// Column Resize Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get column elements
    const sidebarCol = document.getElementById('sidebar-col');
    const mainContentCol = document.getElementById('main-content-col');
    const emailListCol = document.getElementById('email-list-col');
    const emailDetailsCol = document.getElementById('email-details-col');
    const chatCol = document.getElementById('chat-col');
    
    // Get resize handle elements
    const sidebarResize = document.getElementById('sidebar-resize');
    const emailListResize = document.getElementById('email-list-resize');
    const emailDetailsResize = document.getElementById('email-details-resize');
    
    // Variables for tracking resize state
    let isResizing = false;
    let currentResizer = null;
    let initialWidth = 0;
    let initialX = 0;
    let initialTotal = 0;
    
    // Initialize column widths with explicit percentage values
    const setInitialWidths = () => {
        // Set main sections (sidebar and content)
        if (!sidebarCol.style.width) sidebarCol.style.width = '25%';
        if (!mainContentCol.style.width) mainContentCol.style.width = '75%';
        
        // Set content subsections
        if (!emailListCol.style.width) emailListCol.style.width = '41.67%'; // 5/12 of content
        if (!emailDetailsCol.style.width) emailDetailsCol.style.width = '33.33%'; // 4/12 of content
        if (!chatCol.style.width) chatCol.style.width = '25%'; // 3/12 of content
    };
    
    setInitialWidths();
    
    // Start resize process
    function startResize(e) {
        e.preventDefault();
        isResizing = true;
        
        // Determine which resizer was clicked
        if (e.target === sidebarResize) {
            currentResizer = 'sidebar';
            initialWidth = sidebarCol.offsetWidth;
            // We're resizing the main sidebar vs content split
            initialTotal = sidebarCol.parentElement.offsetWidth;
        } else if (e.target === emailListResize) {
            currentResizer = 'emailList';
            initialWidth = emailListCol.offsetWidth;
            // We're working within the content pane
            initialTotal = emailListCol.parentElement.offsetWidth;
        } else if (e.target === emailDetailsResize) {
            currentResizer = 'emailDetails';
            initialWidth = emailDetailsCol.offsetWidth;
            // We're working within the content pane
            initialTotal = emailDetailsCol.parentElement.offsetWidth;
        }
        
        initialX = e.clientX;
        
        // Add visual feedback
        e.target.classList.add('active');
        document.body.style.cursor = 'col-resize';
        document.body.style.userSelect = 'none';
        
        // Add event listeners for resize process
        document.addEventListener('mousemove', resize);
        document.addEventListener('mouseup', stopResize);
        
        // Log initial info
        console.log(`Starting resize: ${currentResizer}`, {
            initialWidth,
            initialTotal,
            initialX
        });
    }
    
    // Handle resize during mouse movement
    function resize(e) {
        if (!isResizing) return;
        
        const deltaX = e.clientX - initialX;
        const newWidth = initialWidth + deltaX;
        const newPercent = (newWidth / initialTotal) * 100;
        
        // Apply constraints and resize based on which element is being resized
        if (currentResizer === 'sidebar') {
            // Limit sidebar width between 15% and 40%
            if (newPercent >= 15 && newPercent <= 40) {
                sidebarCol.style.width = `${newPercent}%`;
                mainContentCol.style.width = `${100 - newPercent}%`;
                console.log(`Sidebar resize: ${newPercent.toFixed(2)}%`);
            }
        } else if (currentResizer === 'emailList') {
            // Limit email list width between 20% and 60%
            if (newPercent >= 20 && newPercent <= 60) {
                emailListCol.style.width = `${newPercent}%`;
                
                // Adjust the other columns to maintain 100% total
                const remainingWidth = 100 - newPercent;
                const detailsRatio = emailDetailsCol.offsetWidth / (emailDetailsCol.offsetWidth + chatCol.offsetWidth);
                
                const newDetailsWidth = remainingWidth * detailsRatio;
                const newChatWidth = remainingWidth - newDetailsWidth;
                
                emailDetailsCol.style.width = `${newDetailsWidth}%`;
                chatCol.style.width = `${newChatWidth}%`;
                
                console.log(`Email list resize: ${newPercent.toFixed(2)}%`);
            }
        } else if (currentResizer === 'emailDetails') {
            // Limit email details width between 20% and 60%
            if (newPercent >= 20 && newPercent <= 60) {
                emailDetailsCol.style.width = `${newPercent}%`;
                
                // Adjust chat column to maintain 100% total
                // Email list remains the same
                const emailListWidth = parseFloat(emailListCol.style.width);
                const newChatWidth = 100 - emailListWidth - newPercent;
                
                // Make sure chat column isn't too small
                if (newChatWidth >= 15) {
                    chatCol.style.width = `${newChatWidth}%`;
                    console.log(`Email details resize: ${newPercent.toFixed(2)}%`);
                }
            }
        }
    }
    
    // End resize process
    function stopResize() {
        if (!isResizing) return;
        
        isResizing = false;
        
        // Remove visual feedback
        document.querySelectorAll('.resize-handle').forEach(handle => {
            handle.classList.remove('active');
        });
        
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        
        // Remove event listeners
        document.removeEventListener('mousemove', resize);
        document.removeEventListener('mouseup', stopResize);
        
        console.log('Resize complete');
    }
    
    // Attach event listeners to resize handles
    if (sidebarResize) {
        sidebarResize.addEventListener('mousedown', startResize);
    } else {
        console.error('Sidebar resize handle not found');
    }
    
    if (emailListResize) {
        emailListResize.addEventListener('mousedown', startResize);
    } else {
        console.error('Email list resize handle not found');
    }
    
    if (emailDetailsResize) {
        emailDetailsResize.addEventListener('mousedown', startResize);
    } else {
        console.error('Email details resize handle not found');
    }
    
    // Add window resize handler to maintain relative proportions
    window.addEventListener('resize', function() {
        console.log('Window resized, maintaining column proportions');
    });
    
    // Log that initialization is complete
    console.log('Resize handlers initialized');
});

// Add these category management functions 
function initCategoryManagement() {
    const addButton = document.getElementById('add-category-btn');
    const categoryInput = document.getElementById('category-input');
    const categoryShowcase = document.getElementById('category-showcase');
    
    // Setup event listeners
    addButton.addEventListener('click', addCategory);
    categoryInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            addCategory();
        }
    });
    
    // Setup delete button listeners for existing categories
    setupDeleteButtons();
    
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
        
        // Add icon based on category name
        let iconHtml = '';
        if (categoryName === 'networking') {
            iconHtml = '<i class="fas fa-network-wired text-warning"></i>';
        } else if (categoryName === 'internship') {
            iconHtml = '<i class="fas fa-briefcase text-primary"></i>';
        } else if (categoryName === 'club events') {
            iconHtml = '<i class="fas fa-calendar-alt text-success"></i>';
        } else {
            iconHtml = '<i class="fas fa-tag"></i>';
        }
        
        categoryBadge.innerHTML = `
            ${iconHtml}
            ${categoryName}
            <button class="delete-category" data-category="${categoryName}">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add to showcase
        categoryShowcase.appendChild(categoryBadge);
        
        // Clear input
        categoryInput.value = '';
        
        // Add delete listener to new badge
        setupDeleteButtons();
        
        // Save to backend
        saveCategoryToBackend(categoryName);
    }
    
    function setupDeleteButtons() {
        document.querySelectorAll('.delete-category').forEach(button => {
            button.addEventListener('click', function() {
                const category = this.getAttribute('data-category');
                this.parentElement.remove();
                deleteCategoryFromBackend(category);
            });
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
        fetch('/delete-category', {
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
                updateSidebarKeywords(data.keywords);
            } else {
                showNotification('Failed to remove category', 'error');
            }
        })
        .catch(error => {
            console.error('Error removing category:', error);
            showNotification('Error removing category', 'error');
        });
    }
    
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
            }, 300);
        }, 3000);
    }
    
    // Add this new function after the previous two
    function updateSidebarKeywords(keywords) {
        const keywordFoldersContainer = document.querySelector('.sidebar .section-header + div').parentElement;
        const sectionHeader = keywordFoldersContainer.querySelector('.section-header');
        
        // Clear existing keyword folders
        const existingFolders = keywordFoldersContainer.querySelectorAll('.folder:not(:first-child):not(:last-child)');
        existingFolders.forEach(folder => folder.remove());
        
        // Add new folders based on keywords
        let folderHTML = '';
        keywords.forEach(keyword => {
            let iconClass = 'fa-tag';
            let colorClass = '';
            
            if (keyword === 'networking') {
                iconClass = 'fa-network-wired';
                colorClass = 'text-warning';
            } else if (keyword === 'internship') {
                iconClass = 'fa-briefcase';
                colorClass = 'text-primary';
            } else if (keyword === 'club events') {
                iconClass = 'fa-calendar-alt';
                colorClass = 'text-success';
            }
            
            folderHTML += `
                <div class="folder">
                    <span>
                        <i class="fas ${iconClass} ${colorClass}"></i>
                        ${keyword.charAt(0).toUpperCase() + keyword.slice(1)}
                    </span>
                    <span class="folder-count">0</span>
                </div>
            `;
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
