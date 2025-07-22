// Main JavaScript for Constituency Bursary System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const fileName = file.name;
                const fileSize = (file.size / 1024 / 1024).toFixed(2);
                
                // Update file name display if exists
                const fileNameDisplay = document.getElementById(input.id + '_filename');
                if (fileNameDisplay) {
                    fileNameDisplay.textContent = `${fileName} (${fileSize} MB)`;
                }

                // Show image preview for image files
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const preview = document.getElementById(input.id + '_preview');
                        if (preview) {
                            preview.src = e.target.result;
                            preview.style.display = 'block';
                        }
                    };
                    reader.readAsDataURL(file);
                }
            }
        });
    });

    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Dynamic form fields based on status selection (for review form)
    const statusRadios = document.querySelectorAll('input[name="status"]');
    statusRadios.forEach(function(radio) {
        radio.addEventListener('change', function() {
            const approvedAmountDiv = document.getElementById('approved_amount_div');
            const rejectionReasonDiv = document.getElementById('rejection_reason_div');
            
            if (this.value === 'approved') {
                approvedAmountDiv.classList.remove('d-none');
                rejectionReasonDiv.classList.add('d-none');
            } else if (this.value === 'rejected') {
                approvedAmountDiv.classList.add('d-none');
                rejectionReasonDiv.classList.remove('d-none');
            } else {
                approvedAmountDiv.classList.add('d-none');
                rejectionReasonDiv.classList.add('d-none');
            }
        });
    });

    // Phone number formatting
    const phoneInputs = document.querySelectorAll('input[type="tel"]');
    phoneInputs.forEach(function(input) {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value.startsWith('254')) {
                value = '+' + value;
            } else if (value.startsWith('0')) {
                value = '+254' + value.substring(1);
            }
            e.target.value = value;
        });
    });

    // Confirmation dialogs
    const deleteButtons = document.querySelectorAll('.delete-confirm');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });

    // Print functionality
    const printButtons = document.querySelectorAll('.print-button');
    printButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            window.print();
        });
    });

    // Table row click navigation
    const clickableRows = document.querySelectorAll('tr[data-href]');
    clickableRows.forEach(function(row) {
        row.addEventListener('click', function() {
            window.location.href = this.dataset.href;
        });
        row.style.cursor = 'pointer';
    });

    // Search functionality
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const tableRows = document.querySelectorAll('tbody tr');
            
            tableRows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Character counter for textareas
    const textareas = document.querySelectorAll('textarea[maxlength]');
    textareas.forEach(function(textarea) {
        const maxLength = textarea.getAttribute('maxlength');
        const counter = document.createElement('small');
        counter.className = 'text-muted';
        counter.textContent = `0 / ${maxLength} characters`;
        textarea.parentNode.appendChild(counter);
        
        textarea.addEventListener('input', function() {
            const currentLength = this.value.length;
            counter.textContent = `${currentLength} / ${maxLength} characters`;
            
            if (currentLength > maxLength * 0.9) {
                counter.classList.add('text-danger');
            } else {
                counter.classList.remove('text-danger');
            }
        });
    });

    // Loading spinner for forms
    const formsWithSpinner = document.querySelectorAll('form[data-loading]');
    formsWithSpinner.forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';
            }
        });
    });

    // Copy to clipboard functionality
    const copyButtons = document.querySelectorAll('.copy-to-clipboard');
    copyButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                const text = targetElement.textContent || targetElement.value;
                navigator.clipboard.writeText(text).then(function() {
                    const originalText = button.innerHTML;
                    button.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    button.classList.add('btn-success');
                    
                    setTimeout(function() {
                        button.innerHTML = originalText;
                        button.classList.remove('btn-success');
                    }, 2000);
                });
            }
        });
    });

    // Toggle password visibility
    const passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(function(toggle) {
        toggle.addEventListener('click', function() {
            const targetId = this.dataset.target;
            const passwordInput = document.getElementById(targetId);
            const icon = this.querySelector('i');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });

    // Dynamic institution selection
    // const educationLevelSelect = document.getElementById('id_education_level');
    // const institutionSelect = document.getElementById('id_institution');
    
    if (educationLevelSelect && institutionSelect) {
        educationLevelSelect.addEventListener('change', function() {
            const selectedLevel = this.value;
            
            // This would typically make an AJAX call to fetch institutions
            // For now, we'll just show a loading message
            // institutionSelect.innerHTML = '<option value="">Loading institutions...</option>';
            // institutionSelect.disabled = true;
            
            // Simulate AJAX call
            setTimeout(function() {
                // In production, this would be replaced with actual AJAX response
                // institutionSelect.innerHTML = '<option value="">Select Institution</option>';
                // institutionSelect.disabled = false;
            }, 500);
        });
    }

    // Format currency inputs
    const currencyInputs = document.querySelectorAll('.currency-input');
    currencyInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            const value = parseFloat(this.value);
            if (!isNaN(value)) {
                this.value = value.toFixed(2);
            }
        });
    });

    // Session timeout warning
    let warningTimer;
    let timeoutTimer;
    const sessionTimeout = 30 * 60 * 1000; // 30 minutes
    const warningTime = 5 * 60 * 1000; // 5 minutes before timeout
    
    function resetTimers() {
        clearTimeout(warningTimer);
        clearTimeout(timeoutTimer);
        
        warningTimer = setTimeout(function() {
            if (confirm('Your session will expire in 5 minutes. Do you want to continue?')) {
                // Make a request to refresh the session
                fetch('/accounts/keep-alive/');
            }
        }, sessionTimeout - warningTime);
        
        timeoutTimer = setTimeout(function() {
            alert('Your session has expired. Please log in again.');
            window.location.href = '/accounts/login/';
        }, sessionTimeout);
    }
    
    // Reset timers on user activity
    ['mousedown', 'keypress', 'scroll', 'touchstart'].forEach(function(event) {
        document.addEventListener(event, resetTimers, true);
    });
    
    resetTimers();
});

// Utility functions
function formatPhoneNumber(phoneNumber) {
    // Format phone number for display
    const cleaned = phoneNumber.replace(/\D/g, '');
    if (cleaned.startsWith('254')) {
        return '+' + cleaned.substring(0, 3) + ' ' + cleaned.substring(3, 6) + ' ' + cleaned.substring(6);
    }
    return phoneNumber;
}

function formatCurrency(amount) {
    // Format currency with thousands separator
    return 'KES ' + parseFloat(amount).toLocaleString('en-KE', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function calculateAge(dateOfBirth) {
    const today = new Date();
    const birthDate = new Date(dateOfBirth);
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
    }
    
    return age;
}