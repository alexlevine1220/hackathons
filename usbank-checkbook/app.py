from flask import Flask, request, jsonify, abort, make_response, send_file
import cf_deployment_tracker
import os
import requests
from pymongo import MongoClient

# Emit Bluemix deployment event
cf_deployment_tracker.track()

app = Flask(__name__)

mongo_client = MongoClient(os.getenv('MONGO_URI'), ssl_ca_certs="./mongo_cert.crt")
mongo_db = mongo_client["users"]
mongo_col = mongo_db["details"]

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
        IMPATH = 'check2.png'
        # TODO: Actually serve live check (currently serving static check)
        # since otherwise we need to add a delay until check is ready
        # img = requests.get(resp.json().get('image_uri'))
        # if img.ok:
        #     with open(IMPATH, 'wb') as f:
        #         f.write(img.content)
        return send_file(IMPATH, mimetype='image/png')
    else:
        abort(500)


@app.route('/check', methods=['GET'])
def serve_check_image():
    return send_file('check2.png', mimetype='image/png')


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
