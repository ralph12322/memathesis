import React, { useState } from 'react';

const App = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [chineseText, setChineseText] = useState('');
  const [translatedText, setTranslatedText] = useState('');
  const [audioUrl, setAudioUrl] = useState('');
  const [sourceLanguage, setSourceLanguage] = useState('zh');
  const [targetLanguage, setTargetLanguage] = useState('en');

  const handleRecord = async () => {
    setIsRecording(true);
    try {
      const response = await fetch('http://localhost:5000/record', {
        method: 'POST',
      });

      const data = await response.json();
      if (data.speech_text) {
        setChineseText(data.speech_text);
      } else {
        console.error('Error:', data.error);
      }
    } catch (error) {
      console.error('Error recording:', error);
    } finally {
      setIsRecording(false);
    }
  };

  const handleTranslate = async () => {
    try {
      // Set the languages before translation
      await fetch('http://localhost:5000/set_language', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ source: sourceLanguage, target: targetLanguage }),
      });

      const response = await fetch('http://localhost:5000/translate', {
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
              <source src={`http://localhost:5000${audioUrl}`} type="audio/mp3" />
              Your browser does not support the audio element.
            </audio>
          </div>
        )}
      </div>
    </div>
  );
};

export default App;
