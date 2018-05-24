from configparser import ConfigParser

from re2oapi import Re2oAPIClient

config = ConfigParser()
config.read('config.ini')

hostname = config.get('Re2o', 'hostname')
password = config.get('Re2o', 'password')
username = config.get('Re2o', 'username')

api_client = Re2oAPIClient(hostname, username, password)
extensions = api_client.list_extensions()

print(len(extensions))
