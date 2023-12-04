import json
configFile = open('config.json')
configData = json.load(configFile)

KEY = bytes(configData["key"], 'utf-8')
MONGO = configData["mongo"]
REDIS_HOST = configData["redis_host"]
REDIS_PORT = configData["redis_port"]
WEBHOOK = configData["webhook"]