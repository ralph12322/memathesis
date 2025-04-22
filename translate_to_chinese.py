from flask import Flask, request, jsonify
import sounddevice as sd
import soundfile as sf
import tempfile
import os
from faster_whisper import WhisperModel
from transformers import AutoTokenizer, MarianMTModel
from gtts import gTTS

# Initialize Flask app
app = Flask(__name__)

# Load Whisper model (use 'base' or 'small' for speed)
whisper_model = WhisperModel("base", compute_type="int8")

# Load MarianMT model for translation
src = "zh"  # Chinese
trg = "en"  # English
model_name = f"Helsinki-NLP/opus-mt-{src}-{trg}"
translator = MarianMTModel.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Store path to the last recorded audio
recorded_audio_path = None

def translate_to_english(text):
    batch = tokenizer([text], return_tensors="pt")
    generated_ids = translator.generate(**batch)
    return tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

@app.route("/record_audio", methods=["POST"])
def record_audio():
    global recorded_audio_path

    if request.json and request.json.get("action") == "start":
        duration = 5  # seconds
        fs = 16000  # sampling frequency

        print("Recording for 5 seconds...")
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            sf.write(temp_audio.name, audio, fs)
            recorded_audio_path = temp_audio.name

        return jsonify({"message": "Recording complete."})

    return jsonify({"error": "Invalid request."}), 400

@app.route("/translate", methods=["GET"])
def translate():
    global recorded_audio_path

    if recorded_audio_path and os.path.exists(recorded_audio_path):
        print(f"Transcribing: {recorded_audio_path}")
        segments, _ = whisper_model.transcribe(recorded_audio_path, language="zh")

        transcript = " ".join([segment.text for segment in segments])
        print("Recognized Chinese:", transcript)

        translated_text = translate_to_english(transcript)
        print("Translated to English:", translated_text)

        tts = gTTS(text=translated_text, lang="en")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_tts:
            tts.save(temp_tts.name)
            audio_path = temp_tts.name

        return jsonify({
            "original_chinese": transcript,
            "translated_text": translated_text,
            "audio_file": audio_path
        })

    return jsonify({"error": "No audio recorded."}), 400

if __name__ == "__main__":
    app.run(debug=True)
