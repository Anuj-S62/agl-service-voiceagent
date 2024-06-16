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

import sys
sys.path.append("../")
import json
import time
import threading
import asyncio
from agl_service_voiceagent.generated import voice_agent_pb2
from agl_service_voiceagent.generated import voice_agent_pb2_grpc
from agl_service_voiceagent.utils.audio_recorder import AudioRecorder
from agl_service_voiceagent.utils.wake_word import WakeWordDetector
from agl_service_voiceagent.utils.stt_model import STTModel
from agl_service_voiceagent.utils.kuksa_interface import KuksaInterface
from agl_service_voiceagent.utils.mapper import Intent2VSSMapper
from agl_service_voiceagent.utils.config import get_config_value, get_logger
from agl_service_voiceagent.utils.common import generate_unique_uuid, delete_file
from agl_service_voiceagent.nlu.snips_interface import SnipsInterface
from agl_service_voiceagent.nlu.rasa_interface import RASAInterface
from agl_service_voiceagent.utils.stt_online_service import STTOnlineService
from agl_service_voiceagent.utils.vss_interface import VSSInterface
from kuksa_client.grpc import Datapoint
from agl_service_voiceagent.utils.media_controller import MediaController


class VoiceAgentServicer(voice_agent_pb2_grpc.VoiceAgentServiceServicer):
    """
    Voice Agent Servicer class that implements the gRPC service defined in voice_agent.proto.
    """

    def __init__(self):
        """
        Constructor for VoiceAgentServicer class.
        """
        # Get the config values
        self.service_version = "v0.4.0"
        self.wake_word = get_config_value('WAKE_WORD')
        self.base_audio_dir = get_config_value('BASE_AUDIO_DIR')
        self.channels = int(get_config_value('CHANNELS'))
        self.sample_rate = int(get_config_value('SAMPLE_RATE'))
        self.bits_per_sample = int(get_config_value('BITS_PER_SAMPLE'))
        self.vosk_model_path = get_config_value('VOSK_MODEL_PATH')
        self.wake_word_model_path = get_config_value('WAKE_WORD_MODEL_PATH')
        self.snips_model_path = get_config_value('SNIPS_MODEL_PATH')
        self.rasa_model_path = get_config_value('RASA_MODEL_PATH')
        self.rasa_server_port = int(get_config_value('RASA_SERVER_PORT'))
        self.rasa_detached_mode = bool(int(get_config_value('RASA_DETACHED_MODE')))
        self.base_log_dir = get_config_value('BASE_LOG_DIR')
        self.store_voice_command = bool(int(get_config_value('STORE_VOICE_COMMANDS')))
        self.logger = get_logger()

        # load the whisper model_path
        self.whisper_model_path = get_config_value('WHISPER_MODEL_PATH')
        self.whisper_cpp_path = get_config_value('WHISPER_CPP_PATH')
        self.whisper_cpp_model_path = get_config_value('WHISPER_CPP_MODEL_PATH')

        # loading values for online mode
        self.online_mode = bool(int(get_config_value('ONLINE_MODE')))
        if self.online_mode:
            self.online_mode_address = get_config_value('ONLINE_MODE_ADDRESS')
            self.online_mode_port = int(get_config_value('ONLINE_MODE_PORT'))
            self.online_mode_timeout = int(get_config_value('ONLINE_MODE_TIMEOUT'))
            self.stt_online = STTOnlineService(self.online_mode_address, self.online_mode_port, self.online_mode_timeout)
            self.stt_online.initialize_connection()
            

        # Initialize class methods
        self.logger.info("Loading Speech to Text and Wake Word Model...")
        self.stt_model = STTModel(self.vosk_model_path, self.whisper_model_path,self.whisper_cpp_path,self.whisper_cpp_model_path,self.sample_rate)
        self.stt_wake_word_model = STTModel(self.vosk_model_path, self.whisper_model_path,self.whisper_cpp_path,self.whisper_cpp_model_path,self.sample_rate)
        self.logger.info("Speech to Text and Wake Word Model loaded successfully.")

        self.logger.info("Starting SNIPS intent engine...")
        self.snips_interface = SnipsInterface(self.snips_model_path)
        self.logger.info("SNIPS intent engine started successfully!")

        self.rasa_interface = RASAInterface(self.rasa_server_port, self.rasa_model_path, self.base_log_dir)

        # Only start RASA server if its not in detached mode, else we assume server is already running
        if not self.rasa_detached_mode:
            self.logger.info(f"Starting RASA intent engine server as a subprocess...")
            self.rasa_interface.start_server()
            self.logger.info(f"RASA intent engine server started successfully! RASA server running at URL: 127.0.0.1:{self.rasa_server_port}")
        
        else:
            self.logger.info(f"RASA intent engine detached mode detected! Assuming RASA server is running at URL: 127.0.0.1:{self.rasa_server_port}")

        self.rvc_stream_uuids = {}

        self.logger.info(f"Loading and parsing mapping files...")
        self.mapper = Intent2VSSMapper()
        self.logger.info(f"Successfully loaded and parsed mapping files.")

        # Media controller
        self.media_controller = MediaController()

        self.vss_interface = VSSInterface()
        self.vss_thread = threading.Thread(target=self.start_vss_client)
        self.vss_thread.start()
        self.vss_event_loop = None
        
    # VSS client methods

    def start_vss_client(self):
        """
        Start the VSS client.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.vss_interface.connect_vss_client())
        self.vss_event_loop = loop
        loop.run_forever()

    def connect_vss_client(self):
        """
        Connect the VSS client.
        """
        future = asyncio.run_coroutine_threadsafe(
            self.vss_interface.connect_vss_client(), 
            self.vss_event_loop
        )
        return future.result()

    def set_current_values(self, path=None, value=None):
        """
        Set the current values.

        Args:
            path (str): The path to set.
            value (any): The value to set.
        """
        future = asyncio.run_coroutine_threadsafe(
            self.vss_interface.set_current_values(path, value),
            self.vss_event_loop
        )
        return future.result()

    def get_current_values(self, paths=None):
        """
        Get the current values.

        Args:
            paths (list): The paths to get.

        Returns:
            dict: The current values.
        """
        print("Getting current values for paths:", paths)
        future = asyncio.run_coroutine_threadsafe(
            self.vss_interface.get_current_values(paths), 
            self.vss_event_loop
        )
        return future.result()

    def disconnect_vss_client(self):
        """
        Disconnect the VSS client.
        """
        future = asyncio.run_coroutine_threadsafe(
            self.vss_interface.disconnect_vss_client(), 
            self.vss_event_loop
        )
        return future.result()
    
    def get_vss_server_info(self):
        """
        Get the VSS server information.
        """
        future = asyncio.run_coroutine_threadsafe(
            self.vss_interface.get_server_info(), 
            self.vss_event_loop
        )
        return future.result()

    def CheckServiceStatus(self, request, context):
        """
        Check the status of the Voice Agent service including the version.
        """
        # Log the unique request ID, client's IP address, and the endpoint
        request_id = generate_unique_uuid(8)
        client_ip = context.peer()
        self.logger.info(f"[ReqID#{request_id}] Client {client_ip} made a request to CheckServiceStatus end-point.")

        response = voice_agent_pb2.ServiceStatus(
            version=self.service_version,
            status=True,
            wake_word=self.wake_word,
        )

        # Convert the response object to a JSON string and log it
        response_data = {
            "version": self.service_version,
            "status": True,
            "wake_word": self.wake_word,
        }
        response_json = json.dumps(response_data)
        self.logger.info(f"[ReqID#{request_id}] Returning response to client {client_ip} from CheckServiceStatus end-point. Response: {response_json}")

        return response


    def DetectWakeWord(self, request, context):
        """
        Detect the wake word using the wake word detection model. This method records voice on server side. If your client 
        and server are not on the same machine, then you should use the `S_DetectWakeWord` method instead.
        """
        # Log the unique request ID, client's IP address, and the endpoint
        request_id = generate_unique_uuid(8)
        client_ip = context.peer()
        self.logger.info(f"[ReqID#{request_id}] Client {client_ip} made a request to DetectWakeWord end-point.")

        wake_word_detector = WakeWordDetector(self.wake_word, self.stt_model, self.channels, self.sample_rate, self.bits_per_sample)
        wake_word_detector.create_pipeline()
        detection_thread = threading.Thread(target=wake_word_detector.start_listening)
        detection_thread.start()
        while True:
            status = wake_word_detector.get_wake_word_status()
            time.sleep(0.5)
            if not context.is_active():
                wake_word_detector.send_eos()
                break
            yield voice_agent_pb2.WakeWordStatus(status=status)
            if status:
                break

        detection_thread.join()
    
    
    def RecognizeVoiceCommand(self, requests, context):
        """
        Recognize the voice command using the STT model and extract the intent using the NLU model. This method records voice 
        on server side, meaning the client only sends a START and STOP request to the server. If your client and server are 
        not on the same machine, then you should use the `S_RecognizeVoiceCommand` method instead.
        """
        stt = ""
        intent = ""
        intent_slots = []
        log_intent_slots = []

        for request in requests:
            stt_framework = ''
            if request.stt_framework == voice_agent_pb2.VOSK:
                stt_framework = 'vosk'
            elif request.stt_framework == voice_agent_pb2.WHISPER:
                stt_framework = 'whisper'
            
            use_online_mode = False
            if request.online_mode == voice_agent_pb2.ONLINE:
                use_online_mode = True

            if request.record_mode == voice_agent_pb2.MANUAL:

                if request.action == voice_agent_pb2.START:
                    status = voice_agent_pb2.REC_PROCESSING
                    stream_uuid = generate_unique_uuid(8)

                    # Log the unique request ID, client's IP address, and the endpoint
                    client_ip = context.peer()
                    self.logger.info(f"[ReqID#{stream_uuid}] Client {client_ip} made a manual START request to RecognizeVoiceCommand end-point.")

                    recorder = AudioRecorder(self.stt_model, self.base_audio_dir, self.channels, self.sample_rate, self.bits_per_sample)
                    recorder.set_pipeline_mode("manual")
                    audio_file = recorder.create_pipeline()

                    self.rvc_stream_uuids[stream_uuid] = {
                        "recorder": recorder,
                        "audio_file": audio_file
                    }
                    
                    recorder.start_recording()

                elif request.action == voice_agent_pb2.STOP:
                    stream_uuid = request.stream_id
                    status = voice_agent_pb2.REC_SUCCESS

                    # Log the unique request ID, client's IP address, and the endpoint
                    client_ip = context.peer()
                    self.logger.info(f"[ReqID#{stream_uuid}] Client {client_ip} made a manual STOP request to RecognizeVoiceCommand end-point.")

                    recorder = self.rvc_stream_uuids[stream_uuid]["recorder"]
                    audio_file = self.rvc_stream_uuids[stream_uuid]["audio_file"]
                    del self.rvc_stream_uuids[stream_uuid]

                    recorder.stop_recording()
                                      
                    used_kaldi = False

                    if use_online_mode and self.online_mode:
                        print("Recognizing voice command using online mode.")
                        if self.stt_online.initialized:
                            stt = self.stt_online.recognize_audio(audio_file=audio_file)
                        elif not self.stt_online.initialized:
                            self.stt_online.initialize_connection()
                            stt = self.stt_online.recognize_audio(audio_file=audio_file)
                    else:
                        recognizer_uuid = self.stt_model.setup_vosk_recognizer()
                        stt = self.stt_model.recognize_from_file(recognizer_uuid, audio_file,stt_framework=stt_framework)
                        used_kaldi = True

                    if use_online_mode and self.online_mode and stt is None:
                        print("Online mode enabled but failed to recognize voice command. Switching to offline mode.")
                        recognizer_uuid = self.stt_model.setup_vosk_recognizer()
                        stt = self.stt_model.recognize_from_file(recognizer_uuid, audio_file,stt_framework=stt_framework)
                        used_kaldi = True

                    print(stt)
                    if stt not in ["FILE_NOT_FOUND", "FILE_FORMAT_INVALID", "VOICE_NOT_RECOGNIZED", ""]:
                        if request.nlu_model == voice_agent_pb2.SNIPS:
                            extracted_intent = self.snips_interface.extract_intent(stt)
                            intent, intent_actions = self.snips_interface.process_intent(extracted_intent)
                            if not intent or intent == "":
                                status = voice_agent_pb2.INTENT_NOT_RECOGNIZED
                            
                            else:
                                for action, value in intent_actions.items():
                                    intent_slots.append(voice_agent_pb2.IntentSlot(name=action, value=value))
                                    log_intent_slots.append({"name": action, "value": value})
                        
                        elif request.nlu_model == voice_agent_pb2.RASA:
                            extracted_intent = self.rasa_interface.extract_intent(stt)
                            intent, intent_actions = self.rasa_interface.process_intent(extracted_intent)

                            if not intent or intent == "":
                                status = voice_agent_pb2.INTENT_NOT_RECOGNIZED

                            else:
                                for action, value in intent_actions.items():
                                    intent_slots.append(voice_agent_pb2.IntentSlot(name=action, value=value))
                                    log_intent_slots.append({"name": action, "value": value})

                        else:
                            status = voice_agent_pb2.NLU_MODEL_NOT_SUPPORTED

                    else:
                        stt = ""
                        status = voice_agent_pb2.VOICE_NOT_RECOGNIZED
                    
                    # cleanup the kaldi recognizer
                    if used_kaldi:
                        self.stt_model.cleanup_recognizer(recognizer_uuid)
                        used_kaldi = False

                    # delete the audio file
                    if not self.store_voice_command:   
                        delete_file(audio_file)


        # Process the request and generate a RecognizeResult
        response = voice_agent_pb2.RecognizeResult(
            command=stt,
            intent=intent,
            intent_slots=intent_slots,
            stream_id=stream_uuid,
            status=status
        )

        # Convert the response object to a JSON string and log it
        response_data = {
            "command": stt,
            "intent": intent,
            "intent_slots": log_intent_slots,
            "stream_id": stream_uuid,
            "status": status
        }
        response_json = json.dumps(response_data)
        self.logger.info(f"[ReqID#{stream_uuid}] Returning {request.action} request response to client {client_ip} from RecognizeVoiceCommand end-point. Response: {response_json}")

        return response
    

    def RecognizeTextCommand(self, request, context):
        """
        Recognize the text command using the STT model and extract the intent using the NLU model.
        """
        intent = ""
        intent_slots = []
        log_intent_slots = []

        stream_uuid = generate_unique_uuid(8)
        text_command = request.text_command
        status = voice_agent_pb2.REC_SUCCESS

        # Log the unique request ID, client's IP address, and the endpoint
        client_ip = context.peer()
        self.logger.info(f"[ReqID#{stream_uuid}] Client {client_ip} made a request to RecognizeTextCommand end-point.")

        if request.nlu_model == voice_agent_pb2.SNIPS:
            extracted_intent = self.snips_interface.extract_intent(text_command)
            intent, intent_actions = self.snips_interface.process_intent(extracted_intent)

            if not intent or intent == "":
                status = voice_agent_pb2.INTENT_NOT_RECOGNIZED
            
            else:
                for action, value in intent_actions.items():
                    intent_slots.append(voice_agent_pb2.IntentSlot(name=action, value=value))
                    log_intent_slots.append({"name": action, "value": value})
        
        elif request.nlu_model == voice_agent_pb2.RASA:
            extracted_intent = self.rasa_interface.extract_intent(text_command)
            intent, intent_actions = self.rasa_interface.process_intent(extracted_intent)

            if not intent or intent == "":
                status = voice_agent_pb2.INTENT_NOT_RECOGNIZED

            else:
                for action, value in intent_actions.items():
                    intent_slots.append(voice_agent_pb2.IntentSlot(name=action, value=value))
                    log_intent_slots.append({"name": action, "value": value})
        
        else:
            status = voice_agent_pb2.NLU_MODEL_NOT_SUPPORTED

        # Process the request and generate a RecognizeResult
        response = voice_agent_pb2.RecognizeResult(
            command=text_command,
            intent=intent,
            intent_slots=intent_slots,
            stream_id=stream_uuid,
            status=status
        )

        # Convert the response object to a JSON string and log it
        response_data = {
            "command": text_command,
            "intent": intent,
            "intent_slots": log_intent_slots,
            "stream_id": stream_uuid,
            "status": status
        }
        response_json = json.dumps(response_data)
        self.logger.info(f"[ReqID#{stream_uuid}] Returning response to client {client_ip} from RecognizeTextCommand end-point. Response: {response_json}")

        return response


    def ExecuteCommand(self, request, context):
        """
        Execute the voice command by sending the intent to Kuksa.
        """
        if self.vss_interface.is_connected==False:
            self.logger.error("Kuksa client found disconnected. Trying to close old instance and re-connecting...")
            self.connect_vss_client()
        # Log the unique request ID, client's IP address, and the endpoint
        request_id = generate_unique_uuid(8)
        client_ip = context.peer()
        self.logger.info(f"[ReqID#{request_id}] Client {client_ip} made a request to ExecuteCommand end-point.")

        intent = request.intent
        intent_slots = request.intent_slots
        processed_slots = []
        for slot in intent_slots:
            slot_name = slot.name
            slot_value = slot.value
            processed_slots.append({"name": slot_name, "value": slot_value})
        print(intent)
        print(processed_slots)

        # Check for the media control intents
        if intent == "MediaControl":
            for slot in processed_slots:
                if slot["name"] == "media_control_action":
                    action = slot["value"]
                    
            if action == "resume" or action == "play":
                if self.media_controller.resume():
                    exec_response = "Yay, I successfully resumed the media."
                    exec_status = voice_agent_pb2.EXEC_SUCCESS
                else:
                    exec_response = "Uh oh, I failed to resume the media."
                    exec_status = voice_agent_pb2.EXEC_ERROR

            elif action == "pause":
                if self.media_controller.pause():
                    exec_response = "Yay, I successfully paused the media."
                    exec_status = voice_agent_pb2.EXEC_SUCCESS
                else:
                    exec_response = "Uh oh, I failed to pause the media."
                    exec_status = voice_agent_pb2.EXEC_ERROR

            elif action == "next":
                if self.media_controller.next():
                    exec_response = "Yay, I successfully played the next track."
                    exec_status = voice_agent_pb2.EXEC_SUCCESS
                else:
                    exec_response = "Uh oh, I failed to play the next track."
                    exec_status = voice_agent_pb2.EXEC_ERROR

            elif action == "previous":
                if self.media_controller.previous():
                    exec_response = "Yay, I successfully played the previous track."
                    exec_status = voice_agent_pb2.EXEC_SUCCESS
                else:
                    exec_response = "Uh oh, I failed to play the previous track."
                    exec_status = voice_agent_pb2.EXEC_ERROR
                    
            elif action == "stop":
                if self.media_controller.stop():
                    exec_response = "Yay, I successfully stopped the media."
                    exec_status = voice_agent_pb2.EXEC_SUCCESS
                else:
                    exec_response = "Uh oh, I failed to stop the media."
                    exec_status = voice_agent_pb2.EXEC_ERROR
            else:
                exec_response = "Sorry, I failed to execute command against intent 'MediaControl'. Maybe try again with more specific instructions."
                exec_status = voice_agent_pb2.EXEC_ERROR
            

            response = voice_agent_pb2.ExecuteResult(
                response=exec_response,
                status=exec_status
            )
            return response


        execution_list = self.mapper.parse_intent(intent, processed_slots, req_id=request_id)
        exec_response = f"Sorry, I failed to execute command against intent '{intent}'. Maybe try again with more specific instructions."
        exec_status = voice_agent_pb2.EXEC_ERROR
        # Check for kuksa status, and try re-connecting again if status is False 
        if self.vss_interface.is_connected:
            self.logger.info(f"[ReqID#{request_id}] Kuksa client found connected.")
        else:
            self.logger.error(f"[ReqID#{request_id}] Kuksa client found disconnected. Trying to close old instance and re-connecting...")
            exec_response = "Uh oh, I failed to connect to Kuksa."
            exec_status = voice_agent_pb2.KUKSA_CONN_ERROR
            self.disconnect_vss_client()
            return voice_agent_pb2.ExecuteResult(
                response=exec_response,
                status=exec_status
            )
        
        if not self.vss_interface.is_connected:
            self.logger.error(f"[ReqID#{request_id}] Kuksa client failed to connect.")
            exec_response = "Uh oh, I failed to connect to Kuksa."
            exec_status = voice_agent_pb2.KUKSA_CONN_ERROR
            response = voice_agent_pb2.ExecuteResult(
                response=exec_response,
                status=exec_status
            )
            return response
        for execution_item in execution_list:
            print(execution_item)
            action = execution_item["action"]
            signal = execution_item["signal"]

            if self.vss_interface.is_connected:
                if action == "set" and "value" in execution_item:
                    value = execution_item["value"]
                    response = self.set_current_values(signal, value)
                    if response is None or response is False:
                        exec_response = "Uh oh, I failed to send value to Kuksa."
                        exec_status = voice_agent_pb2.KUKSA_CONN_ERROR
                    else:
                        exec_response = f"Yay, I successfully updated the intent '{intent}' to value '{value}'."
                        exec_status = voice_agent_pb2.EXEC_SUCCESS

                elif action in ["increase", "decrease"]:
                    if "value" in execution_item:
                        value = execution_item["value"]
                        if self.set_current_values(signal, value):
                            exec_response = f"Yay, I successfully updated the intent '{intent}' to value '{value}'."
                            exec_status = voice_agent_pb2.EXEC_SUCCESS
                    
                    elif "factor" in execution_item:
                        # incoming values are always str as kuksa expects str during subscribe we need to convert
                        # the value to int before performing any arithmetic operations and then convert back to str
                        factor = int(execution_item["factor"]) 
                        current_value = self.get_current_values(signal)
                        if current_value is None:
                            exec_response = f"Uh oh, there is no value set for intent '{intent}'. Why not try setting a value first?"
                            exec_status = voice_agent_pb2.KUKSA_CONN_ERROR
                        else:
                            if current_value:
                                current_value = int(current_value)
                                if action == "increase":
                                    value = current_value + factor
                                    value = str(value)
                                elif action == "decrease":
                                    value = current_value - factor
                                    value = str(value)
                                if self.set_current_values(signal, value):
                                    exec_response = f"Yay, I successfully updated the intent '{intent}' to value '{value}'."
                                    exec_status = voice_agent_pb2.EXEC_SUCCESS

                            else:
                                exec_response = f"Uh oh, there is no value set for intent '{intent}'. Why not try setting a value first?"
                                exec_status = voice_agent_pb2.KUKSA_CONN_ERROR

            else:
                exec_response = "Uh oh, I failed to connect to Kuksa."
                exec_status = voice_agent_pb2.KUKSA_CONN_ERROR

        response = voice_agent_pb2.ExecuteResult(
            response=exec_response,
            status=exec_status
        )

        # Convert the response object to a JSON string and log it
        response_data = {
            "response": exec_response,
            "status": exec_status
        }
        response_json = json.dumps(response_data)
        self.logger.info(f"[ReqID#{request_id}] Returning response to client {client_ip} from ExecuteCommand end-point. Response: {response_json}")

        return response
