#==============================================================================
# Beat Master: Alexa metronome skill.
#==============================================================================

#----------- Globals ------------#
session_attributes={'tempo':60}

#----------- Lambda function entry ------------#
def lambda_handler(event, context):
    # Check to make sure function was called from correct app ID
    if (event['session']['application']['applicationId'] !=
        "amzn1.ask.skill.4c81166c-b26f-4847-996c-41ff54752aaf"):
        raise ValueError("Invalid Application ID")
    
    if event["session"]["new"]:
        on_session_started({"requestId": event["request"]["requestId"]}, event["session"])

    if event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    elif event["request"]["type"] == "IntentRequest":
        return on_intent(event["request"], event["session"])
    elif event["request"]["type"] == "SessionEndedRequest":
        return on_session_ended(event["request"], event["session"])

#----------- Events Routing ------------#

def on_session_started(session_started_request, session):
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])

def on_session_ended(session_ended_request, session):
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])

def on_launch(launch_request, session):
    return get_welcome_response()

def on_intent(intent_request, session):
    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]

    if intent_name == "QueryTempoIntent":
        return current_tempo_response()
    elif intent_name == "PlayIntent":
        return play_metronome(intent)
    elif intent_name == "IncreaseTempoIntent":
        return change_tempo(intent, 1)
    elif intent_name == "DecreaseTempoIntent":
        return change_tempo(intent, -1)
    elif intent_name == "SetTempoIntent":
        return set_tempo_intent(intent)
    elif intent_name == "AMAZON.HelpIntent":
        return get_help_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid Intent")

#----------- Alexa Response Helpers ------------#

def build_speechlet_response(title, s_output, c_output, should_end_session, reprompt_text=""):
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": s_output
        },
        "card": {
            "type": "Simple",
            "title": title,
            "content": c_output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }

def build_speechlet_ssml_response(title, s_output, c_output, should_end_session, reprompt_text=""):
    return {
        "outputSpeech": {
            "type": "SSML",
            "ssml": s_output
        },
        "card": {
            "type": "Simple",
            "title": title,
            "content": c_output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }
    
def build_response(session_attributes, speechlet_response):
    return {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": speechlet_response
    }

#----------- Program Logic ------------#

def current_tempo_response():
    global session_attributes
    speech_output = ""
    card_output = ""
    card_title = "Beat Master"
    reprompt_text = ""
    should_end_session = False

    card_output = "The current tempo is %d beats per minute." % session_attributes["tempo"]
    speech_output = "<speak>%s</speak>" % card_output

    return build_response(session_attributes, build_speechlet_ssml_response(card_title, speech_output, card_output, should_end_session))

def beat(pause_in_ms):
    return ('<phoneme alphabet="ipa" ph="t">t</phoneme><break time="%dms"/>' % pause_in_ms)

# Since we can only wait up to 10 seconds, the slowest tempo is 6 bpm. 
def validate_tempo(tempo):
    return (tempo > 6 and tempo < 200) 

def tempo_out_of_bounds_response(tempo):
    global session_attributes
    card_title = "Beat Master" 
    reprompt_text = "Ask me to start a metronome at your desired tempo."
    should_end_session = False
    card_output = "Invalid tempo: %d BPM" % tempo
    speech_output = "<speak>I'm sorry, I cannot play the metronome at %d beats per minute. " \
                    "I can only play tempos between 6 and 200 beats per minute." \
                    "Please pick a different tempo" % tempo
    return build_response(session_attributes, build_speechlet_ssml_response(card_title, speech_output, card_output, should_end_session))

def invalid_tempo_response():
    global session_attributes
    card_title = "Beat Master" 
    reprompt_text = "Ask me to start a metronome at your desired tempo."
    should_end_session = False
    card_output = "Unparsed tempo"
    speech_output = "<speak>I'm sorry, I did not understand the tempo that you specified. Please try again.</speak>"
 
    return build_response(session_attributes, build_speechlet_ssml_response(card_title, speech_output, card_output, should_end_session))

def invalid_tempo_diff_response():
    global session_attributes
    card_title = "Beat Master" 
    reprompt_text = "Ask me to start a metronome at your desired tempo."
    should_end_session = False
    card_output = "Unparsed tempo change"
    speech_output = "<speak>I'm sorry, I did not understand the change that you specified. Please try again.</speak>"
 
    return build_response(session_attributes, build_speechlet_ssml_response(card_title, speech_output, card_output, should_end_session))

def play_metronome(intent):
    global session_attributes
    speech_output = ""
    card_output = ""
    card_title = "Beat Master"
    reprompt_text = ""
    should_end_session = False

    if "value" in intent["slots"]["bpm"]:
        try:
            session_attributes["tempo"] = int(intent["slots"]["bpm"]["value"])
        except:
            return invalid_tempo_response()       

    if not validate_tempo(session_attributes["tempo"]):
        return tempo_out_of_bounds_response(session_attributes["tempo"])

    else:
        card_output = "Playing metronome at %d BPM" % session_attributes["tempo"]

        # Pause adjusted for time it takes to say the beat 
        pause = 60 * 1000 / session_attributes["tempo"] - 340
        single_beat = beat(pause)
        
        # Unfortunately the outputSpeech field is limited to 8000 characters.
        num_beats = 100
        speech_output = "<speak>%s</speak>" % (single_beat * num_beats)
        
        return build_response(session_attributes, build_speechlet_ssml_response(card_title, speech_output, card_output, should_end_session))
    
def pause():
    global session_attributes
    speech_output = ""
    card_output = "Metronome paused"
    card_title = "Beat Master"  
    reprompt_text = "Ask me to start a metronome at your desired tempo."
    should_end_session = False
    
    return build_response(session_attributes, build_speechlet_ssml_response(card_title, speech_output, card_output, should_end_session))

def set_tempo(new_tempo):
    global session_attributes
    speech_output = ""
    card_output = ""
    card_title = "Beat Master"  
    reprompt_text = "Ask me to start a metronome at your desired tempo."
    should_end_session = False

    if not validate_tempo(tempo):
        return tempo_out_of_bounds_response(new_tempo)
    
    session_attributes["tempo"] = new_tempo 
    card_output = "Tempo set to %d BPM." % new_tempo
    speech_output = "<speak>The new tempo is %d beats per minute.</speak>" % new_tempo
    return build_response(session_attributes, build_speechlet_ssml_response(card_title, speech_output, card_output, should_end_session))

def set_tempo_intent(intent):
    if "value" in intent["slots"]["bpm"]:
        try:
            new_tempo = int(intent["slots"]["bpm"]["value"])
        except:
            return invalid_tempo_response()
    
    return set_tempo(new_tempo)

def change_tempo(intent, diredtion):
    global session_attributes
    
    if "value" in intent["slots"]["diff"]:
        try:
            diff = int(intent["slots"]["diff"]["value"])           
        except:
            return invalid_tempo_diff_response()    

    else:
        # Default diff is 8 bpm
        diff = 8

    new_tempo = session_attributes["tempo"] + direction * diff
    return set_tempo(new_tempo)
    
def get_welcome_response():
    card_title = "Beat Master - Welcome"
    speech_output = "I am the Beat Master! Tell me a tempo and I will start " \
                    "a metronome for you. What tempo would you like to start " \
                    "a metronome at?"
    reprompt_text = "Ask me to start a metronome at your desired tempo."
    should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, speech_output, should_end_session, reprompt_text))

def get_help_response():
    card_title = "Beat Master - Help"
    speech_output = "I am the Beat Master! " \
                    "You can ask me to play a metronome at your desired tempo. " \
                    "For example, you can ask me to start a metronome at 60 beats per minute. "
    reprompt_text = "Ask me to start a metronome at your desired tempo."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, speech_output, should_end_session, reprompt_text))

def handle_session_end_request():
    card_title = "Beat Master - Thanks"
    speech_output = "Thank you for using the Beat Master skill. " \
                    "See you next time!"
    should_end_session = True

    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, None, should_end_session))
