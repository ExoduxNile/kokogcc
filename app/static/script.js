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
    
    // Audio element management
    let currentAudioBlobUrl = null;
    
    // Clean up previous audio URL
    function cleanupAudio() {
        if (currentAudioBlobUrl) {
            URL.revokeObjectURL(currentAudioBlobUrl);
            currentAudioBlobUrl = null;
        }
    }
    
    // Text form submission handler
    const textForm = document.getElementById('text-form');
    textForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        cleanupAudio(); // Clean up previous audio
        
        const formData = new FormData(textForm);
        const text = formData.get('text');
        
        if (!text || text.trim().length === 0) {
            showError('Please enter some text to convert');
            return;
        }
        
        showLoading('Processing text...');
        
        try {
            const response = await fetch('/process-text/', {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                },
                body: new URLSearchParams({
                    text: formData.get('text'),
                    voice: formData.get('voice'),
                    speed: formData.get('speed'),
                    lang: formData.get('lang')
                })
            });

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || `HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            // Fetch audio as blob to avoid range requests
            const audioResponse = await fetch(result.audio_url);
            if (!audioResponse.ok) {
                throw new Error('Failed to fetch audio file');
            }
            
            const audioBlob = await audioResponse.blob();
            currentAudioBlobUrl = URL.createObjectURL(audioBlob);
            
            // Get or create audio player
            let audioPlayer = document.getElementById('text-audio');
            if (!audioPlayer) {
                audioPlayer = document.createElement('audio');
                audioPlayer.id = 'text-audio';
                audioPlayer.controls = true;
                document.getElementById('text-result').prepend(audioPlayer);
            }
            
            // Configure audio player
            audioPlayer.src = currentAudioBlobUrl;
            audioPlayer.preload = 'auto';
            
            // Error handling
            audioPlayer.onerror = function() {
                console.error('Audio playback error:', this.error);
                showError('Failed to play audio. Please try downloading instead.');
            };
            
            // Set download link
            const downloadLink = document.getElementById('text-download');
            downloadLink.href = currentAudioBlobUrl;
            downloadLink.download = `tts-${formData.get('voice')}-${Date.now()}.mp3`;
            
            // Show result area
            document.getElementById('text-result').classList.remove('hidden');
            
            showSuccess('Text converted successfully!');
            
            // Attempt autoplay
            try {
                await audioPlayer.play();
            } catch (playError) {
                console.log('Autoplay prevented:', playError);
            }
        } catch (error) {
            console.error('Error:', error);
            showError(error.message || 'An error occurred while processing your request.');
        } finally {
            hideLoading();
        }
    });
    
    // File form submission
    const fileForm = document.getElementById('file-form');
    fileForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        cleanupAudio(); // Clean up previous audio
        
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
                    downloadLink.href = result.download_url;
                } else {
                    // For single audio file - use blob approach
                    const audioResponse = await fetch(result.download_url);
                    if (!audioResponse.ok) {
                        throw new Error('Failed to fetch audio file');
                    }
                    
                    const audioBlob = await audioResponse.blob();
                    currentAudioBlobUrl = URL.createObjectURL(audioBlob);
                    
                    fileContainer.innerHTML = '<audio controls id="file-audio"></audio>';
                    const audioPlayer = fileContainer.querySelector('audio');
                    audioPlayer.src = currentAudioBlobUrl;
                    audioPlayer.preload = 'auto';
                    
                    downloadLink.textContent = 'Download Audio';
                    downloadLink.href = currentAudioBlobUrl;
                    downloadLink.download = `tts-file-${Date.now()}.mp3`;
                }
                
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
