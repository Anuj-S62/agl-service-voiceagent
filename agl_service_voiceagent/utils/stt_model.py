# SPDX-License-Identifier: Apache-2.0
#
# Copyright (c) 2023 Malik Talha
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import json
import vosk
import wave
from agl_service_voiceagent.utils.common import generate_unique_uuid

# import the whisper model
# import whisper
# for whisper timeout feature
from concurrent.futures import ThreadPoolExecutor  
import subprocess

class STTModel:
    """
    STTModel is a class for speech-to-text (STT) recognition using the Vosk speech recognition library.
    """

    def __init__(self, vosk_model_path,whisper_model_path,whisper_cpp_path,whisper_cpp_model_path,sample_rate=16000):
        """
        Initialize the STTModel instance with the provided model and sample rate.

        Args:
            model_path (str): The path to the Vosk speech recognition model.
            sample_rate (int, optional): The audio sample rate in Hz (default is 16000).
        """
        self.sample_rate = sample_rate
        self.vosk_model = vosk.Model(vosk_model_path)
        self.recognizer = {}
        self.chunk_size = 1024
        # self.whisper_model = whisper.load_model(whisper_model_path)
        self.whisper_cpp_path = whisper_cpp_path
        self.whisper_cpp_model_path = whisper_cpp_model_path
    

    def setup_vosk_recognizer(self):
        """
        Set up a Vosk recognizer for a new session and return a unique identifier (UUID) for the session.

        Returns:
            str: A unique identifier (UUID) for the session.
        """
        uuid = generate_unique_uuid(6)
        self.recognizer[uuid] = vosk.KaldiRecognizer(self.vosk_model, self.sample_rate)
        return uuid

    def init_recognition(self, uuid, audio_data):
        """
        Initialize the Vosk recognizer for a session with audio data.

        Args:
            uuid (str): The unique identifier (UUID) for the session.
            audio_data (bytes): Audio data to process.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        return self.recognizer[uuid].AcceptWaveform(audio_data)

    # Recognize speech using the Vosk recognizer
    def recognize_using_vosk(self, uuid, partial=False):
        """
        Recognize speech and return the result as a JSON object.

        Args:
            uuid (str): The unique identifier (UUID) for the session.
            partial (bool, optional): If True, return partial recognition results (default is False).

        Returns:
            dict: A JSON object containing recognition results.
        """
        self.recognizer[uuid].SetWords(True)
        if partial:
            result = json.loads(self.recognizer[uuid].PartialResult())
        else:
            result = json.loads(self.recognizer[uuid].Result())
            self.recognizer[uuid].Reset()
        return result
    
    # Recognize speech using the whisper model
    # def recognize_using_whisper(self,filename,language = None,timeout = 5,fp16=False):
    #     """
    #     Recognize speech and return the result as a JSON object.

    #     Args:
    #         filename (str): The path to the audio file.
    #         timeout (int, optional): The timeout for recognition (default is 5 seconds).
    #         fp16 (bool, optional): If True, use 16-bit floating point precision, (default is False) because cuda is not supported.
    #         language (str, optional): The language code for recognition (default is None).

    #     Returns:
    #         dict: A JSON object containing recognition results.
    #     """
    #     def transcribe_with_whisper():
    #         return self.whisper_model.transcribe(filename, language = language,fp16=fp16)
        
    #     with ThreadPoolExecutor() as executor:
    #         future = executor.submit(transcribe_with_whisper)
    #         try:
    #             return future.result(timeout=timeout)
    #         except TimeoutError:
    #             return {"error": "Transcription with Whisper exceeded the timeout."}
            
    def recognize_using_whisper_cpp(self,filename):
        command = self.whisper_cpp_path
        arguments = ["-m", self.whisper_cpp_model_path, "-f", filename, "-l", "en","-nt"]

        # Run the executable with the specified arguments
        result = subprocess.run([command] + arguments, capture_output=True, text=True)      

        if result.returncode == 0:
            result = result.stdout.replace('\n', ' ').strip()
            return {"text": result}
        else:
            print("Error:\n", result.stderr)
            return {"error": result.stderr}
    

    def recognize_from_file(self, uuid, filename,stt_framework="vosk"):
        """
        Recognize speech from an audio file and return the recognized text.

        Args:
            uuid (str): The unique identifier (UUID) for the session.
            filename (str): The path to the audio file.
            stt_model (str): The STT model to use for recognition (default is "vosk").

        Returns:
            str: The recognized text or error messages.
        """
        filename = "/Users/anujsolanki/new-test.wav"
        if not os.path.exists(filename):
            print(f"Audio file '{filename}' not found.")
            return "FILE_NOT_FOUND"
        
        wf = wave.open(filename, "rb")
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
            print("Audio file must be WAV format mono PCM.")
            return "FILE_FORMAT_INVALID"
        
        # audio_data = wf.readframes(wf.getnframes())
        # we need to perform chunking as target AGL system can't handle an entire audio file
        audio_data = b""
        while True:
            chunk = wf.readframes(self.chunk_size)
            if not chunk:
                break  # End of file reached
            audio_data += chunk

        if audio_data:
            # Perform speech recognition using the specified STT model
            if stt_framework == "vosk":
                if self.init_recognition(uuid, audio_data):
                    result = self.recognize_using_vosk(uuid)
                    return result['text']
                else:
                    result = self.recognize_using_vosk(uuid, partial=True)
                    return result['partial']
                
            elif stt_framework == "whisper":
                result = self.recognize_using_whisper_cpp(filename)
                if 'error' in result:
                    print(result['error'])
                    # If Whisper times out, fall back to Vosk
                    if self.init_recognition(uuid, audio_data):
                        result = self.recognize_using_vosk(uuid)
                        return result['text']
                    else:
                        result = self.recognize_using_vosk(uuid, partial=True)
                        return result['partial']
                else:
                    return result.get('text', '')

        else:
            print("Voice not recognized. Please speak again...")
            return "VOICE_NOT_RECOGNIZED"
    

    def cleanup_recognizer(self, uuid):
        """
        Clean up and remove the Vosk recognizer for a session.

        Args:
            uuid (str): The unique identifier (UUID) for the session.
        """
        del self.recognizer[uuid]
    