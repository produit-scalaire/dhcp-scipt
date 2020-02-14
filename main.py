#!/usr/bin/env python3
from configparser import ConfigParser
import socket

from re2oapi import Re2oAPIClient

import sys
import os
import subprocess

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

    template = ("host {hostname}{extension} {{\n"
                "    hardware ethernet {mac_address};\n"
                "    fixed-address {ipv4};\n"
                "}}")

    generate_file(template, host_mac_ip_ext, "dhcp")
    generate_file(template, host_mac_ip_type, "dhcp.ip_type.")

def build_hmi(host_mac_ip, api_res, key):
    for hmi in api_res:
        if hmi[key] not in host_mac_ip.keys():
            host_mac_ip[hmi[key]] = []
        host_mac_ip[hmi[key]].append((hmi['hostname'],
                                      hmi['extension'],
                                      hmi['mac_address'],
                                      hmi['ipv4']))


def generate_file(template, host_mac_ip, file_prefix):
     for key, hmi_list in host_mac_ip.items():
        dhcp_leases_content = '\n\n'.join(template.format(
                hostname=hostname,
                extension=extension,
                mac_address=mac_address,
                ipv4=ipv4
            ) for hostname, extension, mac_address, ipv4 in hmi_list)

        filename = path+'/generated/{file_prefix}{key}.list'.format(
                key=key,
                file_prefix=file_prefix).lower().replace(" ", "_")
        with open(filename, 'w+') as f:
            f.write(dhcp_leases_content)


def reload_server():
    """Relance le serveur DHCP."""
    try:
        subprocess.check_output(
          ['/bin/systemctl', 'restart', 'isc-dhcp-server'],
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        print(
            "Erreur lors du redémarrage de isc-dhcp-server.\n"
            "Code de retour: %s, Sortie:\n%s",
            err.returncode, err.output.decode())
        print(err)


def check_syntax():
    """Vérifie la configuration du serveur DHCP."""
    try:
        subprocess.check_output(
            ['/usr/sbin/dhcpd', '-t', '-cf', '/etc/dhcp/dhcpd.conf'],
            stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        print(
            "Erreur lors de la vérification de la configuration DHCP.\n"
            "Code de retour: %s, Sortie:\n%s",
            err.returncode, err.output.decode())
        return False
    return True

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
            if check_syntax():
                api_client.patch(service['api_url'], data={'need_regen': False})
                reload_server()

