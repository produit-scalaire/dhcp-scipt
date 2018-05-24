import time
t1 = time.time()

from configparser import ConfigParser

from re2oapi import Re2oAPIClient

config = ConfigParser()
config.read('config.ini')

hostname = config.get('Re2o', 'hostname')
password = config.get('Re2o', 'password')
username = config.get('Re2o', 'username')

api_client = Re2oAPIClient(hostname, username, password)
domains = api_client.list_domains()

extensions = api_client.list_extensions()

for extension in extensions:

    host_mac_ip = []
    for domain in domains:
        if domain['interface_parent'] is not None and \
                api_client.get(domain['extension'])['name'] == extension['name']:
            interface = api_client.get(domain['interface_parent'])
            if interface['active']:
                host_mac_ip.append((
                    domain['name'],
                    interface['mac_address'],
                    api_client.get(interface['ipv4'])['ipv4']
                ))
    
    template = ("host {hostname}{extension} {{\n"
                "    hardware ethernet {mac};\n"
                "    fixed-address {ipv4};\n"
                "}}")
    
    dhcp_leases_content = '\n\n'.join(template.format(
            hostname=hostname,
            extension=extension['name'],
            mac=mac,
            ipv4=ip
        ) for hostname, mac, ip in host_mac_ip)
    
    filename = 'dhcp-{extension}.list'.format(extension=extension['name'][1:])
    with open(filename, 'w+') as f:
        f.write(dhcp_leases_content)

print(time.time() - t1)
