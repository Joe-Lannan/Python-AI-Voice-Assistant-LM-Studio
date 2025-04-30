import sounddevice as sd
import queue
import json
import requests
import wave
import sys
from vosk import Model, KaldiRecognizer
from piper import PiperVoice
import io
import soundfile as sf
import pyperclip

WAKE_WORD = "computer"
SAMPLERATE = 16000
BLOCKSIZE = 16000
MODEL_PATH = "./vosk-model-en-us-0.22"
MODEL = "local-model"
VOICE_PATH = "./en_US-amy-medium.onnx"
LM_API_URL = "http://localhost:1234/v1/chat/completions"
HEADERS = {"Content-Type": "application/json"}

class colors:
    PROMPT = '\033[95m'
    RESPONSE = '\033[94m'
    SYSTEM = '\033[94m'
    ENDC = '\033[0m'

try:
    vosk_model = Model(MODEL_PATH)
    print(f"Vosk model loaded from {MODEL_PATH}")
except Exception as e:
    print(f"Error loading Vosk model from {MODEL_PATH}: {e}")
    sys.exit(1)

q = queue.Queue()

try:
    piper = PiperVoice.load(VOICE_PATH)
    print(f"Piper voice model loaded from {VOICE_PATH}")
except Exception as e:
    print(f"Error loading Piper voice model from {VOICE_PATH}: {e}")
    sys.exit(1)

def speak(text):
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit audio
        wav_file.setframerate(piper.config.sample_rate)
        piper.synthesize(text, wav_file)
    buf.seek(0)
    audio, sr = sf.read(buf, dtype='float32')
    adjusted_sr = int(sr) # set speed multiplier
    sd.play(audio, samplerate=adjusted_sr)
    sd.wait()

def list_audio_devices():
    print("Available Audio Devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']} - {device['max_input_channels']} channels")
    return devices

def audio_callback(indata, frames, time, status):
    if status:
        print(f"Status: {status}")
        q.queue.clear() #flush buffer on errors
        return
    q.put(bytes(indata))

def detect_wake_word(device_index):
    print(f"Listening for wake word \"{WAKE_WORD}\"...")
    rec = KaldiRecognizer(vosk_model, SAMPLERATE)

    while True:
        with sd.RawInputStream(samplerate=SAMPLERATE, blocksize=BLOCKSIZE, dtype='int16',
                               channels=1, callback=audio_callback, device=device_index, never_drop_input=False):
            try:
                data = q.get(timeout=1.0)
            except queue.Empty:
                q.queue.clear()
                continue
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").lower()
                # print(f"Recognized: {text}")

                if WAKE_WORD in text:
                    prompt = text[text.find(WAKE_WORD) + len(WAKE_WORD):].strip()
                    print("Wake word detected")
                    if not prompt:
                        print("Wake word detected, but no prompt found.")
                        continue
                    # If the prompt contains the keyword "clipboard contents", replace it with clipboard text
                    if "clipboard contents" in prompt.lower():
                        clipboard_text = pyperclip.paste()
                        if not clipboard_text:
                            print("Clipboard is empty.")
                            return "Sorry, clipboard is empty."
                        prompt = prompt.replace("clipboard contents", clipboard_text)
                        print("Clipboard contents detected, inserting into prompt")

                    return prompt

def query_lmstudio(prompt, history):
    history.append({"role": "user", "content": prompt})
    payload = {
        "model": MODEL,
        "messages": history,
        "temperature": 0.7,
    }
    try:
        r = requests.post(LM_API_URL, headers=HEADERS, json=payload)
        r.raise_for_status()  # Check for HTTP errors
        reply = r.json()["choices"][0]["message"]["content"]
        history.append({"role": "assistant", "content": reply})
        return reply
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to server: {e}")
        return "Sorry, I couldn't reach the server. You may need to start the LM Studio server."

def main():
    conversation = []
    print("\n")
    print(colors.SYSTEM)
    devices = list_audio_devices()

    while True:
        try:
            device_index = int(input("Select device index: "))
            if device_index >= len(devices) or devices[device_index]["max_input_channels"] == 0:
                print("Invalid device index or no input channels available. Please try again.")
                continue
            break
        except ValueError:
            print("Invalid input. Please enter a valid device index.")

    selected_device = devices[device_index]
    if selected_device["max_input_channels"] < 1:
        print("Selected device does not support input channels. Exiting.")
        return

    print(f"Using device: {selected_device['name']}")
    print(colors.ENDC)

    while True:
        prompt = detect_wake_word(device_index)
        if prompt:
            print(f"{colors.PROMPT}You: {prompt} {colors.ENDC}")

        if prompt.lower() in ["exit", "quit", "stop"]:
            speak("Goodbye.")
            break

        reply = query_lmstudio(prompt, conversation)
        print(f"{colors.RESPONSE}LM: {reply} {colors.ENDC}")
        speak(reply)

if __name__ == "__main__":
    main()
