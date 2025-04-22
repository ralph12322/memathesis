import React, { useState } from 'react';

const App = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [chineseText, setChineseText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [sourceLanguage, setSourceLanguage] = useState('zh');
  const [targetLanguage, setTargetLanguage] = useState('en');

  const handleRecord = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    const chunks = [];
  
    mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
    mediaRecorder.onstop = async () => {
      const blob = new Blob(audioChunks, { type: 'audio/wav' });
      const formData = new FormData();
      formData.append('audio', blob, 'recording.wav');
    
      try {
        const res = await fetch(`${API_BASE}/record`, {
          method: 'POST',
          body: formData,
        });
        const data = await res.json();
        console.log("Transcription:", data);
      } catch (err) {
        console.error("Error recording:", err);
      }
    };
    
  
    mediaRecorder.start();
    setTimeout(() => mediaRecorder.stop(), 5000); // Record 5 seconds
  };
  
  

  const handleTranslate = async () => {
    try {
      // Set the languages before translation
      await fetch('https://memathesis.onrender.com/set_language', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ source: sourceLanguage, target: targetLanguage }),
      });

      const response = await fetch('https://memathesis.onrender.com/translate', {
        method: 'GET',
      });

      const data = await response.json();
      if (data.audio_file) {
        setTranslatedText(data.translated_text);
        setAudioUrl(data.audio_file);
      } else {
        console.error('Error:', data.error);
      }
    } catch (error) {
      console.error('Error translating:', error);
    }
  };

  return (
    <div className="App">
      <h1>Speech Translator</h1>

      <div>
        <label>
          Source Language:
          <select
            value={sourceLanguage}
            onChange={(e) => setSourceLanguage(e.target.value)}
          >
            <option value="zh">Chinese</option>
            <option value="en">English</option>
            {/* Add more languages as needed */}
          </select>
        </label>
      </div>

      <div>
        <label>
          Target Language:
          <select
            value={targetLanguage}
            onChange={(e) => setTargetLanguage(e.target.value)}
          >
            <option value="zh">Chinese</option>
            <option value="en">English</option>
            {/* Add more languages as needed */}
          </select>
        </label>
      </div>

      <div>
        <button onClick={handleRecord} disabled={isRecording}>
          {isRecording ? 'Recording...' : 'Record Audio'}
        </button>
      </div>

      <div>
        {chineseText && <p><strong>Original ({sourceLanguage}):</strong> {chineseText}</p>}
      </div>

      <div>
        <button onClick={handleTranslate} disabled={!chineseText}>
          Translate
        </button>
      </div>

      <div>
        {translatedText && <p><strong>Translated ({targetLanguage}):</strong> {translatedText}</p>}
      </div>

      <div>
        {audioUrl && (
          <div>
            <p><strong>Translated Speech:</strong></p>
            <audio controls>
              <source src={`https://memathesis.onrender.com${audioUrl}`} type="audio/mp3" />
              Your browser does not support the audio element.
            </audio>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
