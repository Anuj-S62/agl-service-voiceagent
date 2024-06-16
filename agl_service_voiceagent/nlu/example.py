import snips_interface

text = "increase ac temperature by 10 precents"

snips_interfac = snips_interface.SnipsInterface("/Users/anujsolanki/agl-voiceagent/snips-model-agl/model")
intent_output = snips_interfac.extract_intent(text)

print(intent_output)