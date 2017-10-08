import os
import json
import requests
from pymongo import MongoClient

mongo_client = MongoClient(os.getenv('MONGO_URI'), ssl_ca_certs="../mongo_cert.crt")
mongo_db = mongo_client["users"]
mongo_col = mongo_db["details"]


user_ids = requests.get("http://api119525live.gateway.akana.com:80/users").json()

john_doe_count = 0

for id_elem in user_ids.get("LegalParticipantIdentifierList"):

    accounts_payload = {"LegalParticipantIdentifier": id_elem}
    accounts_resp = requests.post("http://api119525live.gateway.akana.com:80/user/accounts",
                                  json=accounts_payload).json()

    for acc_item in accounts_resp.get("AccessibleAccountDetailList"):

        if acc_item.get("ProductCode") == "DDA":

            details_payload = {
                "ProductCode": acc_item.get("ProductCode"),
                "PrimaryIdentifier": acc_item.get("PrimaryIdentifier"),
                "OperatingCompanyIdentifier": acc_item.get("OperatingCompanyIdentifier")
            }
            details_resp = requests.post("http://api119521live.gateway.akana.com:80/api/v1/account/details",
                                         json=details_payload).json()

            record = {}
            address_title = details_resp.get("AccountDetail", {}).get("AddressAndTitle", {})

            record["Address"] = address_title.get("Address", None)
            record["AccountOwnerName"] = address_title.get("AccountTitle", "John Doe")

            if record["AccountOwnerName"] == "John Doe":
                john_doe_count += 1
                record["AccountOwnerEmail"] = "john.doe." + str(john_doe_count) + '@gmail.com'
            else:
                record["AccountOwnerEmail"] = '.'.join(record["AccountOwnerName"].rstrip().lower().split(" ")) + '@gmail.com'

            basic_account_details = details_resp.get("BasicAccountDetail", {})

            record["AccountStatusCode"] = basic_account_details.get("Codes", {}).get("AccountStatusCode", None)
            record["RelationshipCode"] = basic_account_details.get("Codes", {}).get("RelationshipCode", None)
            record["Category"] = basic_account_details.get("Codes", {}).get("CategoryDescription", None)

            record["AccessibleBalanceAmount"] = basic_account_details.get("Balances", {}
                                                                          ).get("AccessibleBalanceAmount", None)
            record["AvailableBalanceAmount"] = basic_account_details.get("Balances", {}
                                                                          ).get("AvailableBalanceAmount", None)

            record["AccountNumber"] = details_resp.get("PrimaryIdentifier")

            if mongo_col.find_one({"AccountOwnerName": record["AccountOwnerName"]}):
                if record["AccountOwnerName"] == "John Doe":
                    mongo_col.insert_one(record)
                    print "Inserted"
                else:
                    pass
            else:
                mongo_col.insert_one(record)
                print "Inserted"

print "Completed"
