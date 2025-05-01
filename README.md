# Python-AI-Voice-Assistant-LM-Studio
Python voice assistant with LM Studio. Super simple setup to build off of.

## Info
Works on linux. Potentially works else where.
Simple assistant that can be started with the wake word ("computer" by default). You can also send clipboard contents with "clipboard contents keyword."

### Install
Install python using whatever method you like conda/micromamba recomended

  #### Install python dependencies
  pip install -r requirements.txt
  
  #### Get required files
  https://huggingface.co/rhasspy/piper-voices  
  default: en_US-amy-medium  
  put piper voices .onnx and onnx.json in the folder. Set with Voice with VOICE_PATH variable.
  
  https://alphacephei.com/vosk/models  
  default: vosk-model-en-us-0.22  
  put vosk model in the folder, set the MODEL_PATH.

#### Mess with the configuration settings
configs with defaults:  
WAKE_WORD = "computer"  
SAMPLERATE = 16000  
BLOCKSIZE = 16000  
DURATION = 15  # recording duration after wake word  
MODEL_PATH = "./vosk-model-en-us-0.22"  
MODEL = "local-model"  
VOICE_PATH = "./en_US-amy-medium.onnx"  
LM_API_URL = "http://localhost:1234/v1/chat/completions"  
HEADERS = {"Content-Type": "application/json"}  


## Run
Start your LM studio model, should be at localhost:1234 or where you set LM_AP_URL.  
run `python voice_chat.py`
