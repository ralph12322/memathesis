print("🚀 translate_to_chinese.py is running!")

from flask import Flask, request, jsonify, send_from_directory
import speech_recognition as sr
import os
from transformers import AutoTokenizer, MarianMTModel
from gtts import gTTS
import tempfile
from flask_cors import CORS
from pydub import AudioSegment

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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

import subprocess

def convert_audio(input_path, output_path):
    try:
        # Attempt to use FFmpeg to convert to PCM WAV if it's not in the correct format
        command = [
            "ffmpeg", 
            "-i", input_path,        # Input file path
            "-ac", "1",              # Mono channels
            "-ar", "16000",          # 16 kHz sample rate
            "-f", "wav",             # Output format as WAV
            output_path              # Output file path
        ]
        # Run the FFmpeg command to convert the audio
        subprocess.run(command, check=True)
        print(f"✅ Audio file converted successfully: {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error during conversion: {str(e)}")
        raise Exception("Audio file conversion failed. Ensure the file is in a supported format.")





@app.route("/set_language", methods=["POST"])
def set_language():
    global src_language, trg_language, model, tokenizer
    try:
        data = request.json
        src_language = data.get("source", "en")  # Default to 'en' if not provided
        trg_language = data.get("target", "zh")  # Default to 'zh' if not provided

        # Load the translation model based on selected languages
        model_name = f"Helsinki-NLP/opus-mt-{src_language}-{trg_language}"
        model = MarianMTModel.from_pretrained(model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        return jsonify({"message": "Languages set successfully!"})
    except Exception as e:
        print(f"❌ Error in /set_language: {str(e)}")
        return jsonify({"error": f"Failed to set languages: {str(e)}"}), 500

# Store speech transcription
speech_text = None

def translate_to_target_language(text):
    # Ensure model and tokenizer are loaded before translating
    if model is None or tokenizer is None:
        raise ValueError("Translation model and tokenizer are not loaded.")

    try:
        batch = tokenizer([text], return_tensors="pt")
        generated_ids = model.generate(**batch)
        return tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    except Exception as e:
        print(f"❌ Error in translate_to_target_language: {str(e)}")
        raise ValueError("Translation failed.") from e


@app.route("/record", methods=["POST"])
def record_audio():
    global speech_text

    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        audio_file = request.files['audio']
        print(f"📦 Received file: {audio_file.filename}, Content-Type: {audio_file.content_type}")

        # Save with original MIME type extension if needed
        suffix = mimetypes.guess_extension(audio_file.content_type) or ".webm"

        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
            input_path = temp.name
            audio_file.save(input_path)
        print(f"📂 Audio saved to temp path: {input_path}")

        # Convert input to standard WAV
        output_path = input_path + "_converted.wav"
        command = [
            "ffmpeg",
            "-y",                # Overwrite output
            "-i", input_path,    # Input path
            "-ac", "1",          # Mono
            "-ar", "16000",      # 16 kHz
            output_path
        ]
        subprocess.run(command, check=True)
        print(f"🎧 Audio converted to WAV: {output_path}")

        # Load with speech recognition
        with sr.AudioFile(output_path) as source:
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)
            speech_text = recognizer.recognize_google(audio_data, language=src_language)
        
        # Cleanup
        os.remove(input_path)
        os.remove(output_path)

        return jsonify({"message": "Recording successful", "speech_text": speech_text})

    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand audio"}), 400
    except sr.RequestError as e:
        return jsonify({"error": f"Speech API error: {str(e)}"}), 500
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error: {e}")
        return jsonify({"error": "Audio conversion failed. Make sure the uploaded file is a valid recording."}), 500
    except Exception as e:
        print(f"🔥 Internal Server Error: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500





@app.route("/translate", methods=["GET"])
def translate():
    global speech_text

    if not speech_text:
        return jsonify({"error": "No recorded speech found. Please record first."}), 400

    try:
        translated = translate_to_target_language(speech_text)
        print(f"✅ Translated to {trg_language}: {translated}")

        # Convert the translated text to speech using gTTS
        tts = gTTS(text=translated, lang=trg_language)
        audio_filename = f"{hash(translated)}.mp3"  # Unique filename based on translation text
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
    except Exception as e:
        print(f"❌ Error in /translate: {str(e)}")
        return jsonify({"error": f"Translation or TTS error: {str(e)}"}), 500

# Route to serve the audio files
@app.route('/static/<filename>')
def serve_audio(filename):
    try:
        return send_from_directory(AUDIO_STORAGE_DIR, filename)
    except Exception as e:
        print(f"❌ Error serving audio file: {str(e)}")
        return jsonify({"error": "Failed to serve audio file"}), 500

if __name__ == "__main__":
    app.run(debug=True)
