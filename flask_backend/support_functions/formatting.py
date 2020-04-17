
def status(text, **kwargs):
    status_dict = {'status': text}
    status_dict.update(kwargs)
    return status_dict


def status_code(status):
    if status == "ok":
        return 200

    if status[:6] == "server":
        return 500

    if status[:6] == "email/" and status[-7:] == "invalid":
        return 401

    return 400

def postprocess_response(response_dict, new_api_key=None):
    status_code = response_dict["status"]
    if status_code != 200:
        return status(response_dict["status"]), status_code

    if new_api_key is not None:
        response_dict.update({"api_key": new_api_key})

    return response_dict, status_code


language_conversion = {
    'de': 'german',
    'en-gb': 'english'
}

def twilio_language_to_string(twilio_language):
    if twilio_language not in language_conversion:
        return ''
    else:
        return language_conversion[twilio_language]


server_error_helper_record = status('server error', details='helper record not found after successful authentication')
