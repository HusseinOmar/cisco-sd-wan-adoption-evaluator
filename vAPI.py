#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2023 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses

All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

__author__ = "Hussein Omar, CSS - ANZ"
__email__ = "husseino@cisco.com"
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2021 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"

# ---> Imports
# from pprint import pprint
# from datetime import datetime
# from threading import Thread
# import datetime
# import csv
import ipaddress
import getpass
import requests
# import itertools
import json


from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ---> Main Code


class vAPI():
    '''
    This class will instantiate an open API session with vManage.
    The session has the following methods:
    1- "Get Data Response" which returns the data element of the JSON response
    2- "Get Full Response" which returns the full JSON response
    3- "Post Request" which post specified payload
    3- "Delete Request" which deletes elements in vManage based on the Mount URL
    '''

    def __init__(self):
        '''
        print a welcome banner
        '''
        print('''
            Copyright (c) 2023 Cisco and/or its affiliates.
    This software is licensed to you under the terms of the Cisco Sample
    Code License, Version 1.1 (the "License"). You may obtain a copy of the
    License at
                   https://developer.cisco.com/docs/licenses

    All use of the material herein must be in accordance with the terms of
    the License. All rights not expressly granted by the License are
    reserved. Unless required by applicable law or agreed to separately in
    writing, software distributed under the License is distributed on an "AS
    IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
    or implied.
    |=================================================|
    |           Welcome to SD-WAN API tool            |
    | ------------------------------------------------|
    | This tool allows you to communicate with        |
    | vManage for login, GET, PUT, POST, DELETE verbs |
    | This code is under Cisco Sample Code license.   |
    | Please read the license agreement before using  |
    | the code in production environment.             |
    | For any questions please contact:               |
    | Hussein Omar on  husseino@cisco.com             |
    |=================================================|
        ''')
# Step 01: Get vManage Info

    def vManageInfo(self):
        '''
        Collect vManage Info and Handle login exceptions
        '''
        # Collection vManage IP address
        self.vmanage_ip = None
        print('')
        while self.vmanage_ip == None:

            vmanage_ip_typed = input('  - vManage IP address: ')
            try:
                self.vmanage_ip = ipaddress.ip_address(vmanage_ip_typed)
            except Exception:
                print(
                    f'ERROR: {vmanage_ip_typed} is not a correct IPv4 or IPv6 address')
        # Collection vManage Port Number
        self.port = None

        while self.port == None:
            self.port = input('  - Port Number (default 8443): ')
            if len(self.port) == 0:
                self.port = 8443
                break
            try:
                self.port = int(self.port)
                print('port number is integer')
                if self.port > 0 and self.port < 65535:
                    break
                else:
                    print('%% Please enter a port number between 1 and 65535')
                    self.port = None
                    continue
            except:
                print(f'%% {self.port} is not a valid port number')
                self.port = None
        print('')
        self.base_url = f'https://{self.vmanage_ip}:{self.port}'
        print(f'=> Logging to {self.base_url}')

# Step 02: Get Login Credintials

    def loginCred(self):
        print('')
        self.username = input('  - Username: ')
        self.password = getpass.getpass('  - Password: ')
        print('')


# Step 03: Connect to vManage


    def connect(self):
        '''
        - Initial first login to vManage and return authentication cookie
        '''
        mount_url = '/j_security_check'
        url = self.base_url + mount_url
        # Format data for loginForm
        payload = {'j_username': self.username, 'j_password': self.password}
        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
            'cache-control': "no-cache"
        }
        try:
            self.response = requests.request(
                "POST", url, data=payload, headers=headers, verify=False)
        except:
            print('')
            print(f' %% Failed to reach {self.vmanage_ip}:{self.port}')
            print('')
            return 0
        else:
            return self.response


# Step 04: Validate Login Credintials


    def validateLogin(self):
        try:
            if self.response.status_code >= 300:
                print('')
                print(f'%% Connection to {self.base_url} Failed')
                print('')
                return 0
            elif '<html>' in self.response.text:
                print('')
                print(f'%% Username or Password is wrong')
                print('')
                return 1
            else:
                self.cookie = str(self.response.cookies).split(' ')[1]
                print('--------------------------------------------------------------------')
                print(
                    f'Authenticated, login to {self.vmanage_ip}:{self.port} is SUCCESSFUL')
                print('--------------------------------------------------------------------')
                return 200
        except:
            pass
# For lab perposes
    def quickLogin(self):
        '''
        - for quick testing
        '''
        self.vmanage_ip = '198.18.133.200'
        self.port = 8443
        self.username = 'admin'
        self.password = 'pocadmin'
        self.base_url = f'https://{self.vmanage_ip}:{self.port}'
        vAPI.connect(self)
        vAPI.validateLogin(self)

# Step 05: Get Authetication Token
    def getToken(self):
        '''
        - Generate authentication token to be used in subsequent requests
        '''
        try:
            mount_url = '/dataservice/client/token'
            url = self.base_url + mount_url
            # Format data for loginForm
            payload = {}
            headers = {
                'Cookie': self.cookie,
            }
            self.response2 = requests.request(
                "GET", url, data=payload, headers=headers, verify=False)
            self.token = self.response2.text
        except:
            pass
# Do Authentication
    def auth(self):
        '''
        - First method to be called in main App
        - Returns session cookie and token
        '''
        valid = 0
        while valid == 0:
            vAPI.vManageInfo(self)
            vAPI.loginCred(self)
            connect = vAPI.connect(self)
            if connect == 0:
                continue
            else:
                valid = vAPI.validateLogin(self)
                if valid == 0:
                    continue
                elif valid == 1:
                    while valid == 1:
                        vAPI.loginCred(self)
                        vAPI.connect(self)
                        valid = vAPI.validateLogin(self)
        vAPI.getToken(self)
    def quickAuth(self):
        vAPI.quickLogin(self)
        vAPI.getToken(self)
#################################################################
#################### API calls Functions #######################

    def getDataResponse(self, mountURL):
        '''
        - Args: mounting URL
        - Construct full URL by adding mountURL to baseURL
        - Send a 'GET' request with empty payload with cookie and token
        - Return the data portion (dict) of the JSON response
        '''
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache",
            'X-XSRF-TOKEN': self.token,
            'Cookie': self.cookie
        }
        url = self.base_url + mountURL
        response = requests.request("GET", url, headers=headers, verify=False)
        data = json.loads(response.text)['data']
        return data

    def getFullResponse(self, mountURL):
        '''
        - Args: mounting URL
        - Construct full URL by adding mountURL to baseURL
        - Send a 'GET' request with empty payload with cookie and token
        - Return the data portion (dict) of the JSON response
        '''
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache",
            'X-XSRF-TOKEN': self.token,
            'Cookie': self.cookie
        }
        url = self.base_url + mountURL
        response = requests.request("GET", url, headers=headers, verify=False)
        return json.loads(response.text)

    def postRequest(self, mountURL, payload):
        '''
        This method takes payload for the POST request
        '''
        headers = {
            'Content-Type': "application/json",
            # 'cache-control': "no-cache",
            'X-XSRF-TOKEN': self.token,
            'Cookie': self.cookie
        }
        url = self.base_url + mountURL
        payload = json.dumps(payload)
        response = requests.request(
            "POST", url, headers=headers, data=payload, verify=False)
        return response

    def putRequest(self, mountURL, payload):
        '''
        This method takes payload for the PUT request
        '''
        headers = {
            'Content-Type': "application/json",
            'cache-control': "no-cache",
            'X-XSRF-TOKEN': self.token,
            'Cookie': self.cookie
        }
        url = self.base_url + mountURL
        response = requests.request(
            "PUT", url, headers=headers, data=payload, verify=False)
        return response

    def deleteRequest(self, mountURL):
        payload = {}
        headers = {
            'X-XSRF-TOKEN': self.token,
            'Cookie': self.cookie
        }
        url = self.base_url + mountURL
        response = requests.request(
            "DELETE", url, headers=headers, data=payload, verify=False)
        return response

#################################################################
################## Tools Functions ##############################
    def getKey(self, dict):
        return list(dict.keys())[0]

    def getValue(self, dict):
        return list(dict.values())[0]

    def readCsvFile(self, filename):
        return csv.DictReader(open(filename))

    def args(self):
        return sys.argv


def main():
    session = vAPI()
    session.auth()
    # session.quickAuth()
    return session


if __name__ == '__main__':
    main()
