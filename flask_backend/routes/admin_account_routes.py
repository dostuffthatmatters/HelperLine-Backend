from flask_backend import app, helper_accounts_collection, status, api
from flask import redirect, request

from flask_backend.routes import support_functions
from flask_backend.nosql_scripts.admin_account_scripts import api_authentication

import time



@app.route("/backend/login/admin", methods=["POST"])
def backend_admin_login():
    params_dict = support_functions.get_params_dict(request)

    # Artificial delay to further prevent brute forcing
    time.sleep(0.05)

    print(params_dict)

    email = params_dict["admin_email"]
    password = params_dict["admin_password"]
    api_key = params_dict["admin_api_key"]

    # Initial login
    if email is not None and password is not None:
        login_result_dict = api_authentication.admin_login_password(email, password)

    # Automatic re-login from webapp
    elif email is not None and api_key is not None:
        # TODO: Generate new API Key for every login request in production!
        login_result_dict = api_authentication.admin_login_api_key(email, api_key)

    else:
        login_result_dict = status("missing parameter admin_email/admin_password/admin_api_key")

    return login_result_dict, 200




@app.route("/backend/logout/admin", methods=["POST"])
def backend_admin_logout():
    params_dict = support_functions.get_params_dict(request)

    if "admin_email" not in params_dict or "admin_api_key" not in params_dict:
        return status("missing parameter admin_email/admin_api_key")

    api_authentication.admin_logout(params_dict["admin_email"], params_dict["admin_api_key"])
    return status("ok")


