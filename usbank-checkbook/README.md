# Hack Your Tomorrow (usbank-checkbook)

This is our submission for US Bank's [Hack Your Tomorrow](http://hackyourtomorrow.com). 
The idea is to use [US Bank's APIs](https://usbinnovation.apiportal.akana.com/#/home/landing?index.htm)
to get real-world users who use Checkbook APIs to simulate integration with
US Bank's app.

**DISCLAIMER**: This is hacky, happy-path programming, so untested side-effects 
are likely to occur anywhere outside of documented usage. :)

## Prerequisites

You'll need the following:
* [Bluemix account]()
* [Bluemix CloudFoundry app](https://console.bluemix.net/apps/0fd78d1b-7654-4790-a4ac-0f1335b69d3c?paneId=overview&ace_config=%7B%22region%22%3A%22us-south%22%2C%22orgGuid%22%3A%223c7aad52-e795-4f7b-b304-b06b8f6a81b9%22%2C%22spaceGuid%22%3A%22a4bf6624-e298-4880-9c12-5cf9131dadec%22%2C%22redirect%22%3A%22https%3A%2F%2Fconsole.bluemix.net%2Fdashboard%2Fcf-apps%3Fenv_id%3Dibm%253Ayp%253Aus-south%22%2C%22bluemixUIVersion%22%3A%22Atlas%22%7D&env_id=ibm:yp:us-south)
* [Bluemix cheat-sheet](https://github.com/LennartFr/BlueMix-cheat-sheet/blob/master/README.md)
* [MongoDB credentials](): Value of environment variable `MONGO_URI`
* [MongoDB SSL certificate](): Contents of file `mongo_cert.crt` at the top level

The app appends to [this Bluemix starter app](https://github.com/IBM-Bluemix/get-started-python) 
so that deployment is straightforward (`bluemix app push usbank-checkbook`) - and free.

`hello.py` is the Python 2.7 entrypoint script, running on port 8000 by default.

There's a MongoDB Compose.io instance deployed and connected to our Bluemix app.

After setting the `MONGO_URI` environment variable locally and through the Bluemix CLI 
(`bluemix app set-env usbank-checkbook MONGO_URI <value>`),
we run `utils/populate_mongo_with_usbank_users.py`. This populates the MongoDB
instance (`db`: `users`, `collection`: `details`) with user information from
US Bank's API. 

We then choose one or more users and create email accounts
and Checkbook accounts for them, and store the `apikey` and `secret` for
those users in their corresponding MongoDB record.

Once this is done, we hardcode the email address for this demo user as `sender`
in `POST /send/check` in `hello.py` and we're good to go. 

| **HTTP Verb** | **Endpoint**  | **Description**                                        |
|---------------|---------------|--------------------------------------------------------|
| `GET`         | `/`           | Health check                                           |
| `POST`        | `/send/check` | Send digital check to recipient from hardcoded sender  |

**Health check (GET)**

    GET /

**Request**

https://usbank-checkbook.mybluemix.net/

**Response**

```json
{
    "message": "The app is running..."
}
```

**Send digital check to recipient from hardcoded sender (POST)**

    POST /send/check

**Request**

https://usbank-checkbook.mybluemix.net/send/check

```json
curl -X POST \
  https://usbank-checkbook.mybluemix.net/send/check \
  -H 'content-type: application/x-www-form-urlencoded' \
  -d 'receiver_name=Raunaq&receiver_email=rvohra@checkbook.io&amount=5.00&description=Lulz'
```

The `description` field above is optional. Missing any of the other three 
keys results in a `400 Bad Request` error.

**Response**

```
<image-of-check-from-response.image_uri-displayed-in-front-end>
```
