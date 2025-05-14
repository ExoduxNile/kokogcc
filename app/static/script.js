document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    function openTab(tabId) {
        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(tab => {
            tab.classList.remove('active');
        });
        
        // Deactivate all tab buttons
        document.querySelectorAll('.tab-button').forEach(button => {
            button.classList.remove('active');
        });
        
        // Activate selected tab
        document.getElementById(tabId).classList.add('active');
        event.currentTarget.classList.add('active');
    }
    
    // Speed slider value display
    const speedSlider = document.getElementById('speed');
    const speedValue = document.getElementById('speed-value');
    speedSlider.addEventListener('input', function() {
        speedValue.textContent = this.value;
    });
    
    const fileSpeedSlider = document.getElementById('file-speed');
    const fileSpeedValue = document.getElementById('file-speed-value');
    fileSpeedSlider.addEventListener('input', function() {
        fileSpeedValue.textContent = this.value;
    });
    
    // Text form submission
    const textForm = document.getElementById('text-form');
    textForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(textForm);
        const text = formData.get('text');
        const voice = formData.get('voice');
        const speed = formData.get('speed');
        const lang = formData.get('lang');
        
        // Show loading state
        showLoading('Processing text...');
        
        try {
            const response = await fetch('/process-text/', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                },
                body: formData
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                // Display audio player
                const audioPlayer = document.getElementById('text-audio');
                audioPlayer.src = result.audio_url;
                
                // Set download link
                const downloadLink = document.getElementById('text-download');
                downloadLink.href = result.audio_url;
                
                // Show result area
                document.getElementById('text-result').classList.remove('hidden');
                
                showSuccess('Text converted successfully!');
            } else {
                showError(result.message);
            }
        } catch (error) {
            showError('An error occurred while processing your request.');
            console.error('Error:', error);
        } finally {
            hideLoading();
        }
    });
    
    // File form submission
    const fileForm = document.getElementById('file-form');
    fileForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(fileForm);
        const file = formData.get('file');
        
        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
            showError('File size must be less than 10MB');
            return;
        }
        
        // Show loading state
        showLoading('Processing file...');
        
        try {
            const response = await fetch('/process-file/', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.status === 'success') {
                const fileContainer = document.getElementById('file-audio-container');
                const downloadLink = document.getElementById('file-download');
                
                // Check if it's a zip file (chapter split)
                if (result.download_url.endsWith('.zip')) {
                    fileContainer.innerHTML = '<p>Your file has been split into chapters. Download the ZIP archive containing all audio files.</p>';
                    downloadLink.textContent = 'Download ZIP Archive';
                } else {
                    // It's a single audio file
                    fileContainer.innerHTML = '<audio controls></audio>';
                    const audioPlayer = fileContainer.querySelector('audio');
                    audioPlayer.src = result.download_url;
                    downloadLink.textContent = 'Download Audio';
                }
                
                downloadLink.href = result.download_url;
                document.getElementById('file-result').classList.remove('hidden');
                
                showSuccess('File converted successfully!');
            } else {
                showError(result.message);
            }
        } catch (error) {
            showError('An error occurred while processing your file.');
            console.error('Error:', error);
        } finally {
            hideLoading();
        }
    });
    
    // Helper functions for status messages
    function showLoading(message) {
        const statusElement = document.getElementById('status-message');
        statusElement.textContent = message;
        statusElement.classList.remove('hidden', 'error', 'success');
        
        document.getElementById('spinner').classList.remove('hidden');
    }
    
    function hideLoading() {
        document.getElementById('spinner').classList.add('hidden');
    }
    
    function showSuccess(message) {
        const statusElement = document.getElementById('status-message');
        statusElement.textContent = message;
        statusElement.classList.remove('hidden', 'error');
        statusElement.classList.add('success');
    }
    
    function showError(message) {
        const statusElement = document.getElementById('status-message');
        statusElement.textContent = message;
        statusElement.classList.remove('hidden', 'success');
        statusElement.classList.add('error');
    }
});
