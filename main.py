import time
t1 = time.time()

from configparser import ConfigParser

from re2oapi import Re2oAPIClient

config = ConfigParser()
config.read('config.ini')

hostname = config.get('Re2o', 'hostname')
password = config.get('Re2o', 'password')
username = config.get('Re2o', 'username')


host_mac_ip = {}
api_client = Re2oAPIClient(hostname, username, password)

for hmi in api_client.list_hostmacip(params={'page_size': 'all'}):
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

print(time.time() - t1)
