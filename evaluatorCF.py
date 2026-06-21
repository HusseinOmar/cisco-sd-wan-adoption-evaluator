#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 Cisco and/or its affiliates.
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

__author__ = "Hussein Omar, CSS - EMEA"
__email__ = "husseino@cisco.com"
__version__ = "0.1.0"
__copyright__ = "Copyright (c) 2021 Cisco and/or its affiliates."
__license__ = "Cisco Sample Code License, Version 1.1"
# imports
# -----------------------------------------
from vAPI import main as vapi
from concurrent.futures import ThreadPoolExecutor
import json
from datetime import datetime
from pprint import pprint as pp

# --> Utility functions
# =======================


def parellel(func, myList):
    '''
    This funtion allows parallel processing of multiple
    for loop iterations.
    ==================================================
    "max_workers" defines the number of apis calls sent
    simlutaneously to vManage, please DON'T increase
    this value as it might affect vmanage functions
    ==================================================
    '''
    with ThreadPoolExecutor(max_workers=30) as exe:
        for item in myList:
            exe.submit(func, item)
# =======================


def timeStamp():
    dateTimeObj = datetime.now()
    timestampStr = dateTimeObj.strftime("%d%m%Y-%H%M%S")
    return timestampStr
# =======================


def writefile(data):
    reportName = 'report-'+timeStamp()+'.txt'
    with open(reportName, 'w', encoding='utf-8') as f:
        f.write(data)


# Core functions
# -----------------------------------------
def printLog(log):
    print("\033[40m" + "\033[33m" + '==> ' + log + "\033[0m")


def printLogVar(log, var):
    print("\033[40m" + "\033[33m" + '==> ' + log +
          "\033[1m" + "\033[1;36m" + f'{var}' + "\033[0m")


class Report():
    def __init__(self):
        self.session = vapi()
        self.completed = "\033[1m" + "\033[1;97m" + \
            "\033[1;42m" + "COMPLETED!" + "\033[0m"
        self.incomplete = "\033[1m" + "\033[1;97m" + \
            "\033[1;41m" + "INCOMPLETE!" + "\033[0m"
        self.notAssessed = "\033[1m" + "\033[1;97m" + \
            "\033[1;40m" + "NOT ASSESSED!" + "\033[0m"

    def runApi(self):
        printLog('Getting all Edge Routers information ... ')
        mountURL1 = '/dataservice/system/device/vedges'
        self.all_devices = self.session.getDataResponse(mountURL1)

        printLog('Getting all SD-WAN Controllers information ... ')
        mountURL2 = '/dataservice/system/device/controllers'
        self.all_controllers = self.session.getDataResponse(mountURL2)

        printLog('Getting all Feature templates information ... ')
        mountURL3 = '/dataservice/template/feature'
        self.all_features = self.session.getDataResponse(mountURL3)

        printLog('Getting Localized Policy information ... ')
        mountURL4 = '/dataservice/template/policy/vedge'
        self.devicesWithLocalPolicy = self.session.getDataResponse(mountURL4)

        printLog('Getting Centralized Policy information ... ')
        mountURL5 = '/dataservice/template/policy/vsmart'
        self.CentralizedPolicy = self.session.getDataResponse(mountURL5)

        printLog('Getting vManage information ... ')
        mountURL7 = '/dataservice/device/action/install/devices/vmanage'
        self.version = self.session.getDataResponse(mountURL7)[0]['version']

        printLog('Getting Organization Name information ... ')
        mountURL13 = '/dataservice/settings/configuration/organization'
        self.orgName = self.session.getDataResponse(mountURL13)[0]['org']

    def analyzeFeatureTemplates(self):
        self.controller_aaa = 0
        self.controller_syslog = 0
        self.controller_ntp = 0
        self.controller_snmp = 0
        self.edge_aaa = 0
        self.edge_syslog = 0
        self.edge_ntp = 0
        self.edge_snmp = 0

        def func(template):
            edge = 0
            controller = 0
            for dv in template['deviceType']:
                if dv == 'vsmart' or dv == 'vmanage':
                    controller = int(template['devicesAttached'])
                else:
                    edge = int(template['devicesAttached'])
                return controller, edge
        for template in self.all_features:
            if template['devicesAttached'] > 0:
                if template['templateType'] == 'aaa' or template['templateType'] == 'cedge_aaa':
                    controller_aaa, edge_aaa = func(template)
                    self.controller_aaa += controller_aaa
                    self.edge_aaa += edge_aaa
                if template['templateType'] == 'snmp' or template['templateType'] == 'cisco_snmp':
                    controller_snmp, edge_snmp = func(template)
                    self.controller_snmp += controller_snmp
                    self.edge_snmp += edge_snmp
                if template['templateType'] == 'logging' or template['templateType'] == 'cisco_logging':
                    controller_syslog, edge_syslog = func(template)
                    self.controller_syslog += controller_syslog
                    self.edge_syslog += edge_syslog
                if template['templateType'] == 'ntp' or template['templateType'] == 'cisco_ntp':
                    controller_ntp, edge_ntp = func(template)
                    self.controller_ntp += controller_ntp
                    self.edge_ntp += edge_ntp

    def checkEnabled(self, data):
        if data:
            return "Yes"
        else:
            return "No"

    def checkEmptyData(self, data):
        if data:
            return "Yes"
        else:
            return "No"

    def checkServiceVPN(self, deviceIp):
        printLogVar('Getting detailed device information for ', deviceIp)
        mountURL = f'/dataservice/device/interface/synced?deviceId={deviceIp}'
        data = self.session.getDataResponse(mountURL)
        numberOfServiceVPNs = 0
        for item in data:
            if int(item['vpn-id']) > 0 and int(item['vpn-id']) < 511:
                numberOfServiceVPNs += 1
            if int(item['vpn-id']) > 512 and int(item['vpn-id']) < 65528:
                numberOfServiceVPNs += 1
        return numberOfServiceVPNs

    def checkDeviceControlConnections(self, deviceIp):
        printLogVar('Checking Control connection information for ', deviceIp)
        mountURL = f'/dataservice/device/counters?deviceId={deviceIp}'
        data = self.session.getDataResponse(mountURL)[0]
        fullControlConnectivity = False
        partialControlConnectivity = False
        noControlConnections = False
        if int(data['number-vsmart-control-connections']) == 0:
            noControlConnections = True
        if int(data['number-vsmart-control-connections']) < int(data['expectedControlConnections']):
            partialControlConnectivity = True
        if int(data['number-vsmart-control-connections']) == int(data['expectedControlConnections']):
            fullControlConnectivity = True
        return fullControlConnectivity, partialControlConnectivity, noControlConnections

    def get_device_info(self):
        self.totalNumberOfDevices = len(self.all_devices)
        self.vManagedDevices = 0
        self.cliDevices = 0
        self.allActiveDevices = 0
        self.allReachableDevices = 0
        self.devicesWithServiceVPN = 0
        self.devicesWithFullControlConnectivity = 0
        self.devicesWithPartialControlConnectivity = 0
        self.implement4 = 0
        siteIds = set()

        def func(device):
            implement4 = {'check12': False, 'check13': False, 'check14': False, 'check15': False,
                          'check16': False, 'check17': False, 'check18': False, 'check19': False, }

            if device['configOperationMode'] == 'vmanage':
                self.vManagedDevices += 1
                implement4['check14'] = True
                implement4['check15'] = True
                implement4['check16'] = True
            if device['configOperationMode'] == 'cli':
                self.cliDevices += 1
                implement4['check14'] = False
                implement4['check15'] = False
                implement4['check16'] = False
            if device['configStatusMessage'] == "In Sync":
                implement4['check17'] = True
            if device['deviceIP']:
                self.allActiveDevices += 1
                implement4['check12'] = True
            if device['reachability'] == 'reachable':
                self.allReachableDevices += 1
                implement4['check19'] = True
            if self.checkServiceVPN(device['deviceIP']) > 0:
                self.devicesWithServiceVPN += 1
                implement4['check18'] = True
            if device['site-id']:
                siteIds.add(device['site-id'])

            check = self.checkDeviceControlConnections(device['deviceIP'])
            if check[0]:
                self.devicesWithFullControlConnectivity += 1
                implement4['check13'] = True
            if check[1]:
                self.devicesWithPartialControlConnectivity += 1
                implement4['check13'] = True
            if implement4['check12'] and implement4['check13'] and implement4['check14'] and implement4['check15'] and implement4['check16'] and implement4['check17']:
                self.implement4 += 1
        parellel(func, self.all_devices)
        self.allSites = len(siteIds)

    def get_controller_info(self):
        self.vBonds = 0
        self.vSmarts = 0
        self.vManages = 0
        for controller in self.all_controllers:
            try:
                if controller['deviceType'] == 'vbond':
                    self.vBonds += 1
                if controller['deviceType'] == 'vsmart':
                    self.vSmarts += 1
                if controller['deviceType'] == 'vmanage':
                    self.vManages += 1
            except:
                pass

    def getLocalPolicyInfo(self):
        devices = 0
        for item in self.devicesWithLocalPolicy:
            devices = devices + int(item['devicesAttached'])
        return devices

    def checkCentralizedPolicy(self):
        self.centralPolicyActive = False
        self.policyDefinition = []

        def checkPolicyDefinition(item):
            definition = json.loads(item)
            for item in definition['assembly']:
                self.policyDefinition.append(item['type'])

        def func(item):
            if item['isPolicyActivated'] == True:
                self.centralPolicyActive = True
                checkPolicyDefinition(item['policyDefinition'])
        parellel(func, self.CentralizedPolicy)

    def reportchecks(self):

        if self.orgName:
            self.check02 = self.completed
        else:
            self.check02 = self.incomplete

        if self.vManages > 0 and self.vSmarts > 0 and self.vBonds > 0:
            self.check03 = self.completed
        else:
            self.check03 = self.incomplete

        if (int(self.vManagedDevices))/(int(self.totalNumberOfDevices)) > 0.02:
            self.check04 = self.completed
        else:
            self.check04 = self.incomplete

        if self.devicesWithServiceVPN > 1:
            self.check05 = self.completed
        else:
            self.check05 = self.incomplete

        if self.getLocalPolicyInfo() > 1:
            self.check06 = self.completed
        else:
            self.check06 = self.incomplete

        if self.centralPolicyActive:
            self.check07 = self.completed
            self.check43 = self.completed
        else:
            self.check07 = self.incomplete
            self.check43 = self.incomplete

        if 'control' in self.policyDefinition:
            self.check08 = self.completed
        else:
            self.check08 = self.incomplete

        if 'cflowd' in self.policyDefinition:
            self.check09 = self.completed
        else:
            self.check09 = self.incomplete

        if 'data' in self.policyDefinition:
            self.check10 = self.completed
        else:
            self.check10 = self.incomplete

        if 'vpnMembershipGroup' in self.policyDefinition:
            self.check11 = self.completed
        else:
            self.check11 = self.incomplete

        if 'appRoute' in self.policyDefinition:
            self.check12 = self.completed
            self.check31 = self.completed
            self.check47 = self.completed

        else:
            self.check12 = self.incomplete
            self.check31 = self.incomplete
            self.check47 = self.incomplete

        if self.allSites > 2:
            self.check13 = self.completed
        else:
            self.check13 = self.incomplete

        if self.implement4 > 4:
            self.check14 = self.completed
            self.check15 = self.completed
            self.check16 = self.completed
            self.check17 = self.completed
            self.check18 = self.completed
            self.check19 = self.completed
            self.check20 = self.completed
            self.check21 = self.completed
        else:
            self.check14 = self.incomplete
            self.check15 = self.incomplete
            self.check16 = self.incomplete
            self.check17 = self.incomplete
            self.check18 = self.incomplete
            self.check19 = self.incomplete
            self.check20 = self.incomplete
            self.check21 = self.incomplete

        if self.allSites > 3:
            self.check22 = self.completed
        else:
            self.check22 = self.incomplete

        if self.implement4 > 4:
            self.check23 = self.completed
            self.check24 = self.completed
            self.check25 = self.completed
            self.check26 = self.completed
            self.check27 = self.completed
            self.check28 = self.completed
            self.check29 = self.completed
            self.check30 = self.completed
        else:
            self.check23 = self.incomplete
            self.check24 = self.incomplete
            self.check25 = self.incomplete
            self.check26 = self.incomplete
            self.check27 = self.incomplete
            self.check28 = self.incomplete
            self.check29 = self.incomplete
            self.check30 = self.incomplete

        if int(self.allReachableDevices)/(self.totalNumberOfDevices) >= 0.25:
            self.check32 = self.completed
        else:
            self.check32 = self.incomplete

        if int(self.allReachableDevices)/(self.totalNumberOfDevices) >= 0.7:
            self.check33 = self.completed
        else:
            self.check33 = self.incomplete

        if self.controller_syslog >= 2:
            self.check34 = self.completed
        else:
            self.check34 = self.incomplete

        if self.controller_snmp >= 2:
            self.check35 = self.completed
        else:
            self.check35 = self.incomplete

        if self.controller_aaa >= 2:
            self.check36 = self.completed
        else:
            self.check36 = self.incomplete

        if self.controller_ntp >= 2:
            self.check37 = self.completed
        else:
            self.check37 = self.incomplete

        if self.edge_syslog >= 2:
            self.check38 = self.completed
        else:
            self.check38 = self.incomplete

        if self.edge_snmp >= 2:
            self.check39 = self.completed
        else:
            self.check39 = self.incomplete

        if self.edge_aaa >= 2:
            self.check40 = self.completed
        else:
            self.check40 = self.incomplete

        if self.edge_ntp >= 2:
            self.check41 = self.completed
        else:
            self.check41 = self.incomplete

        if int(self.allReachableDevices)/(self.totalNumberOfDevices) >= 0.95:
            self.check42 = self.completed
        else:
            self.check42 = self.incomplete

        self.check44 = self.notAssessed
        self.check45 = self.notAssessed
        self.check46 = self.notAssessed
        self.check48 = self.notAssessed
        self.check49 = self.notAssessed

    def generateReport(self):
        reportText = f'''

\033[92m=================================================================================
=============== Cisco Catalyst SD-WAN LifeCycle Evaluation Report ===============
=================================================================================\033[0m

\033[92m==> On-Board Phase
==================\033[0m
\033[92m1- Learn about Cisco SD-WAN Secure Automated WAN (ATX/ACC)\033[0m
\033[92m2- Plan Your SD-WAN Project (ATX/ACC)\033[0m
\033[92m3- Create the SD-WAN overlay\033[0m
    - Verify Smart Account and Virtual Account exist for SDWAN overlay (Required) ==> {self.notAssessed}
    - Verify Organization Name is not blank (Required) ==> {self.check02}

\033[92m==> Implement Phase
====================\033[0m
\033[92m1- Verify the SD-WAN Controller installation\033[0m
    - At least 1 of each vSmart, vBond, and vManage is Active (Required) ==> {self.check03}
\033[92m2- Develope the Feature, device and local policy templates\033[0m
    - WAN Edge devices have at least 2% with assigned device template (Required) ==> {self.check04}
    - Service VPN is configured for at least 1 WAN edge device (Required) ==> {self.check05}
    - Local Policy is configured for at least 1 WAN edge device (Required) ==> {self.check06}
\033[92m3- Create vSmart centralized policies for secure Automated WAN\033[0m
    - Verify the central control policy on vSmart:
        - vSmart Policy must be active (Required) ==> {self.check07}

    - OR at least one of the following policy types should be included in the vSmart central policy (Recommended)
        - Control policy is enabled (Recommended) ==> {self.check08}
        - cFlowd policy is enabled (Recommended) ==> {self.check09}
        - Data policy is enabled (Recommended) ==> {self.check10}
        - VPN Membership policy is enabled (Recommended) ==> {self.check11}
        - App Route policy is enabled (Recommended) ==> {self.check12}

\033[92m4- Create aditional sites with WAN Edge routers\033[0m
    - Verify at least 2 sites are operational for the overlay (Required) ==> {self.check13}
    - Check that at least 4 WAN edge devices have the following
        - WAN Edge is Active (Required) ==> {self.check14}
        - WAN Edge control plane is operational (Required) ==> {self.check15}
        - WAN Edge device has a template assigned (Required) ==> {self.check16}
        - WAN Edge device is not in CLI mode (Required) ==> {self.check17}
        - WAN Edge device is in vManage mode (Required) ==> {self.check18}
        - WAN Edge device is in sync and not pending to sync or out of sync (Required) ==> {self.check19}
        - WAN Edge device has a service VPN configured (Required) ==> {self.check20}
        - WAN Edge device has an up interface (Required) ==> {self.check21}


\033[92m==> Use Phase
=============\033[0m
\033[92m1- Learn About using SD-WAN (ATX/ACC)\033[0m
\033[92m2- Deploy additional sites with WAN Edges to the SD-WAN\033[0m
    - Verify at least 3 sites are operational for the overlay (Required) ==> {self.check22}
    - Check that at least 6 WAN edge devices have the following
        - WAN Edge is Active (Required) ==> {self.check23}
        - WAN Edge control plane is operational (Required) ==> {self.check24}
        - WAN Edge device has a template assigned (Required) ==> {self.check25}
        - WAN Edge device is not in CLI mode (Required) ==> {self.check26}
        - WAN Edge device is in vManage mode (Required) ==> {self.check27}
        - WAN Edge device is in sync and not pending to sync or out of sync (Required) ==> {self.check28}
        - WAN Edge device has a service VPN configured (Required) ==> {self.check29}
        - WAN Edge device has an up interface (Required) ==> {self.check30}
\033[92m3- Enable Application Performance Routing on the SD-WAN\033[0m
    - Verify that application aware route policy is applied (Recommended) ==> {self.check31}
\033[92m4- Monitor the SD-WAN Fabric\033[0m
    - 25% or more of WAN edge devices have connected to Catalyst SDWAN Manager (Recommended) ==> {self.check32}

\033[92m==> Engage Phase
================\033[0m
\033[92m1- Operationalize the network at scale\033[0m
    - 70% of WAN edge devices have connected to Catalyst SDWAN Manager (Recommended) ==> {self.check33}
    - For controllers
        - check is syslog is configured (Required) ==> {self.check34}
        - check if SNMP is configured (Required) ==> {self.check35}
        - check if AAA is configured (Required) ==> {self.check36}
        - check if NTP is configured (Required) ==> {self.check37}
    - For WAN edge devices at lease 6 have the following
        - check if Syslog is configured (Required) ==> {self.check38}
        - check is SNMP is configured (Required) ==> {self.check39}
        - check is AAA is configured (Required) ==> {self.check40}
        - check if NTP is configured (Required) ==> {self.check41}
\033[92m2- Learn About advanced features (ATX/ACC)\033[0m

\033[92m==> Adopt Phase
===============\033[0m
\033[92m1- Learn about integration, health checks (ATX/ACC)\033[0m
\033[92m2- Deploy Advanced Features of Application performance Optimization\033[0m
    - 95% or more WAN edge devices have connected to Catalyst SDWAN Manager (Recommended) ==> {self.check42}
    - vSmart Policy is active and in use (Required) ==> {self.check43}
    - Check if Forward Error Correction is enabled (Recommended) ==> {self.check44}
    - Check if Packet Duplication is enabled (Recommended) ==> {self.check45}
    - Check if TCP Optimization is enabled (Recommended) ==> {self.check46}
\033[92m3- Deploy basic features of other SD-WAN Use cases\033[0m
    - Check if vSmart policy contains an AppRoute policy (Recommended) ==> {self.check47}
    - Check if IPS/IDS is enabled (Recommended) ==> {self.check48}
    - Check if Firewall is enabled (Recommended) ==> {self.check49}
    - Check if Cloud OnRamp for SaaS is enabled (Recommended) ==> {self.notAssessed}

\033[92m==> Optimize Phase
==================\033[0m
\033[92m1- Learn about secure automated WAN performance (ATX/ACC)\033[0m
\033[92m2- Optimize Perfomance of SLA based Application routing policy\033[0m
    - Validate that vAnalytics is enabled (Required) ==> {self.notAssessed}    
        '''

        reportAdditionalInfor = f'''
\033[95m=================================================================================
================ Cisco Catalyst SD-WAN - Additioinal Information ================
=================================================================================\033[0m

\033[95mDeployment information
======================\033[0m
- Organization name: \033[95m{self.orgName}\033[0m
- Current Software Version: \033[95m{self.version}\033[0m
- Deployment Type: {self.notAssessed}
- Smart Account Integration Enabled: {self.notAssessed}
- Telemetry Enabled: {self.notAssessed}

\033[95mController information
======================\033[0m
- Number of vManage Nodes: \033[95m{self.vManages}\033[0m
- Number of vBond Nodes: \033[95m{self.vBonds}\033[0m
- Number of vSmart Nodes: \033[95m{self.vSmarts}\033[0m

\033[95mDevices information
===================\033[0m
- Total Number of Devices: \033[95m{self.totalNumberOfDevices}\033[0m
- Number of Deployed Devices: \033[95m{self.allActiveDevices}\033[0m
- Number of Reachable Devices: \033[95m{self.allReachableDevices}\033[0m
- Number of Devices in vManage Mode: \033[95m{self.vManagedDevices}\033[0m
- Number of Devices in CLI Mode: \033[95m{self.cliDevices}\033[0m
- Number of sites: \033[95m{self.allSites}\033[0m

\033[95mDevices Health information
==========================\033[0m
- Number of devices with Service VPN: \033[95m{self.devicesWithServiceVPN}\033[0m
- Number of devices with Local Policy: \033[95m{self.getLocalPolicyInfo()}\033[0m
- Number of Devices with Full Control Connectivity: \033[95m{self.devicesWithFullControlConnectivity}\033[0m
- Number of Devices with Parial Control Connectivity: \033[95m{self.devicesWithPartialControlConnectivity}\033[0m
- Number of Devices (connected, reachable, vmanaged, in-sync): \033[95m{self.implement4}\033[0m

\033[95mPolicy information
==================\033[0m
- Is Centralized Policy Activated: \033[95m{self.centralPolicyActive}\033[0m
- Centralized Policy Definitions: \033[95m{self.policyDefinition}\033[0m

\033[95m]Operational Information
==================\033[0m
- Number of devices with AAA configured: \033[95m{self.edge_aaa}\033[0m
- Number of devices with Syslog configured: \033[95m{self.edge_syslog}\033[0m
- Number of devices with NTP configured: \033[95m{self.edge_ntp}\033[0m
- Number of devices with SNMP configured: \033[95m{self.edge_snmp}\033[0m

\033[95mService Integration information
================================\033[0m
- Umbrella Integration Enabled: {self.notAssessed}
- vAnalytics Integration Enabled: {self.notAssessed}
- SD-AVC Cloud Enabled: {self.notAssessed}
- Cloud onRamp for SaaS Enabled: {self.notAssessed}
    '''
        print(reportText)
        print(reportAdditionalInfor)
        writefile(reportText + reportAdditionalInfor)

    def runReport(self):
        self.runApi()
        self.get_device_info()
        self.get_controller_info()
        self.checkCentralizedPolicy()
        self.analyzeFeatureTemplates()
        self.reportchecks()
        self.generateReport()


report = Report()
report.runReport()
