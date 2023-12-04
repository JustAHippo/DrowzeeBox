import base64
import gc
import json
from bson import json_util
import requests
from discord_webhook import DiscordWebhook
import os
from time import sleep
from filesplit.split import Split
import string
import cryptography.fernet
import random
import redis
import pymongo
from natsort import natsorted
import config
KEY = config.KEY
mongo_client = pymongo.MongoClient(config.MONGO)
r = redis.Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True)


def parse_json(data):
    return json.loads(json_util.dumps(data))


database = mongo_client["discordfiles"]
fileCollection = database["files"]


def get_info_from_id(internalId: str):
    fileObject = fileCollection.find_one({"id": internalId})
    return fileObject


def upload_file(file_name: str, webhookStr: str, og_name: str, encrypted: bool = True, fileID: str = "", tempDir: str = ""):
    fernet = cryptography.fernet.Fernet(KEY)
    file_stats = os.stat(file_name)
    fileMB = file_stats.st_size / (1024 * 1024)
    split = Split(file_name, tempDir)
    split.bysize(26214399)
    os.remove(file_name)

    manifestFile = open(tempDir + "/manifest", "r")
    fileObject = {"originalName": og_name, "messageIds": [], "id": fileID, "manifest": manifestFile.read(), "size": fileMB, "encrypted": encrypted}
    manifestFile.close()
    sortedFilenames = []
    for filename in os.listdir(tempDir):
        sortedFilenames.append(filename)

    sortedFilenames = natsorted(sortedFilenames)
    for filename in sortedFilenames:
        f = os.path.join(tempDir, filename)
        # checking if it is a file
        if os.path.isfile(f):
            if "manifest" not in filename:
                with open(f, "rb", buffering=10485760) as file:
                    webhook = DiscordWebhook(url=webhookStr, username="DrowzeeBox")
                    if encrypted:
                        webhook.add_file(file=base64.urlsafe_b64decode(fernet.encrypt(file.read())), filename=filename)
                    else:
                        webhook.add_file(file=file.read(), filename=filename)
                    file.close()
                response = webhook.execute()
                responseJson = response.json()
                fileObject["messageIds"].append(responseJson["id"])
                os.unlink(f)
    fileCollection.insert_one(fileObject)
    gc.collect()


def link_from_message_id(webhookStr: str, messageId: str):
    getUrl = webhookStr + "/messages/" + messageId
    response = requests.get(getUrl)
    jsonResp = response.json()
    if "retry_after" in jsonResp:
        sleep(jsonResp["retry_after"] + 0.5)
        return link_from_message_id(webhookStr, messageId)
    fileLink = jsonResp["attachments"][0]["url"]
    return fileLink


def links_from_id(internalId: str, webhookStr: str):
    cachedLinks = r.get(internalId)
    if cachedLinks != None:
        print("Using cache!")
        return json.loads(cachedLinks)

    fileObject = fileCollection.find_one({"id": internalId})
    linkList = []
    for message_id in fileObject["messageIds"]:
        linkList.append(link_from_message_id(webhookStr, message_id))
    r.set(internalId, json.dumps(linkList), ex=72000)
    return linkList


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def get_all_files():
    allFiles = []
    for x in fileCollection.find({},{ "_id": 0, "originalName": 1, "id": 1, "size": 1}):
        allFiles.append(x)
    return allFiles


def remove_file(path: str) -> None:
    os.unlink(path)


def yield_from_links(linksArr, encrypted: bool = True):
    fernet = cryptography.fernet.Fernet(KEY)
    for link in linksArr:
        if encrypted:
            chunk = base64.urlsafe_b64encode(requests.get(link).content)
            yield fernet.decrypt(chunk)
        else:
            yield requests.get(link).content
