from flask import Flask, request, jsonify
import keyboard
import speech_recognition as sr
import os
from transformers import AutoTokenizer, MarianMTModel
from gtts import gTTS
import tempfile
import shutil

# Initialize Flask app
app = Flask(__name__)

# Initialize speech recognizer
recognizer = sr.Recognizer()

# Load the translation model
src = "en"  
trg = "zh" 

model_name = f"Helsinki-NLP/opus-mt-{src}-{trg}"
model = MarianMTModel.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

def translate_to_english(text):
    batch = tokenizer([text], return_tensors="pt")
    generated_ids = model.generate(**batch)
    return tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

# Initialize variable for recognized speech text
speech_audio = None

@app.route("/record_audio", methods=["POST"])
def record_audio():
    global speech_audio
    speech_audio = None  # Reset speech_audio

    if request.json and "action" in request.json and request.json["action"] == "start":
        print("Recording... Please speak now.")
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        try:
            # Convert speech to text (Chinese)
            speech_audio = recognizer.recognize_google(audio, language="zh-CN")
            print("You said (in Chinese):", speech_audio)
        except sr.UnknownValueError:
            print("Could not understand the audio.")
            speech_audio = None
        except sr.RequestError as e:
            print(f"Error with speech recognition service: {e}")
            speech_audio = None

    return jsonify({"message": "Recording completed, now translating to English."})


@app.route("/translate", methods=["GET"])
def translate():
    if speech_audio:
        # Translate to English
        translated_text = translate_to_english(speech_audio)
        print("Translated to English:", translated_text)

        # Convert translated text to speech
        tts = gTTS(text=translated_text, lang='en')
        
        # Save audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            tts.save(temp_file.name)
            temp_file_path = temp_file.name
        
        # Send the file path as the response
        return jsonify({
            "translated_text": translated_text,
            "audio_file": temp_file_path
        })
    else:
        return jsonify({"error": "No speech audio found. Please record audio first."}), 400


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
