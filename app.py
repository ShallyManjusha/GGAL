from flask import Flask, request, jsonify
import os
import requests
import json
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

BearerToken = ""
IBM_APIKEY = os.getenv('IBM_APIKEY')

dict_guidelines = {'generated_text': ['https://us-south.ml.cloud.ibm.com/ml/v1/deployments/lacajaprompt1/text/generation?version=2021-05-01']} 

def load_access():
    global BearerToken
    url = "https://iam.cloud.ibm.com/identity/token"
    payload = f'grant_type=urn%3Aibm%3Aparams%3Aoauth%3Agrant-type%3Aapikey&apikey={IBM_APIKEY}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        BearerToken = response.json().get("access_token", "")
        if not BearerToken:
            print("Error: Unable to retrieve access token")
            print("Response:", response.json())
    else:
        print("Error: Failed to get access token")
        print("Response:", response.json())

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Deployed Prompt API is created"}), 200

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/load_access', methods=['GET'])
def load_access_endpoint():
    load_access()
    return jsonify({'BearerToken': BearerToken})

def refresh_token_if_expired(response):
    if response.status_code == 401:
        response_json = response.json()
        if 'errors' in response_json and response_json['errors'][0]['code'] in ['authentication_token_expired', 'authentication_no_token']:
            print("Token expired or not found, refreshing token...")
            load_access()
            return True
    return False

@app.route('/prompt', methods=['POST'])
def prompt_endpoint():
    data = request.get_json()
    input_text = data['input']
    result = ""
    response_details = {}
    
    for metric in dict_guidelines.keys():
        urls = dict_guidelines[metric]
        for url in urls:
            payload = json.dumps({
                "parameters": {
                    "prompt_variables": {
                        "input": input_text
                    }
                }
            })
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + BearerToken
            }
            response = requests.post(url, headers=headers, data=payload)
            
            if refresh_token_if_expired(response):
                headers['Authorization'] = 'Bearer ' + BearerToken
                response = requests.post(url, headers=headers, data=payload)
            
            response_json = response.json()
            response_details[url] = response_json
            
            if 'results' in response_json:
                result = response_json["results"][0].get("generated_text", "No generated text")
            else:
                result = "Error: 'results' key not found in response,Response JSON from {}: {}".format(url, response_json)
    
    
    return jsonify({
        'generated_text': result,
        'details': response_details
    })

if __name__ == '__main__':
    load_access()
    app.run(debug=True)
