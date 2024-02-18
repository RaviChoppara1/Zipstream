import requests
from requests.auth import HTTPDigestAuth
import logging
import time

class UrlHandler:
    @staticmethod
    def retry(func):
        def wrapper(*args, **kwargs):
            retries = 2
            while retries > 0:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.error(f"Error: {e}. Retrying...")
                    retries -= 1
                    time.sleep(1)
            logging.error(f"Failed after retrying.")
            return None
        return wrapper

    @staticmethod
    @retry
    def Zipstream(profitCameraIP, profitCameraPort, username, password, strength):
        url = f"http://{profitCameraIP}:{profitCameraPort}/axis-cgi/zipstream/setstrength.cgi?schemaversion=1&strength={strength}&camera=1"
        try:
            response = requests.get(url, auth=HTTPDigestAuth(username, password))
            if response.status_code == 200:
                logging.info(f"Request success for {profitCameraIP}:{profitCameraPort}")
                return True
            else:
                logging.error(f"Request failed for {profitCameraIP}:{profitCameraPort} with status code: {response.status_code}")
                return False
        except Exception as e:
            logging.error(f"Error in Zipstream: {e}")
            return False
