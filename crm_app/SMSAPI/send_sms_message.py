# cast = lead_status + " for enquiry ID " + enq_number

#         url = "http://sms.txly.in/vb/apikey.php"
#         payload = {
#             "apikey": "lbwUbocDLNFjenpa",
#             "senderid": "SKTRAL",
#             "templateid": "1007184056708073105",
#             "number": mob,
#             "message": f"Hello {full_name} , Your lead status is updated {cast} for TheSkyTrails CRM. Thank You",
#         }
#         response = requests.post(url, data=payload)


import requests


def send_sms_message(mobile_number, message):
    url = "https://api.bulkwhatsapp.net/wapp/api/send"

    payload_data = {
        "apikey": "lbwUbocDLNFjenpa",
        "senderid": "SKTRAL",
        "templateid": "1007184056708073105",
        "mobile": mobile_number,
        "msg": message,
        # Add other payload parameters as needed
    }

    response = requests.post(url, data=payload_data)

    return response
