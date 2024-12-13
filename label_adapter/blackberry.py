
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from logging import Logger
from pathlib import Path
from uuid import uuid4
import requests
import time
import json
import jwt

class BlackBerryAPI:
    def __init__(self, key_file:Path, logger:Logger, test_level:str):
        self.base_url = 'https://api.radar.blackberry.com/1'
        self.logger = logger
        self.access_token = None
        self.key_file = key_file
        self.do_read = False
        self.do_write = False
        if test_level == 'not_test':
            self.do_read = True
            self.do_write = True
        elif test_level == 'read_only':
            self.do_read = True

    def generate_access_token(self, write_scope=False) -> str:
        self.logger.debug('Generating a new access key')
            
        if (not write_scope and self.do_read) or (write_scope and self.do_write):
            # Load Private Key
            with self.key_file.open("rb") as key_file:
                private_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=None,  # If your key has a password, add it here
                    backend=default_backend()
                )

            # Payload Construction
            payload = {
                "jti": str(uuid4()),
                "iss": "74d61af0-b906-434c-b6e7-8c00acbd575e",
                "sub": "74d61af0-b906-434c-b6e7-8c00acbd575e",
                "aud": "https://oauth2.radar.blackberry.com",
                "iat": int(time.time()),
                "exp": int(time.time()) + 60
            }

            # JWT Generation with ES256
            jwt_token = jwt.encode(
                payload=payload,
                key=private_key,
                algorithm="ES256"
            )
            
            # Set up the payload
            asset_scope = 'read'
            if write_scope: asset_scope = 'write'
            payload = {
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": jwt_token,
                "scope": f"modules:read assets:{asset_scope}"
            }

            # Convert the payload to JSON
            json_payload = json.dumps(payload)

            # Set the API endpoint URL
            url = "https://oauth2.radar.blackberry.com/1/token"

            # Define the headers (Content-Type for JSON payload)
            headers = {
                "Content-Type": "application/json"
            }

            # Make the POST request
            response = requests.post(url, headers=headers, data=json_payload)
        else:
            self.logger.info('Testing...')
            response = self.generate_access_token_test_response()

        if response.status_code == 200:
            self.logger.debug(f'Access token successfully generated:\n {self.log_request_response(response)}')
            return response.json().get('access_token')
        else:
            self.logger.error(f'Unable to generate access token. Response status:\n {self.log_request_response(response)}')
            return None
        
    def add_label(self, asset_id, new_label, retry=True):
        self.logger.debug(f'Adding label {new_label} to asset with ID {asset_id}')
        success = False
        
        if self.do_write:
            url = f'{self.base_url}/assets/{asset_id}/labels'
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            data = {
                "name": f"{new_label}"
            }
            response = requests.post(url, headers=headers, json=data)
        else:
            self.logger.info('Testing...')
            response = self.add_label_test_response()

        if response.status_code == 201:
            success = True
            self.logger.debug(f'Label added successfully:\n {self.log_request_response(response)}')
        elif (response.status_code == 401 or response.status_code == 403) and retry:
            self.logger.debug(f'Response status: {response.status_code} {response.text}')
            self.logger.debug('Attempting to add label again')
            self.access_token = self.generate_access_token(write_scope=True)
            success = self.add_label(asset_id, new_label, False)
        elif response.status_code == 409:
            self.logger.debug('Label already exists.')
        else:
            self.logger.error(f'Failed to create label:\n {self.log_request_response(response)}')
        return success
    
    # GET request
    def get_assets(self, retry=True):
        self.logger.debug('Retrieving assets')
        assets = {}
        
        if self.do_read:
            url = f'{self.base_url}/assets'
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers)
        else:
            self.logger.info('Testing...')
            response = self.get_assets_test_response()

        if response.status_code == 200:
            for x in response.json():
                assets[x['id']] = x['identifier']
            self.logger.debug(f'Assets retrieved successfully:\n {self.log_request_response(response)}')
        elif (response.status_code == 401 or response.status_code == 403) and retry:
            self.logger.debug(f'Response status: {response.status_code} {response.text}')
            self.logger.debug('Attempting to retrieve assets again')
            self.access_token = self.generate_access_token()
            assets = self.get_assets(False)
        else:
            self.logger.error(f'Failed to retrieve assets:\n {self.log_request_response(response)}')
        return assets

    # GET request
    def get_asset_labels(self, asset_id, retry=True):
        self.logger.debug(f'Retrieving asset labels for asset with ID {asset_id}')
        labels = {}
        
        if self.do_read:
            url = f'{self.base_url}/assets/{asset_id}/labels'
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            response = requests.get(url, headers=headers)
        else:
            self.logger.info('Testing...')
            response = self.get_asset_labels_test_response()
        if response.status_code == 200:
            items = response.json()['items']
            for x in items: labels[x['name']] = x['id']
            self.logger.debug(f'Asset labels retrieved successfully:\n {self.log_request_response(response)}')
        elif (response.status_code == 401 or response.status_code == 403) and retry:
            self.logger.debug(f'Response status: {response.status_code} {response.text}')
            self.logger.debug('Attempting to retrieve asset labels again')
            self.access_token = self.generate_access_token()
            labels = self.get_asset_labels(asset_id, False)
        else:
            self.logger.error(f'Failed to retrieve asset labels:\n {self.log_request_response(response)}')
        return labels

    # DELETE request
    def delete_label(self, asset_id, label_id, retry=True):
        self.logger.debug(f'Deleting label {label_id} from asset with ID {asset_id}')
        success = True
            
        if self.do_write:
            url = f'{self.base_url}/assets/{asset_id}/labels/{label_id}'
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            response = requests.delete(url, headers=headers)
        else:
            self.logger.info('Testing...')
            response = self.delete_label_test_response()

        if response.status_code == 204:
            success = True
            self.logger.debug(f"Label deleted successfully:\n {self.log_request_response(response)}")
        elif (response.status_code == 401 or response.status_code == 403) and retry:
            self.logger.debug(f'Response status: {response.status_code} {response.text}')
            self.logger.debug('Attempting to delete label again')
            self.access_token = self.generate_access_token(write_scope=True)
            success = self.delete_label(asset_id, label_id, False)
        else:
            self.logger.error(f'Failed to delete label:\n {self.log_request_response(response)}')
            success = False
        return success

    def log_request_response(self, response):
        if type(response) is self.TestResponse:
            res = f"---------------- Test Response ----------------\n"
            res += f"Status Code: {response.status_code}\n"
            res += f"JSON: {response.json()}"
        else:
            res = f"---------------- Request ----------------\n"
            res += f"Method: {response.request.method}\n"
            res += f"URL: {response.request.url}\n"
            res += f"Headers: {response.request.headers}\n"
            res += f"Body: {response.request.body}\n"
            res += f"---------------- Response ----------------\n"
            res += f"Status Code: {response.status_code}\n"
            res += f"Reason: {response.reason}\n"
            res += f"URL: {response.url}\n"
            res += f"Text: {response.text}"
        return res
    
    class TestResponse:
        def __init__(self, status_code:int, res_json=''):
            self.status_code = status_code
            try:
                self.res_json = json.loads(res_json)
            except Exception:
                self.res_json = ''
        def json(self):
            return self.res_json
        
    def generate_access_token_test_response(self):
        return self.TestResponse(200, '{"access_token":"TEST-TOKEN"}')

    def add_label_test_response(self):
        return self.TestResponse(201)
    
    def get_assets_test_response(self):
        res_json = '''
            [
                {"id": "123-456-001", "identifier": "26706"},
                {"id": "123-456-002", "identifier": "27317"},
                {"id": "123-456-003", "identifier": "27319"},
                {"id": "123-456-004", "identifier": "27320"},
                {"id": "123-456-005", "identifier": "47322"}
            ]
            '''
        return self.TestResponse(200, res_json)

    def get_asset_labels_test_response(self):
        res_json = '''
        {"items": [{"name": "PM Service and Inspect - 90%", "id": "555-123-456"}]}
        '''
        return self.TestResponse(200, res_json)
    
    def delete_label_test_response(self):
        return self.TestResponse(204)
    
