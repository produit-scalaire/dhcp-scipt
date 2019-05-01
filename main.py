#!/usr/bin/env python3
import os
from configparser import ConfigParser
import logging
import socket

from re2oapi import Re2oAPIClient

LOG_LEVEL = logging.INFO

logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)
formatter = logging.Formatter('%(levelname)s :: %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(LOG_LEVEL)
logger.addHandler(stream_handler)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

config = ConfigParser()
config.read(os.path.join(BASE_DIR, 'config.ini'))

api_hostname = config.get('Re2o', 'hostname')
api_password = config.get('Re2o', 'password')
api_username = config.get('Re2o', 'username')

def regen_dhcp(api_client):
    host_mac_ip = {}

    for hmi in api_client.list("dhcp/hostmacip/"):
        if hmi['extension'] not in host_mac_ip.keys():
            host_mac_ip[hmi['extension']] = []
        host_mac_ip[hmi['extension']].append((hmi['hostname'],
                                              hmi['mac_address'],
                                              hmi['ipv4']))

    template = ("host {hostname}{extension} {{\n"
                "    hardware ethernet {mac_address};\n"
                "    fixed-address {ipv4};\n"
                "}}")

    for extension, hmi_list in host_mac_ip.items():
        dhcp_leases_content = '\n\n'.join(template.format(
                hostname=hostname,
                extension=extension,
                mac_address=mac_address,
                ipv4=ipv4
            ) for hostname, mac_address, ipv4 in hmi_list)

        filename = os.path.join(BASE_DIR, 'generated/dhcp{extension}.list'.format(extension=extension))
        with open(filename, 'w+') as f:
            f.write(dhcp_leases_content)

api_client = Re2oAPIClient(api_hostname, api_username, api_password)

client_hostname = socket.gethostname().split('.', 1)[0]

for service in api_client.list("services/regen", params=dict(hostname=client_hostname)):
    if service['service_name'] == 'dhcp' and service['need_regen']:
        logger.info("Regenerating service dhcp")
        regen_dhcp(api_client)
        api_client.patch(service['api_url'], data={'need_regen': False})
