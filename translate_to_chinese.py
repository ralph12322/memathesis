from flask import Flask, request, jsonify, send_from_directory
import speech_recognition as sr
import os
from transformers import AutoTokenizer, MarianMTModel
from gtts import gTTS
import tempfile
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Directory to store the audio files
AUDIO_STORAGE_DIR = "audio_storage"
os.makedirs(AUDIO_STORAGE_DIR, exist_ok=True)

# Initialize speech recognizer
recognizer = sr.Recognizer()

# Global variables for language settings and model/tokenizer
src_language = "en"  # Default source language
trg_language = "zh"  # Default target language
model = None
tokenizer = None

@app.route("/set_language", methods=["POST"])
def set_language():
    global src_language, trg_language, model, tokenizer
    data = request.json
    src_language = data.get("source")
    trg_language = data.get("target")

    # Load the translation model based on selected languages
    model_name = f"Helsinki-NLP/opus-mt-{src_language}-{trg_language}"
    model = MarianMTModel.from_pretrained(model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    return jsonify({"message": "Languages set successfully!"})

# Store speech transcription
speech_text = None

def translate_to_target_language(text):
    # Ensure model and tokenizer are loaded before translating
    if model is None or tokenizer is None:
        raise ValueError("Translation model and tokenizer are not loaded.")

    batch = tokenizer([text], return_tensors="pt")
    generated_ids = model.generate(**batch)
    return tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

@app.route("/record", methods=["POST"])
def record_audio():
    global speech_text

    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files['audio']

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp:
            audio_file.save(temp.name)
            temp_path = temp.name

        with sr.AudioFile(temp_path) as source:
            audio_data = recognizer.record(source)
            speech_text = recognizer.recognize_google(audio_data, language=src_language)

        os.remove(temp_path)

        return jsonify({"message": "Recording successful", "speech_text": speech_text})

    except Exception as e:
        # Print the error to debug logs
        print("❌ Error in /record:", str(e))
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500






@app.route("/translate", methods=["GET"])
def translate():
    global speech_text

    if not speech_text:
        return jsonify({"error": "No recorded speech found. Please record first."}), 400

    translated = translate_to_target_language(speech_text)
    print("Translated to target language:", translated)

    # Convert the translated text to speech using gTTS
    tts = gTTS(text=translated, lang=trg_language)
    audio_filename = f"{hash(translated)}.mp3"  # Create a unique filename based on the translation
    audio_path = os.path.join(AUDIO_STORAGE_DIR, audio_filename)

    # Save the translated speech to the audio storage directory
    tts.save(audio_path)

    # Return the file path or URL to the audio file
    audio_url = f"/static/{audio_filename}"  # Serve this file as static content

    return jsonify({
        "original_text": speech_text,
        "translated_text": translated,
        "audio_file": audio_url
    })

# Route to serve the audio files
@app.route('/static/<filename>')
def serve_audio(filename):
    # Return the file from the AUDIO_STORAGE_DIR directory
    return send_from_directory(AUDIO_STORAGE_DIR, filename)

if __name__ == "__main__":
    # Get the port from the environment variable or default to 5000
    port = int(os.getenv.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
