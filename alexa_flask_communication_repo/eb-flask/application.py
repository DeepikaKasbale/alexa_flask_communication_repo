import config
import handler
import json
import requests
from flask import Flask,request, Response, render_template, redirect


# Elastic Beanstalk initalization
application = Flask(__name__)
application.debug=True
application.secret_key = 'cC1YCIWOj9GgWspgNEo2DDDD'


@application.route('/', methods=['GET', 'POST'])
def index():
    """
    This is entry point function to every alexa json POST request.
    :return: JSON-formatted response required by alexa skill interface

    """
    try:
        event = json.loads(request.get_data())
        token_data = event.get("session").get("user")
        if event:
            if event['session']['new']:
                handler.on_session_started({'requestId': event['request']['requestId']},
                                           event['session'])
            if event['request']['type'] == "LaunchRequest":
                res = handler.on_launch(event['request'], event['session'])
            elif event['request']['type'] == "IntentRequest":
                res = handler.on_intent(event['request'], event['session'],token_data)
            elif event['request']['type'] == "SessionEndedRequest":
                res = handler.on_session_ended(event['request'], event['session'])
    except Exception as e:
        res = "Sorry for interruption. You can call other APIs "
    return Response(json.dumps(res), status=200, mimetype='application/json')


@application.route('/login', methods=['POST', 'GET'])
def login():
    """
    This function provides login functionality for our custom alexa skill.
    """
    if request.method == 'POST':
        args = request.args
        dict_args = args.to_dict(flat=False)
        url = config.SUITE_CRM_INSTANCE_OAUTH_URL
        header = {
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json"
        }
        payload = {
            "grant_type": "password",
            "client_id": str(dict_args.get("client_id")[0]) ,
            # Write here client_secret created in SuiteCRM portal under Oauth keys and client.
            "client_secret": "client_secret",
            "username": request.form['user_name'] ,
            "password":request.form['user_password'],
            "scope":str(dict_args.get("scope")[0])

        }
        try:
            result = requests.post(url, data=json.dumps(payload), headers=header)
            oauth_result_json = json.loads(result.text)
            redirect_uri = str(dict_args.get("redirect_uri")[0])+"#state="+str(dict_args.get("state")[0])+"&access_token=" +str(oauth_result_json.get("access_token")+"&token_type=Bearer")
            return redirect(redirect_uri,code=200)
        except Exception as e:
            render_template('login_template.html')
    return render_template('login_template.html')


if __name__ == '__main__':
    application.run(host='0.0.0.0')


