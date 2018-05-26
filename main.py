from configparser import ConfigParser
import socket

from re2oapi import Re2oAPIClient

config = ConfigParser()
config.read('config.ini')

api_hostname = config.get('Re2o', 'hostname')
api_password = config.get('Re2o', 'password')
api_username = config.get('Re2o', 'username')

def regen_dhcp(api_client):
    for hmi in api_client.list_hostmacip():
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

        filename = 'dhcp{extension}.list'.format(extension=extension)
        with open(filename, 'w+') as f:
            f.write(dhcp_leases_content)

host_mac_ip = {}
api_client = Re2oAPIClient(api_hostname, api_username, api_password)

client_hostname = socket.gethostname().split('.', 1)[0]

for service in api_client.list_servicesregen():
    if service['hostname'] == client_hostname and \
            service['service_name'] == 'dhcp' and \
            service['need_regen']:
        regen_dhcp(api_client)
        api_client.patch(service['api_url'], data={'need_regen': False})
