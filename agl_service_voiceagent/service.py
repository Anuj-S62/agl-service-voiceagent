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
import sys

# Get the path to the directory containing this script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the path to the "generated" folder
generated_dir = os.path.join(current_dir, "generated")
# Add the "generated" folder to sys.path
sys.path.append(generated_dir)
sys.path.append("../")

import argparse
from agl_service_voiceagent.utils.config import set_config_path, load_config, update_config_value, get_config_value, get_logger
from agl_service_voiceagent.utils.common import add_trailing_slash
from agl_service_voiceagent.server import run_server
from agl_service_voiceagent.client import run_client

def print_version():
    print("Automotive Grade Linux (AGL)")
    print(f"Voice Agent Service v0.4.0")


def main():
    parser = argparse.ArgumentParser(description="Automotive Grade Linux (AGL) - Voice Agent Service")
    parser.add_argument('--version', action='store_true', help='Show version')
    
    subparsers = parser.add_subparsers(dest='subcommand', title='Available Commands')
    subparsers.required = False
    
    # Create subparsers for "run server" and "run client"
    server_parser = subparsers.add_parser('run-server', help='Run the Voice Agent gRPC Server')
    client_parser = subparsers.add_parser('run-client', help='Run the Voice Agent gRPC Client')
    
    # Add the arguments for the server
    server_parser.add_argument('--default', action='store_true', help='Starts the server based on default config file.')
    server_parser.add_argument('--config', required=False, help='Path to a config file. Server is started based on this config file.')
    server_parser.add_argument('--vosk-model-path', required=False, help='Path to the Vosk Speech To Text model for Voice Commad detection.')
    server_parser.add_argument('--whisper-model-path', required=False, help='Path to the Whisper Speech To Text model for Voice Commad detection.')
    server_parser.add_argument('--ww-model-path', required=False, help='Path to the Speech To Text model for Wake Word detection. Currently only supports VOSK Kaldi. Defaults to the same model as --vosk-model-path if not provided.')
    server_parser.add_argument('--snips-model-path', required=False, help='Path to the Snips NLU model.')
    server_parser.add_argument('--rasa-model-path', required=False, help='Path to the RASA NLU model.')
    server_parser.add_argument('--rasa-detached-mode', required=False, help='Assume that the RASA server is already running and does not start it as a sub process.')
    server_parser.add_argument('--intents-vss-map-path', required=False, help='Path to the JSON file containing Intent to VSS map.')
    server_parser.add_argument('--vss-signals-spec-path', required=False, help='Path to the VSS signals specification JSON file.')
    server_parser.add_argument('--audio-store-dir', required=False, help='Directory to store the generated audio files.')
    server_parser.add_argument('--log-store-dir', required=False, help='Directory to store the generated log files.')

    # Arguments for online mode
    server_parser.add_argument('--online-mode', required=False, help='Enable online mode for the Voice Agent Service (default is False).')
    server_parser.add_argument('--online-mode-address', required=False, help='URL of the online server to connect to.')
    server_parser.add_argument('--online-mode-port', required=False, help='Port of the online server to connect to.')
    server_parser.add_argument('--online-mode-timeout', required=False, help='Timeout value in seconds for the online server connection.')


    # Add the arguments for the client
    client_parser.add_argument('--server-address', required=True, help='Address of the gRPC server running the Voice Agent Service.')
    client_parser.add_argument('--server-port', required=True, help='Port of the gRPC server running the Voice Agent Service.')
    client_parser.add_argument('--action', required=True, help='Action to perform. Supported actions: "GetStatus", "DetectWakeWord", "ExecuteVoiceCommand" and "ExecuteTextCommand".')
    client_parser.add_argument('--mode', help='Mode to run the client in. Supported modes: "auto" and "manual".')
    client_parser.add_argument('--nlu', help='NLU engine/model to use. Supported NLU engines: "snips" and "rasa".')
    client_parser.add_argument('--recording-time', help='Number of seconds to continue recording the voice command. Required by the \'manual\' mode. Defaults to 10 seconds.')
    client_parser.add_argument('--stt-framework', help='STT framework to use. Supported frameworks: "vosk". Defaults to "vosk".')

    # Arguments for online mode in client as --online-mode is a reserved keyword
    client_parser.add_argument('--online-mode', required=False, help='Enable online mode for the Voice Agent Service (default is False).')

    args = parser.parse_args()
    
    if args.version:
        print_version()

    elif args.subcommand == 'run-server':
        if not args.default and not args.config:
            if not args.vosk_model_path:
                print("Error: The --vosk-model-path is missing. Please provide a value. Use --help to see available options.")
                exit(1)

            if not args.whisper_model_path:
                print("Error: The --whisper-model-path is missing. Please provide a value. Use --help to see available options.")
                exit(1)
            
            if not args.snips_model_path:
                print("Error: The --snips-model-path is missing. Please provide a value. Use --help to see available options.")
                exit(1)
            
            if not args.rasa_model_path:
                print("Error: The --rasa-model-path is missing. Please provide a value. Use --help to see available options.")
                exit(1)
            
            if not args.intents_vss_map_path:
                print("Error: The --intents-vss-map-path is missing. Please provide a value. Use --help to see available options.")
                exit(1)
            
            if not args.vss_signals_spec_path:
                print("Error: The --vss-signals-spec-path is missing. Please provide a value. Use --help to see available options.")
                exit(1)
            
            # Error check for online mode
            if args.online_mode:
                if not args.online_mode_address:
                    print("Error: The --online-mode-address is missing. Please provide a value. Use --help to see available options.")
                    exit(1)
                
                if not args.online_mode_port:
                    print("Error: The --online-mode-port is missing. Please provide a value. Use --help to see available options.")
                    exit(1)    
                           
            # Contruct the default config file path
            config_path = os.path.join(current_dir, "config.ini")

            # Load the config values from the config file
            set_config_path(config_path)
            load_config()

            logger = get_logger()
            logger.info("Starting Voice Agent Service in server mode using CLI provided params...")
            
            # Get the values provided by the user
            vosk_path = args.vosk_model_path
            whisper_path = args.whisper_model_path
            snips_model_path = args.snips_model_path
            rasa_model_path = args.rasa_model_path
            intents_vss_map_path = args.intents_vss_map_path
            vss_signals_spec_path = args.vss_signals_spec_path
            
            # Get the values for online mode
            online_mode = False
            if args.online_mode:
                online_mode = True
                online_mode_address = args.online_mode_address
                online_mode_port = args.online_mode_port
                online_mode_timeout = args.online_mode_timeout or 5
                update_config_value('1', 'ONLINE_MODE')
                update_config_value(online_mode_address, 'ONLINE_MODE_ADDRESS')
                update_config_value(online_mode_port, 'ONLINE_MODE_PORT')
                update_config_value(online_mode_timeout, 'ONLINE_MODE_TIMEOUT')
            
            # Convert to an absolute path if it's a relative path
            vosk_path = add_trailing_slash(os.path.abspath(vosk_path)) if not os.path.isabs(vosk_path) else vosk_path
            whisper_path = add_trailing_slash(os.path.abspath(whisper_path)) if not os.path.isabs(whisper_path) else whisper_path
            snips_model_path = add_trailing_slash(os.path.abspath(snips_model_path)) if not os.path.isabs(snips_model_path) else snips_model_path
            rasa_model_path = add_trailing_slash(os.path.abspath(rasa_model_path)) if not os.path.isabs(rasa_model_path) else rasa_model_path
            intents_vss_map_path = os.path.abspath(intents_vss_map_path) if not os.path.isabs(intents_vss_map_path) else intents_vss_map_path
            vss_signals_spec_path = os.path.abspath(vss_signals_spec_path) if not os.path.isabs(vss_signals_spec_path) else vss_signals_spec_path
            
            # Also update the config.ini file
            update_config_value(vosk_path, 'VOSK_MODEL_PATH')
            update_config_value(whisper_path, 'WHISPER_MODEL_PATH')
            update_config_value(snips_model_path, 'SNIPS_MODEL_PATH')
            update_config_value(rasa_model_path, 'RASA_MODEL_PATH')
            update_config_value(intents_vss_map_path, 'INTENTS_VSS_MAP')
            update_config_value(vss_signals_spec_path, 'VSS_SIGNALS_SPEC')
            if args.rasa_detached_mode:
                update_config_value('1', 'RASA_DETACHED_MODE')

            # Update the audio store dir in config.ini if provided
            audio_dir = args.audio_store_dir or get_config_value('BASE_AUDIO_DIR')
            audio_dir = add_trailing_slash(os.path.abspath(audio_dir)) if not os.path.isabs(audio_dir) else audio_dir
            update_config_value(audio_dir, 'BASE_AUDIO_DIR')

            # Update the log store dir in config.ini if provided
            log_dir = args.log_store_dir or get_config_value('BASE_LOG_DIR')
            log_dir = add_trailing_slash(os.path.abspath(log_dir)) if not os.path.isabs(log_dir) else log_dir
            update_config_value(log_dir, 'BASE_LOG_DIR')


        elif args.config:
            # Get config file path value 
            cli_config_path = args.config

            # if config file path provided then load the config values from it
            if cli_config_path :
                cli_config_path  = os.path.abspath(cli_config_path) if not os.path.isabs(cli_config_path) else cli_config_path 
                print(f"New config file path provided: {cli_config_path}. Overriding the default config file path.")
                set_config_path(cli_config_path)
                load_config()

                logger = get_logger()
                logger.info(f"Starting Voice Agent Service in server mode using provided config file at path '{cli_config_path}' ...")
        
        elif args.default:
            # Contruct the default config file path
            config_path = os.path.join(current_dir, "config.ini")

            # Load the config values from the config file
            set_config_path(config_path)
            load_config()

            logger = get_logger()
            logger.info(f"Starting Voice Agent Service in server mode using the default config file...")
        # create the base audio dir if not exists
        if not os.path.exists(get_config_value('BASE_AUDIO_DIR')):
            os.makedirs(get_config_value('BASE_AUDIO_DIR'))

        run_server()

    elif args.subcommand == 'run-client':
        server_address = args.server_address
        server_port = args.server_port
        nlu_engine = ""
        mode = ""
        action = args.action
        recording_time = 5 # seconds
        stt_framework = args.stt_framework or "vosk"
        online_mode = args.online_mode or False

        if action not in ["GetStatus", "DetectWakeWord", "ExecuteVoiceCommand", "ExecuteTextCommand"]:
            print("Error: Invalid value for --action. Supported actions: 'GetStatus', 'DetectWakeWord', 'ExecuteVoiceCommand' and 'ExecuteTextCommand'. Use --help to see available options.")
            exit(1)
        
        if action in ["ExecuteVoiceCommand", "ExecuteTextCommand"]:
            if not args.nlu:
                print("Error: The --nlu flag is missing. Please provide a value for intent engine. Supported NLU engines: 'snips' and 'rasa'.  Use --help to see available options.")
                exit(1)
            
            nlu_engine = args.nlu
            if nlu_engine not in ['snips', 'rasa']:
                print("Error: Invalid value for --nlu. Supported NLU engines: 'snips' and 'rasa'. Use --help to see available options.")
                exit(1)

        if action in ["ExecuteVoiceCommand"]:
            if not args.mode:
                print("Error: The --mode flag is missing. Please provide a value for mode. Supported modes: 'auto' and 'manual'.  Use --help to see available options.")
                exit(1)
            
            mode = args.mode
            if mode == "manual" and args.recording_time:
                recording_time = int(args.recording_time)
            if args.stt_framework and args.stt_framework not in ['vosk', 'whisper']:
                print("Error: Invalid value for --stt-framework. Supported frameworks: 'vosk' and 'whisper'. Use --help to see available options.")
                exit(1)
            if args.stt_framework:
                stt_framework = args.stt_framework
            
            if args.online_mode and args.online_mode not in ['True', 'False', 'true', 'false', '1', '0']:
                print("Error: Invalid value for --online-mode. Supported values: 'True' and 'False'. Use --help to see available options.")
                exit(1)
            if args.online_mode:
                online_mode = True if args.online_mode in ['True', 'true', '1'] else False

        run_client(server_address, server_port, action, mode, nlu_engine, recording_time, stt_framework, online_mode)

    else:
        print_version()
        print("Use --help to see available options.")


if __name__ == '__main__':
    main()