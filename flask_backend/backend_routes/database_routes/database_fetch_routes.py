
from flask_backend import app
from flask_backend.database_scripts.account_scripts import account_scripts
from flask_backend.database_scripts.call_scripts import call_scripts
from flask_backend.database_scripts.settings_scripts import filter_scripts, forward_scripts
from flask_backend.database_scripts.performance_scripts import performance_scripts
from flask_backend.support_functions import routing, formatting, tokening

from flask import request


@app.route('/<api_version>/database/fetchall', methods=["GET"])
def route_database_fetchall(api_version):
    if api_version == "v1":

        params_dict = routing.get_params_dict(request)

        authentication_result = tokening.check_helper_api_key(params_dict, new_api_key=True)
        if authentication_result["status"] != "ok":
            return authentication_result

        email = params_dict['email']
        new_api_key = authentication_result['api_key']

        account_dict = account_scripts.get_account(email, new_api_key)
        calls_dict = call_scripts.get_calls(email, new_api_key)
        filter_dict = filter_scripts.get_filter(email, new_api_key)
        forward_dict = forward_scripts.get_forward(email, new_api_key)

        for result_dict in [account_dict, calls_dict, filter_dict, forward_dict]:
            if result_dict["status"] != "ok":
                return result_dict, 400

        performance_dict = performance_scripts.get_performance(account_dict["account"]["zip_code"])

        return formatting.status("ok",
                                 account=account_dict["account"],
                                 calls=calls_dict["calls"],
                                 filter=filter_dict["filter"],
                                 forward=forward_dict["forward"],
                                 performance=performance_dict["performance"]), 200
    else:
        return formatting.status("api_version invalid")


@app.route('/<api_version>/database/performance/<zip_code>', methods=["GET"])
def route_database_performance(api_version, zip_code):
    if api_version == "v1":
        performance_dict = performance_scripts.get_performance(zip_code)
        return formatting.status("ok", performance=performance_dict["performance"]), 200
    else:
        return formatting.status("api_version invalid")