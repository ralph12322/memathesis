from flask import Flask, request, jsonify
import speech_recognition as sr
import os
from transformers import AutoTokenizer, MarianMTModel
from gtts import gTTS
import tempfile

app = Flask(__name__)

# Initialize speech recognizer
recognizer = sr.Recognizer()

# Load the translation model
src = "en"  # Chinese
trg = "zh"  # English
model_name = f"Helsinki-NLP/opus-mt-{src}-{trg}"
model = MarianMTModel.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Store speech transcription
speech_text = None

def translate_to_english(text):
    batch = tokenizer([text], return_tensors="pt")
    generated_ids = model.generate(**batch)
    return tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

@app.route("/record", methods=["POST"])
def record_audio():
    global speech_text

    try:
        print("Recording... Please speak now.")
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

        # Convert speech to text
        speech_text = recognizer.recognize_google(audio, language="zh-CN")
        print("You said (in Chinese):", speech_text)

        return jsonify({"message": "Recording successful", "chinese": speech_text})

    except sr.UnknownValueError:
        return jsonify({"error": "Could not understand audio"}), 400
    except sr.RequestError as e:
        return jsonify({"error": f"Speech recognition error: {e}"}), 500

@app.route("/translate", methods=["GET"])
def translate():
    global speech_text

    if not speech_text:
        return jsonify({"error": "No recorded speech found. Please record first."}), 400

    translated = translate_to_english(speech_text)
    print("Translated to English:", translated)

    # Convert to speech using gTTS
    tts = gTTS(text=translated, lang='en')
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
        tts.save(temp_audio.name)
        audio_path = temp_audio.name

    return jsonify({
        "original_chinese": speech_text,
        "translated_text": translated,
        "audio_file": audio_path
    })

if __name__ == "__main__":
    app.run(debug=True)
