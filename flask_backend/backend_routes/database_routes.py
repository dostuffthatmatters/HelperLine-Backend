
from flask_backend import app, api
from flask_backend.support_functions import formatting

from flask_backend.restful_resources.rest_account import RESTAccount
from flask_backend.restful_resources.rest_call import RESTCall


api.add_resource(RESTAccount, '/v1/database/account')
api.add_resource(RESTCall, '/v1/database/call')


@app.route('/<api_version>/database/fetchall', methods=["GET"])
def route_database_fetchall(api_version):
    if api_version == "v1":
        # TODO: Performance fetch + new api token
        return formatting.status("ok")
    else:
        return formatting.status("api_version invalid")


@app.route('/<api_version>/database/performance/<zip_code>', methods=["GET"])
def route_database_performance(api_version, zip_code):
    if api_version == "v1":
        # TODO: Performance fetch + new api token
        return formatting.status("ok")
    else:
        return formatting.status("api_version invalid")
