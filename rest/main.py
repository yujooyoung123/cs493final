from google.cloud import datastore
from flask import Flask, request, make_response
import json
import constants
from json2html import *

app = Flask(__name__)
client = datastore.Client()

@app.route('/')
def index():
    return "Please navigate to URL in actual use to use this API"

@app.route('/boats', methods=['POST', 'PUT', 'DELETE'])
def boats_put_post_delete():
    if request.method == 'POST':
        try:
            if request.mimetype != 'application/json':
                return ({    
                        "Error":  "The request object in an unsupported MIME type"
                        }
                        , 415)

            if request.headers["Accept"] != 'application/json' and request.headers["Accept"] != '*/*':
                return ({    
                        "Error":  "Client requested response in unsupported MIME type"
                        }
                        , 406)
    
            content = request.get_json()

            if not validate_name(content["name"]):
                return ({    
                        "Error":  "A boat with this name already exists"
                        }
                        , 403)
            
            valid_keys = ["name", "type", "length"]
            valid_chars = "abcdefghijklmnopqrstuvwxyz0123456789\
                           ABCDEFGHIJKLMNOPQRSTUVWXYZ "
            
            for index in content.keys():
                if index not in valid_keys:
                    return ({"Error": "The request contains an unsupported attribute"}, 400)
                
            for index in content["name"]:
                if index not in valid_chars:
                    return ({"Error": "The request name contains an unsupported character"}, 400)

            if len(content["name"]) > 25:
                return ({"Error": "The request name is too long (>25 characters)"}, 400)

            new_boat = datastore.entity.Entity(key=client.key(constants.boats))
            new_boat.update(
                {"name": content["name"],
                "type": content["type"],
                "length": content["length"]
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
                "id": int(new_boat.key.id)}
            
            return json.dumps(dict), 201
        
        except:
            return ({    
                    "Error":  "The request object is missing at least one of the required attributes"
                    }
                    , 400)
    
    elif request.method == 'DELETE' or request.method == 'PUT':
        return ({    
                "Error":  "Unsupported method"
                }
                , 405)
    
    else:
        return 'Method not recognized'

def validate_name(name):

    name_query = client.query(kind=constants.boats)
    results = list(name_query.fetch())
    boat_name_list = []

    for e in results:
        boat_name_list.append(e["name"])

    if name in boat_name_list:
        return False
    else:
        return True

@app.route('/boats/<id>', methods=['PUT', 'PATCH', 'DELETE', 'GET'])
def boats_put_delete_patch_get(id):

    if request.method == 'PUT':

        if request.mimetype != 'application/json':

            return ({    
                    "Error":  "The request object in an unsupported MIME type"
                    }
                    , 415)

        if request.headers["Accept"] != 'application/json' and request.headers["Accept"] != '*/*':

            return ({    
                    "Error":  "Client requested response in unsupported MIME type"
                    }
                    , 406)


        content = request.get_json()
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)

        # A note on why there is no added check for attempted change in ID:
        # The implementation of PUT in this REST API does not take into account
        # the body of the request containing and "id" attribute in its logic,
        # so the need to place a check for an "id" attribute in the request is 
        # unnecessary.

        valid_keys = ["name", "type", "length"]

        if len(content.keys()) != 3:
            return ({    
                    "Error":  "The request object is missing at least one of the required attributes/contains an unacceptable one or has an attribute that is not in an accepted format"
                    }, 400)

        for index in valid_keys:
            if index not in content.keys():
                return ({    
                        "Error":  "The request object is missing at least one of the required attributes/contains an unacceptable one or has an attribute that is not in an accepted format"
                        }, 400)
            
        if boat is None:
            return ({"Error": "No boat with this boat_id exists"}, 404)

        if not validate_name(content["name"]):
            return ({    
                    "Error":  "A boat with this name already exists"
                    }
                    , 403)
        
        valid_chars = "abcdefghijklmnopqrstuvwxyz0123456789\
                        ABCDEFGHIJKLMNOPQRSTUVWXYZ "
            
        for index in content["name"]:
            if index not in valid_chars:
                return ({"Error": "The request name contains an unsupported character"}, 400)

        if len(content["name"]) > 25:
            return ({"Error": "The request name is too long (>25 characters)"}, 400)

        boat.update({
             "name": content["name"],
             "type": content["type"],
             "length": content["length"]
             })
        
        dict = {
            "name": boat["name"],
            "type": boat["type"],
            "length": boat["length"],
            "self": boat["self"],
            "id": int(boat.key.id)}
        
        client.put(boat)
        response = make_response(json.dumps(dict))
        response.headers['Location'] = 'https://hw1-yujoo.ue.r.appspot.com/boats/' + str(boat.key.id)

        return (response, 303)
    
    elif request.method == 'PATCH':

        if request.mimetype != 'application/json':

            return ({    
                    "Error":  "The request object in an unsupported MIME type"
                    }
                    , 415)

        if request.headers["Accept"] != 'application/json' and request.headers["Accept"] != '*/*':

            return ({    
                    "Error":  "Client requested response in unsupported MIME type"
                    }
                    , 406)

        content = request.get_json()
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        
        if boat is None:
            return ({"Error": "No boat with this boat_id exists"}, 404)
        
        valid_keys = ["name", "type", "length"]
        for index in content.keys():
            if index not in valid_keys:
                return {"Error":  "The request object is missing at least one of the required attributes/contains an unacceptable one or has an attribute that is not in an accepted format"}, 400

        if not validate_name(content["name"]):
            return ({    
                    "Error":  "A boat with this name already exists"
                    }
                    , 403)
        
        valid_chars = "abcdefghijklmnopqrstuvwxyz0123456789\
                        ABCDEFGHIJKLMNOPQRSTUVWXYZ "
            
        for index in content["name"]:
            if index not in valid_chars:
                return ({"Error": "The request name contains an unsupported character"}, 400)

        if len(content["name"]) > 25:
            return ({"Error": "The request name is too long (>25 characters)"}, 400)
        
        for index in content.keys():
            boat[index] = content[index]

        dict = {
            "name": boat["name"],
            "type": boat["type"],
            "length": boat["length"],
            "self": boat["self"],
            "id": int(boat.key.id)}
        
        client.put(boat)
        response = make_response(json.dumps(dict))

        return response, 200
    
    elif request.method == 'DELETE':

        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        client.delete(boat_key)
        if boat is None:
            return ({'Error' : 'No boat with this boat_id exists'}, 404)
        return ('', 204)

    elif request.method == 'GET':

        if request.headers["Accept"] != 'application/json' and request.headers["Accept"] != '*/*' and request.headers["Accept"] != 'text/html':

            return ({    
                    "Error":  "Client requested response in unsupported MIME type"
                    }
                    , 406)
        
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)

        if boat is None:
            return ({"Error": "No boat with this boat_id exists"}, 404)

        if request.headers['Accept'] == 'application/json':
            res = make_response(json.dumps(boat))
            res.headers.set('Content-Type', 'application/json')
            return res, 200
        
        elif request.headers['Accept'] == 'text/html':
            res = make_response(json2html.convert(json = json.dumps(boat)))
            res.headers.set('Content-Type', 'text/html')
            return res, 200
        
    else:
        return 'Method not recognized'

def validate_name(name):

    name_query = client.query(kind=constants.boats)
    results = list(name_query.fetch())
    boat_name_list = []

    for e in results:
        boat_name_list.append(e["name"])

    if name in boat_name_list:
        return False
    else:
        return True
    
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)