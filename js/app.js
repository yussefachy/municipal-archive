// Form validation and navigation functions

// Validate email format
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Validate password (minimum 6 characters)
function validatePassword(password) {
    return password.length >= 6;
}

// Show error message
function showError(input, message) {
    const formGroup = input.closest('.form-group');
    const errorDiv = formGroup.querySelector('.invalid-feedback') || document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    if (!formGroup.querySelector('.invalid-feedback')) {
        formGroup.appendChild(errorDiv);
    }
    input.classList.add('is-invalid');
}

// Clear error message
function clearError(input) {
    const formGroup = input.closest('.form-group');
    const errorDiv = formGroup.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
    input.classList.remove('is-invalid');
}

// Validate login form
function validateLoginForm(event) {
    event.preventDefault();
    const email = document.getElementById('email');
    const password = document.getElementById('password');
    let isValid = true;

    clearError(email);
    clearError(password);

    if (!email.value) {
        showError(email, 'Email is required');
        isValid = false;
    } else if (!validateEmail(email.value)) {
        showError(email, 'Please enter a valid email');
        isValid = false;
    }

    if (!password.value) {
        showError(password, 'Password is required');
        isValid = false;
    } else if (!validatePassword(password.value)) {
        showError(password, 'Password must be at least 6 characters');
        isValid = false;
    }

    if (isValid) {
        window.location.href = 'index.html';
    }
}

// Validate registration form
function validateRegistrationForm(event) {
    event.preventDefault();
    const name = document.getElementById('name');
    const email = document.getElementById('email');
    const password = document.getElementById('password');
    let isValid = true;

    clearError(name);
    clearError(email);
    clearError(password);

    if (!name.value) {
        showError(name, 'Name is required');
        isValid = false;
    }

    if (!email.value) {
        showError(email, 'Email is required');
        isValid = false;
    } else if (!validateEmail(email.value)) {
        showError(email, 'Please enter a valid email');
        isValid = false;
    }

    if (!password.value) {
        showError(password, 'Password is required');
        isValid = false;
    } else if (!validatePassword(password.value)) {
        showError(password, 'Password must be at least 6 characters');
        isValid = false;
    }

    if (isValid) {
        window.location.href = 'index.html';
    }
}

// Validate booking form
function validateBookingForm(event) {
    event.preventDefault();
    const date = document.getElementById('date');
    const notes = document.getElementById('notes');
    let isValid = true;

    clearError(date);
    clearError(notes);

    if (!date.value) {
        showError(date, 'Date is required');
        isValid = false;
    }

    if (isValid) {
        window.location.href = 'confirm.html';
    }
}

// Initialize form validation
document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const bookingForm = document.getElementById('bookingForm');

    if (loginForm) {
        loginForm.addEventListener('submit', validateLoginForm);
    }

    if (registerForm) {
        registerForm.addEventListener('submit', validateRegistrationForm);
    }

    if (bookingForm) {
        bookingForm.addEventListener('submit', validateBookingForm);
    }

    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.classList.remove('show');
            setTimeout(function() {
                message.remove();
            }, 150);
        }, 5000);
    });
}); 