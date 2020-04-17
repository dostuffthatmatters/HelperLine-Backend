from flask_backend import calls_collection, helper_behavior_collection, helper_accounts_collection
from flask_backend.database_scripts.call_scripts import dequeue
from flask_backend.database_scripts.hotline_scripts import enqueue
from flask_backend.support_functions import fetching, formatting

from bson.objectid import ObjectId
from pymongo import UpdateOne
from datetime import datetime, timezone, timedelta

# These scripts will just be used internally!

def accept_call(params_dict):
    # call_id and helper_id are assumed to be valid

    helper = helper_accounts_collection.find_one({'email': params_dict['email']})

    if helper is None:
        return formatting.server_error_helper_record

    dequeue_result = dequeue.dequeue(
        str(helper['_id']),
        zip_code=helper['account']['zip_code'],
        only_local_calls=params_dict['filter']['call_type']['only_local'],
        only_global_calls=params_dict['filter']['call_type']['only_global'],
        accept_german=params_dict['filter']['language']['german'],
        accept_english=params_dict['filter']['language']['english']
    )

    if dequeue_result['status'] != 'ok':
        return dequeue_result
    else:
        return fetching.get_all_helper_data(email=params_dict['email'])


def modify_call(params_dict):

    # Step 1) Check database correctness

    helper = helper_accounts_collection.find_one({"email": params_dict["email"]})
    if helper is None:
        return formatting.server_error_helper_record

    call = calls_collection.find_one({"_id": ObjectId(params_dict['call']["call_id"])})

    if call is None:
        return formatting.status("call_id invalid")



    # Step 2) Check eligibility to modify this call

    if str(call["helper_id"]) != str(helper["_id"]):
        return formatting.status("not authorized to edit this call")

    if (call["status"] == "fulfilled") and (params_dict['call']["action"] in ["reject", "fulfill"]):
        return formatting.status('cannot change a fulfilled call')



    # Step 2) Actually edit the call

    if params_dict['call']["action"] == "fulfill":
        fulfill_call(params_dict['call']["call_id"], helper["_id"])

    elif params_dict['call']["action"] == "reject":
        reject_call(params_dict['call']["call_id"], helper["_id"])

    elif params_dict['call']["action"] == "comment":
        comment_call(params_dict['call']["call_id"], params_dict['call']["comment"])

    return formatting.status("ok")


def fulfill_call(call_id, helper_id):
    # call_id and agent_id are assumed to be valid

    current_timestamp = datetime.now(timezone(timedelta(hours=2)))

    # Change call formatting.status
    call_update = {
        'status': 'fulfilled',
        'timestamp_fulfilled': current_timestamp
    }
    calls_collection.update_one({'_id': ObjectId(call_id)}, {'$set': call_update})

    new_behavior_log = {
        'helper_id': ObjectId(helper_id),
        'call_id': ObjectId(call_id),
        'timestamp': current_timestamp,
        'action': 'fulfilled',
    }
    helper_behavior_collection.insert_one(new_behavior_log)


def reject_call(call_id, helper_id):
    # Change call formatting.status
    call_update_dict_1 = {
        "$set": {
            'status': 'pending',
            'helper_id': 0,
            'comment': '',
        }
    }

    # accepted-match if local call was accepted from local queue (successful)
    # accepted-mismatch if local call was accepted from global/urgent queue (not successful)

    call_update_dict_2 = {
        "$pull": {
            "call_type": {"$in": ["forwarded", "accepted-match", "accepted-mismatch"]},
        }
    }

    operations = [
        UpdateOne({"_id": ObjectId(call_id)}, call_update_dict_1),
        UpdateOne({"_id": ObjectId(call_id)}, call_update_dict_2)
    ]
    calls_collection.bulk_write(operations)

    enqueue.enqueue(call_id)

    new_behavior_log = {
        'helper_id': ObjectId(helper_id),
        'call_id': ObjectId(call_id),
        'timestamp': datetime.now(timezone(timedelta(hours=2))),
        'action': 'rejected',
    }
    helper_behavior_collection.insert_one(new_behavior_log)


def comment_call(call_id, comment):
    calls_collection.update_one({'_id': ObjectId(call_id)}, {'$set': {'comment': comment}})


if __name__ == '__main__':
    call_id = '5e81e00cc40e18001ea76912'
    calls_collection.update_one({'_id': ObjectId(call_id)}, {'$set': {'feedback_granted': True}})
    print(calls_collection.find_one({'_id': ObjectId(call_id)}))
