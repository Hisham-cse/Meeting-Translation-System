document.addEventListener('DOMContentLoaded', function() {
    const startButton = document.getElementById('startButton');
    const stopButton = document.getElementById('stopButton');
    const originalText = document.getElementById('originalText');
    const translatedText = document.getElementById('translatedText');
    const sourceLang = document.getElementById('sourceLang');
    const targetLang = document.getElementById('targetLang');

    let recognition = null;
    let isRecording = false;

    if ('webkitSpeechRecognition' in window) {
        recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
    } else {
        startButton.disabled = true;
        alert('Speech recognition is not supported in this browser.');
    }

    function startRecording() {
        if (recognition) {
            recognition.lang = sourceLang.value;
            recognition.start();
            isRecording = true;
            startButton.disabled = true;
            stopButton.disabled = false;
            startButton.classList.add('recording');
        }
    }

    function stopRecording() {
        if (recognition) {
            recognition.stop();
            isRecording = false;
            startButton.disabled = false;
            stopButton.disabled = true;
            startButton.classList.remove('recording');
        }
    }

    async function translateText(text) {
        try {
            const response = await fetch('/translate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    sourceLang: sourceLang.value,
                    targetLang: targetLang.value
                })
            });

            const data = await response.json();
            return data.translation;
        } catch (error) {
            console.error('Translation error:', error);
            return 'Translation error occurred';
        }
    }

    if (recognition) {
        recognition.onresult = async function(event) {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                const transcript = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalTranscript += transcript;
                    const translation = await translateText(transcript);
                    translatedText.innerHTML += `<p>${translation}</p>`;
                } else {
                    interimTranscript += transcript;
                }
            }

            originalText.innerHTML = `<p>${finalTranscript}</p><i>${interimTranscript}</i>`;
        };

        recognition.onerror = function(event) {
            console.error('Speech recognition error:', event.error);
            stopRecording();
        };
    }

    startButton.addEventListener('click', startRecording);
    stopButton.addEventListener('click', stopRecording);
});
