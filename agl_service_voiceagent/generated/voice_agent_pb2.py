# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: voice_agent.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11voice_agent.proto\"\x07\n\x05\x45mpty\"C\n\rServiceStatus\x12\x0f\n\x07version\x18\x01 \x01(\t\x12\x0e\n\x06status\x18\x02 \x01(\x08\x12\x11\n\twake_word\x18\x03 \x01(\t\"^\n\nVoiceAudio\x12\x13\n\x0b\x61udio_chunk\x18\x01 \x01(\x0c\x12\x14\n\x0c\x61udio_format\x18\x02 \x01(\t\x12\x13\n\x0bsample_rate\x18\x03 \x01(\x05\x12\x10\n\x08language\x18\x04 \x01(\t\" \n\x0eWakeWordStatus\x12\x0e\n\x06status\x18\x01 \x01(\x08\"\x93\x01\n\x17S_RecognizeVoiceControl\x12!\n\x0c\x61udio_stream\x18\x01 \x01(\x0b\x32\x0b.VoiceAudio\x12\x1c\n\tnlu_model\x18\x02 \x01(\x0e\x32\t.NLUModel\x12\x11\n\tstream_id\x18\x03 \x01(\t\x12$\n\rstt_framework\x18\x04 \x01(\x0e\x32\r.STTFramework\"\xd1\x01\n\x15RecognizeVoiceControl\x12\x1d\n\x06\x61\x63tion\x18\x01 \x01(\x0e\x32\r.RecordAction\x12\x1c\n\tnlu_model\x18\x02 \x01(\x0e\x32\t.NLUModel\x12 \n\x0brecord_mode\x18\x03 \x01(\x0e\x32\x0b.RecordMode\x12\x11\n\tstream_id\x18\x04 \x01(\t\x12$\n\rstt_framework\x18\x05 \x01(\x0e\x32\r.STTFramework\x12 \n\x0bonline_mode\x18\x06 \x01(\x0e\x32\x0b.OnlineMode\"J\n\x14RecognizeTextControl\x12\x14\n\x0ctext_command\x18\x01 \x01(\t\x12\x1c\n\tnlu_model\x18\x02 \x01(\x0e\x32\t.NLUModel\")\n\nIntentSlot\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t\"\x8e\x01\n\x0fRecognizeResult\x12\x0f\n\x07\x63ommand\x18\x01 \x01(\t\x12\x0e\n\x06intent\x18\x02 \x01(\t\x12!\n\x0cintent_slots\x18\x03 \x03(\x0b\x32\x0b.IntentSlot\x12\x11\n\tstream_id\x18\x04 \x01(\t\x12$\n\x06status\x18\x05 \x01(\x0e\x32\x14.RecognizeStatusType\"A\n\x0c\x45xecuteInput\x12\x0e\n\x06intent\x18\x01 \x01(\t\x12!\n\x0cintent_slots\x18\x02 \x03(\x0b\x32\x0b.IntentSlot\"E\n\rExecuteResult\x12\x10\n\x08response\x18\x01 \x01(\t\x12\"\n\x06status\x18\x02 \x01(\x0e\x32\x12.ExecuteStatusType*%\n\x0cSTTFramework\x12\x08\n\x04VOSK\x10\x00\x12\x0b\n\x07WHISPER\x10\x01*%\n\nOnlineMode\x12\n\n\x06ONLINE\x10\x00\x12\x0b\n\x07OFFLINE\x10\x01*#\n\x0cRecordAction\x12\t\n\x05START\x10\x00\x12\x08\n\x04STOP\x10\x01*\x1f\n\x08NLUModel\x12\t\n\x05SNIPS\x10\x00\x12\x08\n\x04RASA\x10\x01*\"\n\nRecordMode\x12\n\n\x06MANUAL\x10\x00\x12\x08\n\x04\x41UTO\x10\x01*\xb4\x01\n\x13RecognizeStatusType\x12\r\n\tREC_ERROR\x10\x00\x12\x0f\n\x0bREC_SUCCESS\x10\x01\x12\x12\n\x0eREC_PROCESSING\x10\x02\x12\x18\n\x14VOICE_NOT_RECOGNIZED\x10\x03\x12\x19\n\x15INTENT_NOT_RECOGNIZED\x10\x04\x12\x17\n\x13TEXT_NOT_RECOGNIZED\x10\x05\x12\x1b\n\x17NLU_MODEL_NOT_SUPPORTED\x10\x06*\x82\x01\n\x11\x45xecuteStatusType\x12\x0e\n\nEXEC_ERROR\x10\x00\x12\x10\n\x0c\x45XEC_SUCCESS\x10\x01\x12\x14\n\x10KUKSA_CONN_ERROR\x10\x02\x12\x18\n\x14INTENT_NOT_SUPPORTED\x10\x03\x12\x1b\n\x17INTENT_SLOTS_INCOMPLETE\x10\x04\x32\xa4\x03\n\x11VoiceAgentService\x12,\n\x12\x43heckServiceStatus\x12\x06.Empty\x1a\x0e.ServiceStatus\x12\x34\n\x10S_DetectWakeWord\x12\x0b.VoiceAudio\x1a\x0f.WakeWordStatus(\x01\x30\x01\x12+\n\x0e\x44\x65tectWakeWord\x12\x06.Empty\x1a\x0f.WakeWordStatus0\x01\x12G\n\x17S_RecognizeVoiceCommand\x12\x18.S_RecognizeVoiceControl\x1a\x10.RecognizeResult(\x01\x12\x43\n\x15RecognizeVoiceCommand\x12\x16.RecognizeVoiceControl\x1a\x10.RecognizeResult(\x01\x12?\n\x14RecognizeTextCommand\x12\x15.RecognizeTextControl\x1a\x10.RecognizeResult\x12/\n\x0e\x45xecuteCommand\x12\r.ExecuteInput\x1a\x0e.ExecuteResultb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'voice_agent_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_STTFRAMEWORK']._serialized_start=993
  _globals['_STTFRAMEWORK']._serialized_end=1030
  _globals['_ONLINEMODE']._serialized_start=1032
  _globals['_ONLINEMODE']._serialized_end=1069
  _globals['_RECORDACTION']._serialized_start=1071
  _globals['_RECORDACTION']._serialized_end=1106
  _globals['_NLUMODEL']._serialized_start=1108
  _globals['_NLUMODEL']._serialized_end=1139
  _globals['_RECORDMODE']._serialized_start=1141
  _globals['_RECORDMODE']._serialized_end=1175
  _globals['_RECOGNIZESTATUSTYPE']._serialized_start=1178
  _globals['_RECOGNIZESTATUSTYPE']._serialized_end=1358
  _globals['_EXECUTESTATUSTYPE']._serialized_start=1361
  _globals['_EXECUTESTATUSTYPE']._serialized_end=1491
  _globals['_EMPTY']._serialized_start=21
  _globals['_EMPTY']._serialized_end=28
  _globals['_SERVICESTATUS']._serialized_start=30
  _globals['_SERVICESTATUS']._serialized_end=97
  _globals['_VOICEAUDIO']._serialized_start=99
  _globals['_VOICEAUDIO']._serialized_end=193
  _globals['_WAKEWORDSTATUS']._serialized_start=195
  _globals['_WAKEWORDSTATUS']._serialized_end=227
  _globals['_S_RECOGNIZEVOICECONTROL']._serialized_start=230
  _globals['_S_RECOGNIZEVOICECONTROL']._serialized_end=377
  _globals['_RECOGNIZEVOICECONTROL']._serialized_start=380
  _globals['_RECOGNIZEVOICECONTROL']._serialized_end=589
  _globals['_RECOGNIZETEXTCONTROL']._serialized_start=591
  _globals['_RECOGNIZETEXTCONTROL']._serialized_end=665
  _globals['_INTENTSLOT']._serialized_start=667
  _globals['_INTENTSLOT']._serialized_end=708
  _globals['_RECOGNIZERESULT']._serialized_start=711
  _globals['_RECOGNIZERESULT']._serialized_end=853
  _globals['_EXECUTEINPUT']._serialized_start=855
  _globals['_EXECUTEINPUT']._serialized_end=920
  _globals['_EXECUTERESULT']._serialized_start=922
  _globals['_EXECUTERESULT']._serialized_end=991
  _globals['_VOICEAGENTSERVICE']._serialized_start=1494
  _globals['_VOICEAGENTSERVICE']._serialized_end=1914
# @@protoc_insertion_point(module_scope)
