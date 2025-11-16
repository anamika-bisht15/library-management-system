document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Delete book functionality
    const deleteButtons = document.querySelectorAll('.delete-book');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const bookId = this.getAttribute('data-book-id');
            const bookTitle = this.closest('tr').querySelector('td:nth-child(2)').textContent;
            
            if (confirm(`Are you sure you want to delete "${bookTitle}"?`)) {
                showLoading('Deleting book...');
                
                fetch(`/books/${bookId}/delete`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (data.success) {
                        this.closest('tr').remove();
                        showAlert('Book deleted successfully!', 'success');
                    } else {
                        showAlert('Failed to delete book!', 'danger');
                    }
                })
                .catch(error => {
                    hideLoading();
                    console.error('Error:', error);
                    showAlert('Error deleting book!', 'danger');
                });
            }
        });
    });

    // Borrow book form
    const borrowForm = document.getElementById('borrowForm');
    if (borrowForm) {
        borrowForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const resultDiv = document.getElementById('borrowResult');
            
            showLoading('Processing borrow request...');
            
            fetch('/borrow', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                if (data.success) {
                    resultDiv.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                    borrowForm.reset();
                    // Refresh the page after 2 seconds to update available books
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    resultDiv.innerHTML = `<div class="alert alert-danger">${data.message}</div>`;
                }
            })
            .catch(error => {
                hideLoading();
                console.error('Error:', error);
                resultDiv.innerHTML = `<div class="alert alert-danger">Error borrowing book!</div>`;
            });
        });
    }

    // Return book functionality
    const returnButtons = document.querySelectorAll('.return-book');
    returnButtons.forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            const bookId = this.getAttribute('data-book-id');
            const bookTitle = this.closest('tr').querySelector('td:first-child').textContent;
            
            if (confirm(`Return "${bookTitle}"?`)) {
                showLoading('Returning book...');
                
                const formData = new FormData();
                formData.append('user_id', userId);
                formData.append('book_id', bookId);
                
                fetch('/return', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (data.success) {
                        showAlert(data.message, 'success');
                        this.closest('tr').remove();
                        // Update borrowed books count
                        const badge = document.querySelector('.badge.bg-info');
                        if (badge) {
                            const currentCount = parseInt(badge.textContent);
                            badge.textContent = currentCount - 1;
                        }
                    } else {
                        showAlert(data.message, 'danger');
                    }
                })
                .catch(error => {
                    hideLoading();
                    console.error('Error:', error);
                    showAlert('Error returning book!', 'danger');
                });
            }
        });
    });

    // Send notifications functionality - UPDATED
    // Send notifications functionality - UPDATED WITH BETTER UI
const sendNotificationsBtn = document.getElementById('sendNotificationsBtn');
if (sendNotificationsBtn) {
    sendNotificationsBtn.addEventListener('click', function() {
        const originalText = this.innerHTML;
        const resultDiv = document.getElementById('notificationResult');
        
        // Clear previous results
        resultDiv.innerHTML = '';
        
        // Show immediate loading state
        resultDiv.innerHTML = `
            <div class="card border-info">
                <div class="card-body">
                    <div class="text-center">
                        <div class="spinner-border text-primary mb-3" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <h5 class="text-info">Sending Notifications...</h5>
                        <p class="text-muted mb-0">Please wait while we send emails to users</p>
                    </div>
                </div>
            </div>
        `;
        
        // Update button to show loading state
        this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
        this.disabled = true;
        
        fetch('/admin/send-notifications')
            .then(response => response.json())
            .then(data => {
                // Restore button immediately
                this.innerHTML = originalText;
                this.disabled = false;
                
                if (data.success) {
                    const totalSent = data.results.overdue_notifications + data.results.reminder_notifications;
                    
                    const successMessage = `
                        <div class="card border-success">
                            <div class="card-header bg-success text-white">
                                <h5 class="mb-0"><i class="fas fa-check-circle me-2"></i>Notifications Sent Successfully!</h5>
                            </div>
                            <div class="card-body">
                                <div class="row text-center">
                                    <div class="col-md-6">
                                        <div class="border-end">
                                            <h2 class="text-danger">${data.results.overdue_notifications}</h2>
                                            <p class="text-muted mb-0">Overdue Notices</p>
                                        </div>
                                    </div>
                                    <div class="col-md-6">
                                        <h2 class="text-warning">${data.results.reminder_notifications}</h2>
                                        <p class="text-muted mb-0">Reminder Notices</p>
                                    </div>
                                </div>
                                <hr>
                                <div class="text-center">
                                    <h4 class="text-success">Total Emails Sent: ${totalSent}</h4>
                                    <p class="text-muted"><small>All notifications have been delivered successfully</small></p>
                                    <div class="mt-3">
                                        <i class="fas fa-envelope-circle-check fa-2x text-success"></i>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    resultDiv.innerHTML = successMessage;
                } else {
                    resultDiv.innerHTML = `
                        <div class="alert alert-danger">
                            <h5><i class="fas fa-exclamation-triangle me-2"></i>Failed to Send Notifications</h5>
                            <p class="mb-0">${data.message || 'An error occurred while sending notifications.'}</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                // Restore button
                this.innerHTML = originalText;
                this.disabled = false;
                
                console.error('Error:', error);
                resultDiv.innerHTML = `
                    <div class="alert alert-danger">
                        <h5><i class="fas fa-exclamation-triangle me-2"></i>Network Error</h5>
                        <p class="mb-0">Unable to connect to the server. Please check your internet connection and try again.</p>
                    </div>
                `;
            });
    });
}

// Add this to your existing script.js file - notifications functionality
function initializeNotifications() {
    const sendNotificationsBtn = document.getElementById('sendNotificationsBtn');
    const resultDiv = document.getElementById('notificationResult');

    if (sendNotificationsBtn && resultDiv) {
        console.log('Initializing notifications functionality');
        
        sendNotificationsBtn.addEventListener('click', function() {
            if (confirm('Send email notifications to users with overdue books?')) {
                const originalText = this.innerHTML;
                
                // Clear previous results
                resultDiv.innerHTML = '';
                
                // Show immediate loading state
                resultDiv.innerHTML = `
                    <div class="card border-info">
                        <div class="card-body">
                            <div class="text-center">
                                <div class="spinner-border text-primary mb-3" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <h5 class="text-info">Sending Notifications...</h5>
                                <p class="text-muted mb-0">Please wait while we send emails to users</p>
                            </div>
                        </div>
                    </div>
                `;
                
                // Update button to show loading state
                this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
                this.disabled = true;
                
                fetch('/admin/send-notifications')
                    .then(response => response.json())
                    .then(data => {
                        // Restore button immediately
                        this.innerHTML = originalText;
                        this.disabled = false;
                        
                        if (data.success) {
                            const totalSent = data.results.overdue_notifications + data.results.reminder_notifications;
                            
                            resultDiv.innerHTML = `
                                <div class="card border-success">
                                    <div class="card-header bg-success text-white">
                                        <h5 class="mb-0"><i class="fas fa-check-circle me-2"></i>Notifications Sent Successfully!</h5>
                                    </div>
                                    <div class="card-body">
                                        <div class="row text-center mb-3">
                                            <div class="col-md-6">
                                                <div class="border-end">
                                                    <h2 class="text-danger display-6">${data.results.overdue_notifications}</h2>
                                                    <p class="text-muted mb-0">Overdue Notices</p>
                                                </div>
                                            </div>
                                            <div class="col-md-6">
                                                <h2 class="text-warning display-6">${data.results.reminder_notifications}</h2>
                                                <p class="text-muted mb-0">Reminder Notices</p>
                                            </div>
                                        </div>
                                        <hr>
                                        <div class="text-center">
                                            <h4 class="text-success mb-3">Total Emails Sent: ${totalSent}</h4>
                                            <p class="text-muted"><small>${data.message}</small></p>
                                            <div class="mt-3">
                                                <i class="fas fa-envelope-circle-check fa-3x text-success"></i>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            `;
                        } else {
                            resultDiv.innerHTML = `
                                <div class="alert alert-danger">
                                    <h5><i class="fas fa-exclamation-triangle me-2"></i>Failed to Send Notifications</h5>
                                    <p class="mb-0">${data.message || 'An error occurred while sending notifications.'}</p>
                                </div>
                            `;
                        }
                    })
                    .catch(error => {
                        // Restore button
                        this.innerHTML = originalText;
                        this.disabled = false;
                        
                        console.error('Error:', error);
                        resultDiv.innerHTML = `
                            <div class="alert alert-danger">
                                <h5><i class="fas fa-exclamation-triangle me-2"></i>Network Error</h5>
                                <p class="mb-0">Unable to connect to the server. Please check your internet connection and try again.</p>
                            </div>
                        `;
                    });
            }
        });
    }
}

// Initialize notifications when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeNotifications();
});

    // Fine payment functionality
    const payFineButtons = document.querySelectorAll('.pay-fine');
    payFineButtons.forEach(button => {
        button.addEventListener('click', function() {
            const userId = this.getAttribute('data-user-id');
            const bookId = this.getAttribute('data-book-id');
            
            if (confirm('Mark this fine as paid?')) {
                showLoading('Processing payment...');
                
                fetch(`/users/${userId}/pay-fine/${bookId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (data.success) {
                        showAlert('Fine paid successfully!', 'success');
                        this.closest('tr').remove();
                        // Update total fine amount
                        const totalFineElement = document.querySelector('.alert h5 strong');
                        if (totalFineElement) {
                            // Reload the page for accurate total
                            setTimeout(() => {
                                window.location.reload();
                            }, 2000);
                        }
                    } else {
                        showAlert(data.message, 'danger');
                    }
                })
                .catch(error => {
                    hideLoading();
                    console.error('Error:', error);
                    showAlert('Error processing payment!', 'danger');
                });
            }
        });
    });

    // Search functionality with debounce
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.value.length >= 3 || this.value.length === 0) {
                    this.closest('form').submit();
                }
            }, 500);
        });
    }

    // Auto-refresh dashboard every 30 seconds
    if (window.location.pathname === '/') {
        setInterval(() => {
            fetch('/')
                .then(response => response.text())
                .then(html => {
                    console.log('Dashboard auto-refreshed');
                })
                .catch(error => console.error('Auto-refresh error:', error));
        }, 30000);
    }

    // Utility functions
    function showLoading(message = 'Loading...') {
        let loadingDiv = document.getElementById('loadingOverlay');
        if (!loadingDiv) {
            loadingDiv = document.createElement('div');
            loadingDiv.id = 'loadingOverlay';
            loadingDiv.className = 'loading-overlay';
            loadingDiv.innerHTML = `
                <div class="loading-spinner">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <div class="loading-message">${message}</div>
                </div>
            `;
            document.body.appendChild(loadingDiv);
        }
    }

    function hideLoading() {
        const loadingDiv = document.getElementById('loadingOverlay');
        if (loadingDiv) {
            loadingDiv.remove();
        }
    }

    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Add confirmation for form submissions
    const destructiveForms = document.querySelectorAll('form[data-confirm]');
    destructiveForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});