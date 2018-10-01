import config
import isodate
import json
import jwt
import requests
import time


def isTimeFormat(input):
    """
    This is function to check given input in proper format(HH:MM) or not.
    :param input: time formatted string
        :type: string
    :return: Boolean value
    """
    try:
        time.strptime(input, '%H:%M')
        return True
    except ValueError:
        return False


# --------------- Helpers that build all of the responses ----------------------
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    """
    This function help us to build a speechlet response.

    :param title: String visible on echo display device
    :param output: The object containing the speech to render to the user.
    :param reprompt_text: Text to be repromted if the your service keeps the session open
     after sending the response, but the user does not respond.
    :param should_end_session: A boolean value with true meaning that the session should end
     after Alexa speaks the response, or false if the session should remain active. If not provided, defaults to true.

    :return: Dictionary object to build response parameter.

    """
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
        "card": {
            "type": "Simple",
            "title": "SessionSpeechlet - " + title,
            "content": "SessionSpeechlet - " + output
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }


def build_response(session_attributes, speechlet_response):
    """
    This is method to buid a response.

    :param session_attributes: A map of key-value pairs to persist in the session.
    :param speechlet_response: A response object that defines what to render to the user.

    :return: Dictionary object containing required parameters in Alexa acceptable response format.
    """
    final_response = {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response" : speechlet_response
    }
    return final_response


def build_speechlet_response_for_dialog(title, output, should_end_session,slot_dict):
    """
    This method to buid a response specifically when dialog interaction is there.

    :return: Dictionary object containing required parameters in Alexa acceptable response format.
    """
    return {
        'shouldEndSession': should_end_session,
        "directives":  [
                        {
                        "type": "Dialog.Delegate",
                        "updatedIntent": {
                            "name": "MakeACake",
                            "confirmationStatus": "NONE",
                            "slots":
                                slot_dict
                            }
                      }
                    ]
    }


def build_response_for_dialog(message):
    res = {
        'version': '1.0',
        'sessionAttributes': {},
        'response': message
    }
    return res


def continue_dialog():
    message = {
        'shouldEndSession': False,
        'directives': [{'type': 'Dialog.Delegate'}]
    }
    return build_response_for_dialog(message)


def statement(title, body,should_end_session = True):
    speechlet = {
        'outputSpeech': {'type': 'PlainText', 'text': body},
        'card': {'type': 'Simple', 'title': title, 'content': body},
        'shouldEndSession': should_end_session
    }
    return build_response_for_dialog(speechlet)


def handle_session_end_request():
    """
    This is method to handle a request when CancelIntent or StopIntent is called.
    :return: JSON object containing required parameters in Alexa acceptable response format.

    """
    card_title = "Session Ended"
    speech_output = "Thank you for trying the Alexa Skills Kit sample. " \
                    "Have a nice day! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the Alexa Skills Kit for SUGAR CRM. "

    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Welcome to SUGAR CRM."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_help_response():
    session_attributes = {}
    card_title = "Help"
    speech_output = "Hello user, this alexa skill set will provide you information from sugar CRM." \
                    " This will include lead information, Meetings & calls scheduled, task related information. "
    reprompt_text = "This alexa skill set will provide you information from sugar CRM."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def format_suitecrm_response(data_list, prefix='',format_string = '',column_list=[]):
    """
    This method is used to beautify the data, coming as a response from SuiteCRM API call, in structured sentences.

    :param data_list: list containg data to be beautify.
        :type: list
    :param prefix: string to be added at the start of the sentence.
        :type: string
    :param format_string: string containing placeholders to be replaced with actual data.
        :type: string
    :param column_list: list of columns names.
        :type: list
    :return:
    """
    output_text = ""
    if not column_list:
        response_list = []
        for each_data in data_list:
            response_list.append(each_data[0])
        output_text += prefix + " " + (",".join(response_list))
    else:
        output_text = prefix
        for data_key, data_value in enumerate(data_list):
            format_new = format_string
            lstindex = len(data_value)
            for data_sub_key, data_sub_value in enumerate(data_value):
                format_new = format_new.replace('<' + column_list[data_sub_key] + '>', data_sub_value)
                if data_sub_key == (lstindex - 1):
                    output_text += format_new + '.'
    return output_text


def check_no_error(json_response_data):
    """
    Check for errors in API response.

    :param json_response_data: data returned as a response from SuiteCRM's API call.
    :return: True if there is no error in the response.
    """
    if json_response_data.get("error"):
        return "There is error in your request. Detailed description is " + str(json_response_data.get("message"))
    else:
        return True


def change_url(url_string):
    """
    Change IP based URL to https based domain URL.
    """
    return url_string.replace(config.SUITE_CRM_INSTANCE_IP_URL,config.SUITE_CRM_INSTANCE_BASE_URL)


def call_suitecrm_api(url,request_type, header_authorization_token, column_list=[],module_name=False,request_post_body={}):
    """
    This method allows to call SuiteCRMs API.

    :param url: request URL
    :param request_type: type of request i.e GET/POST/PATCH
    :param header_authorization_token: authentication token
    :param column_list: list of requested columns
    :param module_name: name of the module on which URL is operating.
    :param request_post_body: Dictionary containing data to be inserted in the suiteCRM database(in case of POST request).

    :return: JSON object containing response from API call.
    """
    header = {
        "Content-Type": "application/vnd.api+json",
        "Accept": "application/vnd.api+json",
        "Authorization": "Bearer " + str(header_authorization_token)
    }
    if request_type == 'GET':
        if column_list:
            url += '&fields[{0}]={1}'.format(module_name, (','.join(column_list)))
        suitecrm_response = requests.get(url, headers=header)
        suitecrm_data = json.loads(suitecrm_response.text)
        check_error_response = check_no_error(suitecrm_data)
        if isinstance(check_error_response, bool):
            if suitecrm_data:
                suitecrm_data_list = suitecrm_data.get("data")
                if suitecrm_data_list is not None:
                    output_response = []
                    for each_data_element in suitecrm_data_list:
                        attribute_dict = each_data_element.get("attributes")
                        attr_value_list = []
                        for column in column_list:
                            attr_value_list.append(attribute_dict.get(column))
                        output_response.append(attr_value_list)
                else:
                    output_response = "No data to show"
        else:
            output_response = check_error_response
    elif request_type == 'POST':
        suitecrm_response = requests.post(url, data= json.dumps(request_post_body) ,headers=header)
        output_response = json.loads(suitecrm_response.text)
    elif request_type == 'PATCH':
        suitecrm_response = requests.patch(url, data=json.dumps(request_post_body), headers=header)
        output_response = json.loads(suitecrm_response.text)
    return output_response


def get_leads(intent,token_data):
    """
    Get List of leads.

    :param intent: name of the intent
    :param token_data: authentication token
    """
    url = config.SUITE_CRM_INSTANCE_BASE_URL + "/api/v8/modules/Leads?page[limit]=5"
    suitecrm_lead_data = call_suitecrm_api(url,'GET',token_data,['name'],'Leads')
    if not isinstance(suitecrm_lead_data,str):
        output_text = format_suitecrm_response(suitecrm_lead_data,"The list of leads is as follows : ")
    else:
        output_text = suitecrm_lead_data
    return build_response({}, build_speechlet_response(
        intent['name'], output_text, output_text, False))


def get_meetings(intent, token_data):
    """
        Get List of meetings.

        :param intent: name of the intent
        :param token_data: authentication token
        """
    url = config.SUITE_CRM_INSTANCE_BASE_URL + "/api/v8/modules/Meetings?page[limit]=5"
    if intent.get('slots').get("datevalue") and intent.get('slots').get("datevalue").get('value'):
        requested_date = intent.get('slots').get("datevalue").get('value')
        url +="&filter[Meetings.date_start]=[[li]]{0}%".format(requested_date)
    suitecrm_lead_data = call_suitecrm_api(url, 'GET', token_data, ['name','date_start'], 'Meetings')
    if not isinstance(suitecrm_lead_data, str):
        format_string = '<name> on <date_start>'
        output_text = format_suitecrm_response(suitecrm_lead_data, "The list of meetings is as follows : ",format_string,['name','date_start'])
    else:
        output_text = suitecrm_lead_data
    return build_response({}, build_speechlet_response(
        intent['name'], output_text, output_text, False))


def post_request_details(intent,intent_dialogState,param_list,url,header_authorization_token,module_name,merge_datetime):
    """
    Method used to post a data into SuiteCRM.

    :param intent: name of the intent with slot information
    :param intent_dialogState: dialogState from intent request
    :param param_list: list of fields/columns
    :param url: request url of SuiteCRM API
    :param header_authorization_token: authentication token
    :param module_name: name of the module on which URL is operating.
    :param merge_datetime: boolean value whether to concatenate date and time or not.

    :return: JSON object
    """
    if intent_dialogState in ("STARTED", "IN_PROGRESS"):
        return continue_dialog()
    elif intent_dialogState == "COMPLETED":
        if intent.get("confirmationStatus") == "CONFIRMED":
            param_key_val_dict = {}
            for each_param in param_list:
                param_key_val_dict[each_param] = intent.get('slots').get(each_param).get('value')
            if merge_datetime:
                is_time = isTimeFormat(param_key_val_dict.get("time"))
                if is_time:
                    meeting_time = param_key_val_dict.get("time") + ':00'
                else:
                    meeting_time = "00:00:00"
                param_key_val_dict['date_start'] = param_key_val_dict.get("date") + " " + meeting_time
                param_key_val_dict.pop('date',None)
                param_key_val_dict.pop('time',None)

                duration = param_key_val_dict.get("duration")
                new_time = isodate.parse_duration(duration)
                days, seconds = new_time.days, new_time.seconds
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                param_key_val_dict['duration_hours'] = int(hours)
                param_key_val_dict['duration_minutes'] = int(minutes)
                param_key_val_dict.pop('duration', None)
            payload = jwt.decode(header_authorization_token, verify=False)
            if payload:
                user_db_id = payload.get('sub')
            try:
                request_body = {
                                    "data": {
                                        "type": module_name,
                                        "attributes": param_key_val_dict
                                    }
                                }
                result = call_suitecrm_api(url,'POST',header_authorization_token,request_post_body=request_body)
                if result.get("errors") or result.get("error"):
                    if result.get("error") == "access_denied":
                        return statement(intent.get("name"),result.get("error"))
                    else:
                        return statement(intent.get("name"), "Error in request creation. Reason "+(result.get("message") if result.get("message") else 'Not specified' ))
                else:
                    assigned_user_url = result.get("data").get("relationships").get("assigned_user_link").get("links").get("related")
                    changed_url = change_url(assigned_user_url)
                    request_body ={
                                    "data": {
                                            "type": "Users",
                                            "id": user_db_id,
                                            "links": {
                                                "href": config.SUITE_CRM_INSTANCE_BASE_URL+"/api/v8/modules/Users/"+str(user_db_id)
                                            }
                                    }
                                    }
                    result = call_suitecrm_api(changed_url, 'PATCH', header_authorization_token, request_post_body=request_body)
                    return statement(intent.get("name"), "Succesfully created",should_end_session=False)
            except Exception as e:
                return statement(intent.get("name"), "Inside try Your request is been cancelled")
        else:
            return statement(intent.get("name"), "If not CONFIRMED,Your request is been cancelled")
    else:
        return statement(intent.get("name"), "Error in posting meeting.")


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    res = "\n ** on_session_started requestId= " + session_started_request['requestId'] + ", sessionId=" + session['sessionId']
    return res


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """
    session_attributes = {}
    should_end_session = False
    # Dispatch to your skill's launch
    speech_output = " Welcome to the Alexa Skills Kit for SUGAR CRM. "
    reprompt_text = " Welcome to SUGAR CRM."
    return build_response(session_attributes, build_speechlet_response(
        "Welcome", speech_output, reprompt_text, should_end_session))


def on_intent(intent_request, session,token_data={}):
    """ Called when the user specifies an intent for this skill """
    intent = intent_request['intent']
    intent_dialogState = intent_request.get("dialogState")
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "SugarCrmLeadRequestIntent":
        return get_leads(intent, token_data.get("accessToken"))
    elif intent_name == "SugarCrmGetMeetingIntent":
        return get_meetings(intent, token_data.get("accessToken"))
    elif intent_name == "SugarCrmPostLeadIntent":
        url = config.SUITE_CRM_INSTANCE_BASE_URL + '/api/v8/modules/Leads'
        return post_request_details(intent, intent_dialogState, ['first_name', 'last_name', 'description'], url,
                                    token_data.get("accessToken"),'Leads',False)
    elif intent_name == "SugarCrmPostMeetingIntent":
        url = config.SUITE_CRM_INSTANCE_BASE_URL + '/api/v8/modules/Meetings'
        return post_request_details(intent, intent_dialogState, ['name','date', 'time', 'description','duration'], url,
                                    token_data.get("accessToken"), 'Meetings',True)
    elif intent_name == "AMAZON.HelpIntent":
        return get_help_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    session_attributes = {}
    should_end_session = True
    print("@ on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here
    output_text = "Thank you, Ending session here."
    return build_response(session_attributes, build_speechlet_response(
        'End session Intent', output_text, output_text, should_end_session))

