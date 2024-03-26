#!/usr/bin/env python3
from configparser import ConfigParser
import socket
import psycopg2
from re2oapi import Re2oAPIClient

import sys
import os
import subprocess

conn = psycopg2.connect(
          user = "kea",
          password = "plopiplop",
          host = "localhost",
          database = "leasesdhcp"
    )
cursor = conn.cursor()

path =(os.path.dirname(os.path.abspath(__file__)))

config = ConfigParser()
config.read(path+'/config.ini')

api_hostname = config.get('Re2o', 'hostname')
api_password = config.get('Re2o', 'password')
api_username = config.get('Re2o', 'username')

def regen_dhcp(api_client):
    """Genere les fichiers de zone du DHCP, par extension et par plage d'ip"""
    host_mac_ip_ext = {}
    host_mac_ip_type = {}

    api_res = api_client.list("dhcp/hostmacip/")

    build_hmi(host_mac_ip_ext, api_res, 'extension')
    build_hmi(host_mac_ip_type, api_res, 'ip_type')

    update_bdd(host_mac_ip_ext)
    update_bdd(host_mac_ip_type)

def build_hmi(host_mac_ip, api_res, key):
    for hmi in api_res:
        if hmi[key] not in host_mac_ip.keys():
            host_mac_ip[hmi[key]] = []
        if 'ipv4' in hmi:
            host_mac_ip[hmi[key]].append((hmi['hostname'],
                                      hmi['extension'],
                                      hmi['mac_address'],
                                      hmi['ipv4']))
        

def update_bdd(host_mac_ip):
    cursor.execute("DELETE FROM hosts")
    for key, hmi_list in host_mac_ip.items():
        for hostname, extension, mac_address, ipv4 in hmi_list:
            cursor.execute("INSERT INTO hosts (dhcp_identifier, dhcp_identifier_type, ipv4_address, hostname) VALUES (DECODE(REPLACE(%s, ':', ''), 'hex'), (SELECT type FROM host_identifier_type WHERE name=%s), (SELECT (%s::inet - '0.0.0.0'::inet)), %s)", (mac_address, 'hw-address', ipv4, hostname + extension))
    conn.commit()


api_client = Re2oAPIClient(api_hostname, api_username, api_password, use_tls=True)

client_hostname = socket.gethostname().split('.', 1)[0]

for arg in sys.argv:
    if arg=="--force":
        regen_dhcp(api_client)

for service in api_client.list("services/regen/"):
    if service['hostname'] == client_hostname and \
            service['service_name'] == 'dhcp' and \
            service['need_regen']:
            regen_dhcp(api_client)
            api_client.patch(service['api_url'], data={'need_regen': False})

