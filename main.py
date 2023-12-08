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

LOADS = "loads"
BOATS = "boats"
USERS = "users"

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

# -------------------------------------------------------------------------------------------------------------------------------

def validate_boat_name(name):
    name_query = client.query(kind=BOATS)
    results = list(name_query.fetch())
    boat_name_list = []

    for e in results:
        boat_name_list.append(e["name"])

    if name in boat_name_list:
        return False
    else:
        return True
    
def validate_boat_credentials(content):
    valid_keys = ["name", "type", "length"]
    valid_chars = "abcdefghijklmnopqrstuvwxyz0123456789\
                    ABCDEFGHIJKLMNOPQRSTUVWXYZ "
    
    for index in content.keys():
        if index not in valid_keys:
            return ({"Error": "The request contains an unsupported attribute"}, 400)
    
    if len(content.keys()) != 3:
        return ({"Error": "Request has invalid number of attributes"}, 400)
        
    for index in content["name"]:
        if index not in valid_chars:
            return ({"Error": "The request name contains an unsupported character"}, 400)

    if len(content["name"]) > 25:
        return ({"Error": "The request name is too long (>25 characters)"}, 400)

    if content["length"] < 0:
        return({"Error": "The length of a boat cannot be negative"}, 400)
    
    if type(content["length"]) is not int:
        return({"Error": "Boat length must be integer value"}, 400)

@app.route('/users', methods=['GET'])
def get_users():

    user_query = client.query(kind=USERS)
    results = list(user_query.fetch())
    response = []
    for index in results:
        response.append({
            # "first_name": index["first_name"],
            # "last_name": index["last_name"],
            # "favorite_animal": index["favorite_animal"],
            "id": index["id"]
        })
            
    return (response, 200)

@app.route('/boats', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def crud_boats():
    payload = verify_jwt(request)

    if request.headers["Accept"] != 'application/json' and request.headers["Accept"] != '*/*':

        return ({    
                "Error":  "Client requested response in unsupported MIME type"
                }
                , 406)

    if request.method=='GET':
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
                    "owner": index["owner"],
                    "self": index["self"],
                    "loads": index["loads"]
                })
            
        return (response, 200)

    elif request.method=='POST':

        # if request.headers["Accept"] != 'application/json' and request.headers["Accept"] != '*/*':

        #     return ({    
        #             "Error":  "Client requested response in unsupported MIME type"
        #             }
        #             , 406)

        content = request.get_json()

        if not validate_boat_name(content["name"]):
                return ({    
                        "Error":  "A boat with this name already exists"
                        }
                        , 403)
        
        validate_boat_credentials(content)
    
        new_boat = datastore.entity.Entity(key=client.key(BOATS))
        new_boat.update({
            "name": content["name"],
            "type": content["type"],
            "length": content["length"],
            "owner": payload["sub"],
            "loads": []
        })
        client.put(new_boat)

        new_boat["id"] = int(new_boat.key.id)
        new_boat["self"] = "https://hw1-yujoo.ue.r.appspot.com/boats/" + str(new_boat.key.id)
        client.put(new_boat)

        dict = {
            "name": new_boat["name"],
            "type": new_boat["type"],
            "length": new_boat["length"],
            "self": new_boat["self"],
            "owner": new_boat["owner"],
            "id": int(new_boat.key.id),
            "loads": []
            }
            
        return json.dumps(dict), 201
    
    elif request.method=='PUT':
        
        # if request.headers["Accept"] != 'application/json' and request.headers["Accept"] != '*/*':

        #     return ({    
        #             "Error":  "Client requested response in unsupported MIME type"
        #             }
        #             , 406)
        
        content = request.get_json()
        boat_key = client.key(BOATS, int(id))
        boat = client.get(key=boat_key)

        if boat is None:
            return ({"Error": "No boat with this boat_id exists"}, 404)

        if not validate_boat_name(content["name"]):
                return ({    
                        "Error":  "A boat with this name already exists"
                        }
                        , 403)
        
        validate_boat_credentials(content)

        boat.update({
             "name": content["name"],
             "type": content["type"],
             "length": content["length"]
             })
        
        client.put(boat)
        
        dict = {
            "name": boat["name"],
            "type": boat["type"],
            "length": boat["length"],
            "self": boat["self"],
            "id": int(boat.key.id),
            "owner": boat["owner"],
            "loads": boat["loads"]}
        
        return json.dumps(dict), 200
    
    elif request.method=='PATCH':

        content = request.get_json()
        boat_key = client.key(BOATS, int(id))
        boat = client.get(key=boat_key)

        if boat is None:
            return ({"Error": "No boat with this boat_id exists"}, 404)
        
        if not validate_boat_name(content["name"]):
                return ({    
                        "Error":  "A boat with this name already exists"
                        }
                        , 403)
        
        validate_boat_credentials(content)

        for index in content.keys():
            boat[index] = content[index]

        dict = {
            "name": boat["name"],
            "type": boat["type"],
            "length": boat["length"],
            "self": boat["self"],
            "id": int(boat.key.id),
            "owner": boat["owner"],
            "loads": boat["loads"]}
        
        client.put(boat)

        return json.dumps(dict), 200

    elif request.method=='DELETE':
        boat_key = client.key(BOATS, int(id))
        boat = client.get(key=boat_key)
        client.delete(boat_key)
        if boat is None:
            return ({'Error' : 'No boat with this boat_id exists'}, 404)
        return ('', 204)
    
    else:
        return 'Method not recognized'

@app.route('/loads', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def crud_loads():
    if request.headers["Accept"] != 'application/json' and request.headers["Accept"] != '*/*':

        return ({    
                "Error":  "Client requested response in unsupported MIME type"
                }
                , 406)
    
    if request.method=='GET':
        # load_query = client.query(kind=LOADS)
        # results = list(load_query.fetch())
        # response = []

        # for index in results:      
        #     response.append({
        #         "id": index["id"],
        #         "name": index["name"],
        #         "type": index["type"],
        #         "length": index["length"],
        #         "owner": index["owner"],
        #         "self": index["self"],
        #         "loads": index["loads"]
        #     })
            
        # return (response, 200)
        pass
    
    elif request.method=='POST':

        content = request.get_json()
        new_load = datastore.entity.Entity(key=client.key(LOADS))
        new_load.update(
            {"volume": content["volume"],
            "item" : content["item"],
            "creation_date": content["creation_date"],
            "carrier": None
            })
        
        client.put(new_load)

        new_load["self"] = "https://fiery-radius-401600.ue.r.appspot.com/loads/" + str(new_load.key.id)
        new_load["id"] = int(new_load.key.id)

        client.put(new_load)
        dict = {
            "volume": content["volume"],
            "item" : content["item"],
            "creation_date": content["creation_date"],
            "id": int(new_load.key.id),
            "self": new_load["self"],
            "carrier": None}

        return json.dumps(dict), 201
    
    elif request.method=='PUT':
        content = request.get_json()
        load_key = client.key(LOADS, int(id))
        load = client.get(key=load_key)

        if load is None:
            return ({"Error": "No load with this load_id exists"}, 404)
        
        new_load.update(
            {"volume": content["volume"],
            "item" : content["item"],
            "creation_date": content["creation_date"],
            })

    elif request.method=='PATCH':

        content = request.get_json()
        load_key = client.key(LOADS, int(id))
        load = client.get(key=load_key)

        if load is None:
            return ({"Error": "No load with this load_id exists"}, 404)

        for index in content.keys():
            load[index] = content[index]
        
        client.put(load)

        dict = {
            "volume": load["volume"],
            "item" : load["item"],
            "creation_date": load["creation_date"],
            "id": int(load.key.id),
            "self": load["self"],
            "carrier": load["carrier"]
            }

        return json.dumps(dict), 201

    elif request.method=='DELETE':
        load_key = client.key(LOADS, int(id))
        load = client.get(key=load_key)
        client.delete(load_key)
        if load is None:
            return ({'Error' : 'No load with this load_id exists'}, 404)
        return ('', 204)
    
    else:
        return 'Method not recognized'

# -------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

