import gc
import os
import shutil
import aiofiles as aiofiles
from starlette.responses import StreamingResponse
from starlette.background import BackgroundTasks
from fastapi import FastAPI, UploadFile, Form
from typing_extensions import Annotated
import config
import discord
from fastapi.staticfiles import StaticFiles
WEBHOOK = config.WEBHOOK
app = FastAPI()
CHUNK_SIZE = 1096 * 1096


@app.post("/api/upload")
async def upload_file(file: UploadFile, encrypted: Annotated[bool, Form()]):
    print(encrypted)
    temp_id = discord.id_generator(15)
    temp_dir = "tmp/" + temp_id
    temp_file_path = temp_dir + "/" + temp_id
    os.mkdir(temp_dir)
    async with aiofiles.open(temp_file_path, 'wb') as f:
        while chunk := await file.read(CHUNK_SIZE):
            await f.write(chunk)
    await file.close()
    discord.upload_file(temp_file_path, WEBHOOK, file.filename, encrypted, temp_id, temp_dir)
    shutil.rmtree(temp_dir)
    gc.collect()
    return True


@app.get("/api/links")
async def get_links(id: str):
    gc.collect()
    return discord.links_from_id(id, WEBHOOK)


@app.get("/api/download")
async def test_download(id: str, background_tasks: BackgroundTasks):
    thingId = discord.get_info_from_id(id)
    urlArray = discord.links_from_id(id, WEBHOOK)

    headers = {'Content-Disposition': 'attachment; filename="' + thingId["originalName"]}

    background_tasks.add_task(gc.collect)
    return StreamingResponse(discord.yield_from_links(urlArray, thingId["encrypted"]), media_type="application/octet-stream", headers=headers)


@app.get("/api/list")
async def list():
    arrayList = discord.get_all_files()
    gc.collect()
    return discord.parse_json(arrayList)
app.mount("/", StaticFiles(directory="static", html=True), name="static")
