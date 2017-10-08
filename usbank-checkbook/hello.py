from cloudant import Cloudant
from flask import Flask, render_template, request, jsonify, abort, make_response, send_file
import atexit
import cf_deployment_tracker
import os
import requests
import json
from pymongo import MongoClient

# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

mongo_client = MongoClient(os.getenv('MONGO_URI'), ssl_ca_certs="./mongo_cert.crt")
mongo_db = mongo_client["users"]
mongo_col = mongo_db["details"]

db_name = 'mydb'
client = None
db = None

# this is just to support the app on bluemix
if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('Found local VCAP_SERVICES')
        creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)

# On Bluemix, get the port number from the environment variable PORT
# When running this app on the local machine, default the port to 8000
port = int(os.getenv('PORT', 8000))


@app.route('/')
def home():
    # return render_template('index.html')
    return jsonify({"message": "The app is running..."})


@app.route('/send/check', methods=["POST"])
def pay():
    req = request.form
    if not {'receiver_name', 'receiver_email', 'amount'} <= set(req):
        abort(400)
    # sender = mongo_col.find_one({"AccountOwnerEmail": "jill.anne.smolensky@gmail.com"})
    sender = mongo_col.find_one({"AccountOwnerEmail": "ronald.andrew.kalichak@gmail.com"})

    auth_keys = [sender.get("apikey"), sender.get("secret")]

    auth_header = {
        'Authorization': ':'.join(auth_keys)
    }
    payload = {
        'name': req['receiver_name'],
        'recipient': req['receiver_email'],
        'amount': float(req['amount'])
    }
    if req.get('description'):
        payload['description'] = req['description']

    resp = requests.post("https://sandbox.checkbook.io/v3/check/digital", headers=auth_header, json=payload)

    if resp.ok:
        img = requests.get(resp.json().get('image_uri'))
        IMPATH = 'check.png'
        with open(IMPATH, 'w') as f:
            f.write(img.content)
        return send_file(IMPATH, mimetype='image/png')
    else:
        abort(500)


# these methods aren't used, just there to support the app
@app.route('/api/visitors', methods=['GET'])
def get_visitor():
    if client:
        return jsonify(list(map(lambda doc: doc['name'], db)))
    else:
        print('No database')
        return jsonify([])


@app.route('/api/visitors', methods=['POST'])
def put_visitor():
    user = request.json['name']
    if client:
        data = {'name': user}
        db.create_document(data)
        return 'Hello %s! I added you to the database.' % user
    else:
        print('No database')
        return 'Hello %s!' % user


@atexit.register
def shutdown():
    if client:
        client.disconnect()


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.errorhandler(401)
def unauthorized(error):
    return make_response(jsonify({'error': 'Unauthorized: Invalid API key in `api-key` header'}), 401)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(500)
def internal_server_error(error):
    return make_response(jsonify({'error': 'Internal server error'}), 500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=False)
