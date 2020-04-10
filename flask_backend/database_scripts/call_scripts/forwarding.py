
from flask_backend import helper_accounts_collection, calls_collection, helper_behavior_collection
from flask_backend.support_functions import fetching, formatting

from pymongo import UpdateOne
from bson import ObjectId
from datetime import datetime, timedelta


def set_online(params_dict):

    if 'filter_type_local' not in params_dict or 'filter_type_global' not in params_dict or \
            'filter_language_german' not in params_dict or 'filter_language_english' not in params_dict:
        return formatting.status('filters missing')

    helper = helper_accounts_collection.find_one({'email': params_dict['email']})

    if helper is None:
        return formatting.status('server error: helper record not found')

    if helper["phone_number"] == "" or not helper["phone_number_verified"] or not helper["phone_number_confirmed"]:
        return formatting.status("phone number not verified/confirmed")

    helper_update = {
        'filter_type_local': params_dict["filter_type_local"],
        'filter_type_global': params_dict["filter_type_global"],
        'filter_language_german': params_dict["filter_language_german"],
        'filter_language_english': params_dict["filter_language_english"],

        'online': True,
        'last_switched_online': datetime.now(),
    }
    helper_accounts_collection.update_one({'email': params_dict['email']}, {"$set": helper_update})

    return fetching.get_all_helper_data(email=params_dict['email'])


def set_offline(params_dict):
    helper_update = {
        'online': False,
    }
    helper_accounts_collection.update_one({'email': params_dict['email']}, {"$set": helper_update})

    return fetching.get_all_helper_data(email=params_dict['email'])


def find_forward_helper(call_id):
    # Returns formatting.status="ok" and helper phone number if helper was found
    # Returns formatting.status="no helper available" if no helper was found.


    call = calls_collection.find_one({"_id": ObjectId(call_id)})

    if call is None:
        return formatting.status("call_id invalid")




    # Step 1) Get call details

    language = call['language']

    language_dict = {}

    if language == "german":
        language_dict.update({"filter_language_german": True})
    if language == "english":
        language_dict.update({"filter_language_english": True})



    # Step 2) Construct helper query dict

    if "local" in call['call_type']:

        helper_query_dict = {
            "$and":
                [{
                    "online": True,
                    "last_switched_online": {"$gt": datetime.now() - timedelta(minutes=120)},

                    "zip_code": {"$in": fetching.get_adjacent_zip_codes(call['zip_code'])}
                }, {
                    "$or": [
                        {"filter_type_local": True},
                        {"filter_type_local": False}, {"filter_type_global": False},
                    ]
                }, language_dict]
        }

    elif "global" in call['call_type']:

        # Step 2) Find Helper

        helper_query_dict = {
            "$and":
                [{
                    "online": True,
                    "last_switched_online": {"$gt": datetime.now() - timedelta(minutes=120)},
                }, {
                    "$or": [
                        {"filter_type_global": True},
                        {"filter_type_local": False}, {"filter_type_global": False},
                    ]
                }, language_dict]
        }

    else:
        return formatting.status("call_type invalid")





    # Step 3) Find helper and switch him offline

    helper_update_dict = {
        "$set": {
            "online": False,
        }
    }

    helper = helper_accounts_collection.find_one_and_update(helper_query_dict, helper_update_dict)

    if helper is None:
        return formatting.status("no helper available")





    # Step 4) Update call (call_type, helper_id, formatting.status, timestamp_accepted)

    call_query_dict = {
        "_id": ObjectId(call_id)
    }

    call_update_dict_1 = {
        "$set": {
            "status": "accepted",
            "helper_id": ObjectId(helper["_id"]),
            "timestamp_accepted": datetime.now(),
        }
    }
    call_update_dict_2 = {
        "$push": {
            "call_type": "forwarded",
        }
    }

    operations = [
        UpdateOne(call_query_dict, call_update_dict_1),
        UpdateOne(call_query_dict, call_update_dict_2)
    ]
    calls_collection.bulk_write(operations)



    # Step 5) Add helper behavior (helper_id, call_id, timestamp, action='forwarded')

    new_behavior_log = {
        'helper_id': ObjectId(helper["_id"]),
        'call_id': ObjectId(call_id),
        'timestamp': datetime.now(),
        'action': 'forwarded',
    }
    helper_behavior_collection.insert_one(new_behavior_log)

    return formatting.status("ok", phone_number=helper["phone_number"], helper_id=str(helper["_id"]))



def flag_helper(call_id, helper_id, dial_call_status):
    new_behavior_log = {
        'helper_id': ObjectId(helper_id),
        'call_id': ObjectId(call_id),
        'timestamp': datetime.now(),
        'action': f'call not successful - DialCallStatus = {dial_call_status}',
    }
    helper_behavior_collection.insert_one(new_behavior_log)
