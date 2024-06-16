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

import grpc
import sys
sys.path.append("../")
from agl_service_voiceagent.generated import audio_processing_pb2
from agl_service_voiceagent.generated import audio_processing_pb2_grpc

class STTOnlineService:
    """
    STTOnlineService class is used to connect to an online gPRC based Whisper ASR service.
    """
    def __init__(self, server_address, server_port,server_timeout=5):
        """
        Initialize the online speech-to-text service.

        Args:
            server_ip (str): The IP address of the online speech-to-text service.
            server_port (int): The port number of the online speech-to-text service.
            server_timeout (int, optional): The timeout value in seconds (default is 5).
        """
        self.server_address = server_address
        self.server_port = server_port
        self.server_timeout = server_timeout
        self.client = None
        self.initialized = False


    def initialize_connection(self):
        """
        Initialize the connection to the online speech-to-text service.
        """
        try:
            channel = grpc.insecure_channel(f"{self.server_address}:{self.server_port}")
            self.client = audio_processing_pb2_grpc.AudioProcessingStub(channel)
            self.initialized = True
            print("STTOnlineService initialized with server address:",self.server_address,"and port:",self.server_port,"and timeout:",self.server_timeout,"seconds.")
        except Exception as e:
            print("Error initializing online speech-to-text service:",e)
            self.initialized = False
        return self.initialized

    def close_connection(self):
        """
        Close the connection to the online speech-to-text service.
        """
        self.client = None
        self.initialized = False
        return not self.initialized
    
    def recognize_audio(self, audio_file):
        """
        Recognize speech from audio data.

        Args:
            audio_data (bytes): Audio data to process.

        Returns:
            str: The recognized text.
        """
        if not self.initialized:
            print("STTOnlineService not initialized.")
            return None
        try:
            with open(audio_file, 'rb') as audio_file:
                audio_data = audio_file.read()
            request = audio_processing_pb2.AudioRequest(audio_data=audio_data)
            response = self.client.ProcessAudio(request,timeout=self.server_timeout)
            return response.text
        except Exception as e:
            print("Error recognizing audio:",e)
            return None

    