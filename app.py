from flask import Flask, request, jsonify
import os
import requests
import json
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

BearerToken = ""

dict_guidelines = {'generated_text': ['https://us-south.ml.cloud.ibm.com/ml/v1/deployments/lacajaprompt1/text/generation?version=2021-05-01']} 

def load_access():
    global BearerToken
    IBM_APIKEY = os.getenv('IBM_APIKEY')
    url = "https://iam.cloud.ibm.com/identity/token"
    payload = f'grant_type=urn%3Aibm%3Aparams%3Aoauth%3Agrant-type%3Aapikey&apikey={IBM_APIKEY}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(url, headers=headers, data=payload)
    BearerToken = response.json().get("access_token", "")
    if not BearerToken:
        print("Error: Unable to retrieve access token")
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

@app.route('/prompt', methods=['POST'])
def prompt_endpoint():
    data = request.get_json()
    input_text = data['input']
    result = ""
    
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
            
            # Debugging: Print the response JSON
            response_json = response.json()
            print("Response JSON from {}: {}".format(url, response_json))
            
            # Handle missing 'results' key
            if 'results' in response_json:
                result = response_json["results"][0].get("generated_text", "No generated text")
            else:
                result = "Error: 'results' key not found in response"
    
    return jsonify({'generated_text': result})

if __name__ == '__main__':
    load_access()
    app.run(debug=True)
