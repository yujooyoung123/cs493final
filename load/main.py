from google.cloud import datastore
from flask import Flask, request
import json
import constants

app = Flask(__name__)
client = datastore.Client()

@app.route('/')
def index():
    return "Please navigate to URL in actual use to use this API"

@app.route('/boats', methods=['POST','GET'])
def boats_get_post():
    if request.method == 'POST':
        try:
            content = request.get_json()
            new_boat = datastore.entity.Entity(key=client.key(constants.boats))
            new_boat.update(
                {"name": content["name"],
                "type": content["type"],
                "length": content["length"],
                "loads": []})
            client.put(new_boat)

            new_boat["id"] = int(new_boat.key.id)
            new_boat["self"] = "https://fiery-radius-401600.ue.r.appspot.com/boats/" + str(new_boat.key.id)

            client.put(new_boat)
            dict = {
                "name": new_boat["name"],
                "type": new_boat["type"],
                "length": new_boat["length"],
                "loads": new_boat["loads"],
                "self": new_boat["self"],
                "id": int(new_boat.key.id)}
            
            return dict, 201
        except:
            return ({"Error":"The request object is missing at least one of the required attributes"}, 400)
    
    elif request.method == 'GET':
        query = client.query(kind=constants.boats)
        results = list(query.fetch())
        for e in results:
            e["id"] = e.key.id

        offset = request.args.get("offset")
        if offset is None:
            offset = 0
        print(results)

        return paginate_boats(results, offset)
    
    else:
        return ('Error', 400)
    
def paginate_boats(results, offset):
    
    query = client.query(kind=constants.boats)
    results = list(query.fetch())
    for e in results:
        e["id"] = e.key.id

    if len(results) - int(offset) == 1:
        return {
            "boats":[
                results[int(offset)]
            ]
        }, 200

    elif len(results) - int(offset) == 2:
        return {
            "boats": [
                results[int(offset)],
                results[int(offset) + 1]
            ]
        }, 200

    else:
        return {
        "boats": [
            results[int(offset)],
            results[int(offset) + 1],
            results[int(offset) + 2]
        ],
        "next": f"https://fiery-radius-401600.ue.r.appspot.com/boats?offset={int(offset) + 3}"
    }, 200


@app.route('/boats/<id>', methods=['DELETE','GET'])
def boats_put_delete(id):

    if request.method == 'DELETE':
        try:

            boat_key = client.key(constants.boats, int(id))
            boat = client.get(key=boat_key)
            remove_deleted_boat_from_load(int(boat.key.id))
            client.delete(boat_key)
            
            return ('', 204)
        except:
            return ({'Error' : 'No boat with this boat_id exists'}, 404)

    elif request.method == 'GET':
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        if boat is None:
            return ({"Error": "No boat with this boat_id exists"}, 404)
        return json.dumps(boat)

    else:
        return 'Method not recognized'
    
def remove_deleted_boat_from_load(boat_id):

    slip_query = client.query(kind=constants.loads)
    results = list(slip_query.fetch())
    load_id_list = []

    for e in results:
        load_id_list.append(e.key.id)

    for index in load_id_list:
        load_key = client.key(constants.loads, int(index))
        load = client.get(key=load_key)

        if load["carrier"] is not None:
            if load["carrier"]["id"] == boat_id:
                load.update({
                "carrier" : None
                    })
                client.put(load)

                break
    
@app.route('/loads', methods=['POST','GET'])
def loads_get_post():
    if request.method == 'POST':
        try:

            content = request.get_json()
            new_load = datastore.entity.Entity(key=client.key(constants.loads))
            new_load.update(
                {"volume": content["volume"],
                "carrier": None,
                "item" : content["item"],
                "creation_date": content["creation_date"],
                "self": None
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

            return dict, 201
        except:
            return ({"Error":"The request object is missing at least one of the required attributes"}, 400)
        
    elif request.method == 'GET':
        query = client.query(kind=constants.loads)
        results = list(query.fetch())
        for e in results:
            e["id"] = e.key.id

        offset = request.args.get("offset")
        if offset is None:
            offset = 0

        return paginate_loads(results, offset)
    
    else:
        return 'Method not recognized'
    
def paginate_loads(results, offset):
    
    query = client.query(kind=constants.loads)
    results = list(query.fetch())
    for e in results:
        e["id"] = e.key.id

    if len(results) - int(offset) == 1:
        return {
            "loads":[
                results[int(offset)]
            ]
        }, 200

    elif len(results) - int(offset) == 2:
        return {
            "loads": [
                results[int(offset)],
                results[int(offset) + 1]
            ]
        }, 200

    else:
        return {
        "loads": [
            results[int(offset)],
            results[int(offset) + 1],
            results[int(offset) + 2]
        ],
        "next": f"https://fiery-radius-401600.ue.r.appspot.com/loads?offset={int(offset) + 3}"
    }, 200

@app.route('/loads/<id>', methods=['DELETE','GET'])
def loads_put_delete(id):

    if request.method == 'DELETE':
        try:
            load_key = client.key(constants.loads, int(id))
            load = client.get(key=load_key)
            remove_deleted_load_from_boat(int(load.key.id))
            client.delete(load_key)
            return ('', 204)
        except:
            return ({'Error' : 'No load with this load_id exists'}, 404)

    elif request.method == 'GET':
        load_key = client.key(constants.loads, int(id))
        load = client.get(key=load_key)
        if load is None:
            return ({"Error": "No load with this load_id exists"}, 404)
        return json.dumps(load)

    else:
        return 'Method not recognized'
    
def remove_deleted_load_from_boat(load_id):

    boat_query = client.query(kind=constants.boats)
    results = list(boat_query.fetch())
    boat_id_list = []
    for e in results:
        boat_id_list.append(e.key.id)
    
    for index in boat_id_list:
        boat_key = client.key(constants.boats, int(index))
        boat = client.get(key=boat_key)
        print(boat)
        if len(boat["loads"]) > 0: 
            for x in range(0, len(boat["loads"])):
                print(55, x)
                if boat["loads"][x]["id"] == load_id:
                    boat["loads"].pop(x)
                    client.put(boat)
                    break

@app.route('/boats/<boat_id>/loads/<load_id>', methods=['PUT', 'DELETE'])
def loads_and_boats(boat_id, load_id):
    if request.method == 'PUT':

        load_id = client.key(constants.loads, int(load_id))
        boat_key = client.key(constants.boats, int(boat_id))

        load = client.get(key=load_id)
        boat = client.get(key=boat_key)

        # list of boat ids
        boat_query = client.query(kind=constants.boats)
        results = list(boat_query.fetch())
        boat_id_list = []

        for e in results:
            boat_id_list.append(e.key.id)

        # list of load ids

        load_query = client.query(kind=constants.loads)
        results = list(load_query.fetch())
        loads_id_list = []

        for e in results:
            loads_id_list.append(e.key.id)
            
        try:
            int(load.key.id) not in loads_id_list
        except:
            return ({"Error" : "The specified boat and/or load does not exist"}, 404) 
        
        try:
            int(boat.key.id) not in boat_id_list
        except:
            return ({"Error" : "The specified boat and/or load does not exist"}, 404)

        if load["carrier"] is not None:
            return ({"Error": "The load is already loaded on another boat"}, 403)
        
        boat["loads"].append(
            {"id": load["id"],
             "self": load["self"],
             "creation_date": load["creation_date"],
             "volume": load["volume"],
             "item": load["item"]
             })
        
        load["carrier"] = {
            "id": boat["id"],
            "name": boat["name"],
            "self": boat["self"]
        }

        client.put(boat)
        client.put(load)

        return ('', 204)
    
    if request.method == 'DELETE':

        load_id = client.key(constants.loads, int(load_id))
        boat_key = client.key(constants.boats, int(boat_id))

        load = client.get(key=load_id)
        boat = client.get(key=boat_key)

        # list of boat ids
        boat_query = client.query(kind=constants.boats)
        results = list(boat_query.fetch())
        boat_id_list = []

        for e in results:
            boat_id_list.append(e.key.id)

        # list of load ids

        load_query = client.query(kind=constants.loads)
        results = list(load_query.fetch())
        loads_id_list = []

        for e in results:
            loads_id_list.append(e.key.id)
            
        try:
            int(load.key.id) not in loads_id_list
        except:
            return ({"Error" : "No boat with this boat_id is loaded with the load with this load_id"}, 404) 
        
        try:
            int(boat.key.id) not in boat_id_list
        except:
            return ({"Error" : "No boat with this boat_id is loaded with the load with this load_id"}, 404)   
        
        try:
            if int(boat.key.id) != load["carrier"]["id"]:
                return ({"Error" : "No boat with this boat_id is loaded with the load with this load_id"}, 404)     
        except:
            return ({"Error" : "No boat with this boat_id is loaded with the load with this load_id"}, 404)

        for index in range(0, len(boat["loads"])):
            if boat["loads"][index]["id"] == load["id"]:
                boat["loads"].pop(index)

        load["carrier"] = None

        client.put(boat)
        client.put(load)

        return ('', 204)
    
@app.route('/boats/<id>/loads', methods=['GET'])
def loads_of_boat(id):
    
    boat_key = client.key(constants.boats, int(id))
    boat = client.get(key=boat_key)
    if boat is None:
        return ({"Error": "No boat with this boat_id exists"}, 404)
    
    return (boat, 200)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)