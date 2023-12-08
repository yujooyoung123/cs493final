from google.cloud import datastore
from flask import Flask, request, jsonify, _request_ctx_stack
import requests

from functools import wraps
import json

from six.moves.urllib.request import urlopen
from flask_cors import cross_origin
from jose import jwt


import json
from os import environ as env
from werkzeug.exceptions import HTTPException

from dotenv import load_dotenv, find_dotenv
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import session
from flask import url_for
from authlib.integrations.flask_client import OAuth
from six.moves.urllib.parse import urlencode

app = Flask(__name__)
app.secret_key = 'SECRET_KEY'

client = datastore.Client()

LODGINGS = "lodgings"
BOATS = "boats"

# Update the values of the following 3 variables
CLIENT_ID = 'O0DBHBaRhOPQlUSXM5PNDGz5OYOklJAH'
CLIENT_SECRET = 'atdRsLnJCXUuNNM9G7pNaMtqOeWz6RJ5yRsKmZiS_kFBqTWLQgQKISXgj_yoXfKX'
DOMAIN = 'dev-fuzcjsbul6ub7xdw.us.auth0.com'
# For example
# DOMAIN = 'fall21.us.auth0.com'

ALGORITHMS = ["RS256"]

oauth = OAuth(app)

auth0 = oauth.register(
    'auth0',
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    api_base_url="https://" + DOMAIN,
    access_token_url="https://" + DOMAIN + "/oauth/token",
    authorize_url="https://" + DOMAIN + "/authorize",
    client_kwargs={
        'scope': 'openid profile email',
    },
)

# This code is adapted from https://auth0.com/docs/quickstart/backend/python/01-authorization?_ga=2.46956069.349333901.1589042886-466012638.1589042885#create-the-jwt-validation-decorator

class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

# Verify the JWT in the request's Authorization header
def verify_jwt(request):
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization'].split()
        token = auth_header[1]
    else:
        raise AuthError({"code": "no auth header",
                            "description":
                                "Authorization header is missing"}, 401)
    
    jsonurl = urlopen("https://"+ DOMAIN+"/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.JWTError:
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    if unverified_header["alg"] == "HS256":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Invalid header. "
                            "Use an RS256 signed JWT Access Token"}, 401)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=CLIENT_ID,
                issuer="https://"+ DOMAIN+"/"
            )
        except jwt.ExpiredSignatureError:
            raise AuthError({"code": "token_expired",
                            "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                            "description":
                                "incorrect claims,"
                                " please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
                            "description":
                                "Unable to parse authentication"
                                " token."}, 401)

        return payload
    else:
        raise AuthError({"code": "no_rsa_key",
                            "description":
                                "No RSA key in JWKS"}, 401)


@app.route('/')
def index():
    return "Please navigate to /login to use this API"\
    
@app.route('/boats', methods=['POST', 'GET'])
def post_get_boat():
    if request.method == 'POST':
        payload = verify_jwt(request)

        content = request.get_json()

        new_boat = datastore.entity.Entity(key=client.key(BOATS))
        new_boat.update({
            "name": content["name"],
            "type": content["type"],
            "length": content["length"],
            "public": content["public"],
            "owner": payload["sub"]
        })
        client.put(new_boat)
        new_boat["id"] = int(new_boat.key.id)
        client.put(new_boat)
        return ({
            "owner": payload["sub"],
            "id": str(new_boat.key.id)
        }, 201)
    
    elif request.method == 'GET':
        try:
            payload = verify_jwt(request)
            owner_id_query = client.query(kind=BOATS)
            results = list(owner_id_query.fetch())
            response = []

            for index in results:      
                if index["owner"] == payload["sub"]:
                    response.append({
                        "id": index["id"],
                        "name": index["name"],
                        "type": index["type"],
                        "length": index["length"],
                        "public": index["public"],
                        "owner": index["owner"]
                    })
                
            return (response, 200)
        
        except:
            owner_id_query = client.query(kind=BOATS)
            results = list(owner_id_query.fetch())
            response = []

            for index in results:
                if index["public"] == True:
                    response.append({
                        "id": index["id"],
                        "name": index["name"],
                        "type": index["type"],
                        "length": index["length"],
                        "public": index["public"],
                        "owner": index["owner"]
                    })
            
            return (response, 200)


@app.route('/owners/<owner_id>/boats', methods=['GET'])
def get_owners_public_boats(owner_id):
    if request.method == 'GET':
        owner_id_query = client.query(kind=BOATS)
        results = list(owner_id_query.fetch())
        response = []
        for index in results:
            if index["public"] is True and index["owner"] == owner_id:
                response.append({
                    "id": index["id"],
                    "name": index["name"],
                    "type": index["type"],
                    "length": index["length"],
                    "public": index["public"],
                    "owner": index["owner"]
                })

        return (response, 200)

@app.route('/boats/<boat_id>', methods=['DELETE'])
def delete_boat(boat_id):
    if request.method == 'DELETE':
        payload = verify_jwt(request)

        boat_key = client.key(BOATS, int(boat_id))
        boat = client.get(key=boat_key)

        if boat is None:
            return ({'Error': 'No boat with this boat_id exists'}, 403)
        
        if boat["owner"] != payload["sub"]:
            return ({"Error": "Boat is owned by someone else"}, 403)

        client.delete(boat_key)
        return ('', 204)

    # boat_query = client.query(kind=BOATS)
    # results = list(boat_query.fetch())

    # # for index in results:
    # #     if index["id"] == boat_id:
    # #         if payload["sub"] != index["owner"]:
    # #             return ({"Error": "Boat is owned by someone else"}, 403)
            
    # #         boat_key = client.key(BOATS, int(boat_id))
    # #         boat = client.get(key=boat_key)
    # #         client.delete(boat_key)
        
    # # return ({"Error": "No boat with this boat_id exists"}, 403)


# Decode the JWT supplied in the Authorization header
@app.route('/decode', methods=['GET'])
def decode_jwt():
    payload = verify_jwt(request)
    return payload          
        

# Generate a JWT from the Auth0 domain and return it
# Request: JSON body with 2 properties with "username" and "password"
#       of a user registered with this Auth0 domain
# Response: JSON with the JWT as the value of the property id_token

@app.route('/login', methods=['POST'])
def login_user():
    content = request.get_json()
    username = content["username"]
    password = content["password"]
    body = {'grant_type':'password',
            'username':username,
            'password':password,
            'client_id':CLIENT_ID,
            'client_secret':CLIENT_SECRET
           }
    headers = { 'content-type': 'application/json' }
    url = 'https://' + DOMAIN + '/oauth/token'
    r = requests.post(url, json=body, headers=headers)
    return r.text, 200, {'Content-Type':'application/json'}

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

