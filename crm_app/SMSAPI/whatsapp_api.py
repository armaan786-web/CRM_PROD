import requests


def send_whatsapp_message(mobile_number, message):
    print("tetingggg", mobile_number)
    url = "https://api.bulkwhatsapp.net/wapp/api/send"

    payload_data = {
        "apikey": "e0c31251049e44b9a02ed485e127d02f",
        "mobile": mobile_number,
        "msg": message,
        # Add other payload parameters as needed
    }

    response = requests.post(url, data=payload_data)
    print("REWSPONSEE", response)

    return response


def send_sms_message(mobile, message):
    print("demooooooo")
    url = "https://api.bulkwhatsapp.net/wapp/api/send"

    payload_data = {
        "apikey": "lbwUbocDLNFjenpa",
        "senderid": "SKTRAL",
        "templateid": "1007184056708073105",
        "mobile": mobile,
        "msg": message,
        # Add other payload parameters as needed
    }
    print("ssssssgg")

    response2 = requests.post(url, data=payload_data)

    return response2
