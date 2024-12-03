import os
import uuid

import requests
import urllib3

from logger_setup import setup_logger

logger = setup_logger('gigachat_api')
# disable HTTPS check warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

TOKEN = os.getenv('GIGACHAT_TOKEN')


def post_get_token():
    rq_id = str(uuid.uuid4())
    logger.info(f"Starting get data TOKEN from API GIGACHAT. RqUID: {rq_id}")
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    headers = {
        'Authorization': 'Basic ' + TOKEN,
        'Content-Type': 'application/x-www-form-urlencoded',
        'RqUID': rq_id
    }

    data = {
        'scope': 'GIGACHAT_API_PERS'
    }

    try:
        response = requests.post(url, headers=headers, data=data, verify=False)

        if response.status_code == 200:
            response_json = response.json()
            access_token = response_json.get('access_token')
            expires_at = response_json.get('expires_at')

            if access_token and expires_at:
                logger.info(f"The token has been received. Expires At (Unix Time): {expires_at}")
                return access_token, expires_at
            else:
                logger.error("Response JSON does not contain expected fields.")
                return None
        else:
            logger.error(f"Failed to get a response. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"post_get_token() An error occurred: {e}")
        return None


def count_tokens(access_token, text):
    if not access_token:
        logger.error("No access token provided. Unable to proceed with counting tokens.")
        return None

    url = "https://gigachat.devices.sberbank.ru/api/v1/tokens/count"

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    data = {
        "model": "GigaChat",
        "input": [text]
    }

    try:
        response = requests.post(url, headers=headers, json=data, verify=False)

        if response.status_code == 200:
            response_json = response.json()

            if isinstance(response_json, list) and len(response_json) > 0:
                token_data = response_json[0]
                tokens_count = token_data.get('tokens')
                characters = token_data.get('characters')

                if tokens_count and characters:
                    logger.info(f"Token count: {tokens_count}, Characters count: {characters}")
                    return tokens_count, characters
                else:
                    logger.error("The token data does not contain expected fields.")
                    return None
            else:
                logger.error("Response is not in the expected format (list).")
                return None
        else:
            logger.error(f"Failed to get a response. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"count_tokens() An error occurred: {e}")
        return None


def ask_chat(access_token, text):
    if not access_token:
        logger.error("No access token provided. Unable to proceed with asking chat.")
        return None

    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    headers = {
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    data = {
        "model": "GigaChat",
        "messages": [
            {
                "role": "user",
                "content": text
            }
        ],
        "stream": False,
        "repetition_penalty": 1
    }

    try:
        response = requests.post(url, headers=headers, json=data, verify=False)

        if response.status_code == 200:
            response_json = response.json()
            choices = response_json.get('choices')

            if choices and len(choices) > 0:
                chat_response = choices[0].get('message', {}).get('content')
                if chat_response:
                    logger.info(f"Received response from GigaChat: {chat_response}")
                    return chat_response
                else:
                    logger.error("The response does not contain content in message.")
                    return None
            else:
                logger.error("The response does not contain any choices.")
                return None
        else:
            logger.error(f"Failed to get a response. Status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"ask_chat() An error occurred: {e}")
        return None
