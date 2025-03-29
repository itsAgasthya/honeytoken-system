/**
 * Honeytoken UEBA System
 * Settings Page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the settings page
    initSettings();
    
    // Set up event listeners for forms
    setupFormSubmissions();
    
    // Set up UI interactions
    setupUiInteractions();
});

/**
 * Initialize settings page
 */
function initSettings() {
    console.log('Initializing settings page...');
    
    // Show toast notification for demo purposes
    showToast('Settings page loaded successfully', 'info');
    
    // Load settings from API if needed
    // In a real implementation, this would fetch actual settings from the backend
}

/**
 * Set up form submission handlers
 */
function setupFormSubmissions() {
    // General Settings Form
    const generalSettingsForm = document.getElementById('generalSettingsForm');
    if (generalSettingsForm) {
        generalSettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                systemName: document.getElementById('systemName').value,
                apiKey: document.getElementById('apiKey').value,
                loggingLevel: document.getElementById('loggingLevel').value,
                enableDebug: document.getElementById('enableDebug').checked
            };
            
            console.log('General settings submitted:', formData);
            saveSettings('general', formData);
        });
    }
    
    // Honeytoken Settings Form
    const honeytokenSettingsForm = document.getElementById('honeytokenSettingsForm');
    if (honeytokenSettingsForm) {
        honeytokenSettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                honeytokenPath: document.getElementById('honeytokenPath').value,
                defaultSensitivity: document.getElementById('defaultSensitivity').value,
                autoRegenerate: document.getElementById('autoRegenerate').checked
            };
            
            console.log('Honeytoken settings submitted:', formData);
            saveSettings('honeytoken', formData);
        });
    }
    
    // Alert Settings Form
    const alertSettingsForm = document.getElementById('alertSettingsForm');
    if (alertSettingsForm) {
        alertSettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                alertRetention: document.getElementById('alertRetention').value,
                notifications: {
                    email: document.getElementById('emailNotification').checked,
                    sms: document.getElementById('smsNotification').checked,
                    slack: document.getElementById('slackNotification').checked
                },
                emailRecipients: document.getElementById('emailRecipients').value
            };
            
            console.log('Alert settings submitted:', formData);
            saveSettings('alerts', formData);
        });
    }
    
    // UEBA Settings Form
    const uebaSettingsForm = document.getElementById('uebaSettingsForm');
    if (uebaSettingsForm) {
        uebaSettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                anomalyThreshold: document.getElementById('anomalyThreshold').value,
                baselinePeriod: document.getElementById('baselinePeriod').value,
                modelUpdateFrequency: document.getElementById('modelUpdateFrequency').value
            };
            
            console.log('UEBA settings submitted:', formData);
            saveSettings('ueba', formData);
        });
    }
    
    // User Settings Form
    const userSettingsForm = document.getElementById('userSettingsForm');
    if (userSettingsForm) {
        userSettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                userDataSource: document.getElementById('userDataSource').value,
                monitorAllUsers: document.getElementById('monitorAllUsers').checked,
                highRiskThreshold: document.getElementById('highRiskThreshold').value
            };
            
            console.log('User settings submitted:', formData);
            saveSettings('users', formData);
        });
    }
}

/**
 * Set up UI interactions
 */
function setupUiInteractions() {
    // Regenerate API Key button
    const regenerateApiKeyBtn = document.getElementById('regenerateApiKey');
    if (regenerateApiKeyBtn) {
        regenerateApiKeyBtn.addEventListener('click', function() {
            const apiKeyInput = document.getElementById('apiKey');
            // Generate a random API key for demo purposes
            const newApiKey = 'honeytoken_api_' + generateRandomString(16);
            apiKeyInput.value = newApiKey;
            showToast('API key regenerated', 'success');
        });
    }
    
    // Anomaly threshold slider
    const anomalyThresholdSlider = document.getElementById('anomalyThreshold');
    const anomalyThresholdValue = document.getElementById('anomalyThresholdValue');
    if (anomalyThresholdSlider && anomalyThresholdValue) {
        anomalyThresholdSlider.addEventListener('input', function() {
            anomalyThresholdValue.textContent = this.value;
        });
    }
    
    // Backup Database button
    const backupDatabaseBtn = document.getElementById('backupDatabase');
    if (backupDatabaseBtn) {
        backupDatabaseBtn.addEventListener('click', function() {
            showToast('Database backup started', 'info');
            setTimeout(() => {
                showToast('Database backup completed successfully', 'success');
            }, 3000);
        });
    }
    
    // Schedule Backup button
    const scheduleBackupBtn = document.getElementById('scheduleBackup');
    if (scheduleBackupBtn) {
        scheduleBackupBtn.addEventListener('click', function() {
            alert('Backup Scheduling Dialog would appear here in a real implementation');
        });
    }
    
    // Backup Configuration button
    const backupConfigBtn = document.getElementById('backupConfig');
    if (backupConfigBtn) {
        backupConfigBtn.addEventListener('click', function() {
            showToast('Preparing configuration for download', 'info');
            setTimeout(() => {
                showToast('Configuration file ready for download', 'success');
                // In a real implementation, this would trigger a file download
            }, 1500);
        });
    }
    
    // Restore button
    const restoreBackupBtn = document.getElementById('restoreBackup');
    if (restoreBackupBtn) {
        restoreBackupBtn.addEventListener('click', function() {
            const restoreFile = document.getElementById('restoreFile');
            if (restoreFile && restoreFile.files.length > 0) {
                showToast('Restore process started', 'info');
                setTimeout(() => {
                    showToast('System restored successfully', 'success');
                }, 3000);
            } else {
                showToast('Please select a backup file', 'error');
            }
        });
    }
}

/**
 * Save settings to the server
 * In a demo implementation, this just shows a success notification
 */
function saveSettings(section, data) {
    // Here you would normally make an API call to save the settings
    console.log(`Saving ${section} settings:`, data);
    
    // Simulate API call delay
    showToast('Saving settings...', 'info');
    
    setTimeout(() => {
        showToast('Settings saved successfully', 'success');
    }, 1500);
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Remove any existing toasts
    const existingToasts = document.getElementsByClassName('toast-container');
    if (existingToasts.length > 0) {
        existingToasts[0].remove();
    }
    
    // Create toast container if it doesn't exist
    let toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
    document.body.appendChild(toastContainer);
    
    // Create toast element
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${getToastBackground(type)} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    // Create toast content
    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    // Add toast to container
    toastContainer.appendChild(toastEl);
    
    // Initialize toast with Bootstrap
    const toast = new bootstrap.Toast(toastEl, {
        animation: true,
        autohide: true,
        delay: 3000
    });
    
    // Show toast
    toast.show();
}

/**
 * Map toast type to Bootstrap background class
 */
function getToastBackground(type) {
    switch (type) {
        case 'success':
            return 'success';
        case 'error':
            return 'danger';
        case 'warning':
            return 'warning';
        case 'info':
        default:
            return 'primary';
    }
}

/**
 * Generate a random string of specified length
 */
function generateRandomString(length = 10) {
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    
    for (let i = 0; i < length; i++) {
        result += characters.charAt(Math.floor(Math.random() * characters.length));
    }
    
    return result;
} 