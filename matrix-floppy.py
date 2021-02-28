import asyncio
from collections import defaultdict
from datetime import datetime
import os
import sys
import time
from typing import Optional
from urllib.parse import urlparse

from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import Markup
from jinja2 import select_autoescape
from nio import AsyncClient
from nio import AsyncClientConfig
from nio import DownloadError
from nio import Event
from nio import MessageDirection
from nio import MatrixRoom
from nio import RoomMessage
from nio import RoomMessageAudio
from nio import RoomMessageFormatted
from nio import RoomMessageImage
from nio import RoomMessageMedia
from nio import RoomMessageText
from nio import RoomMessageVideo
from nio import RoomMessagesError
from nio import SyncResponse
from nio.store import SqliteMemoryStore

media = []
events = defaultdict(list)


def progress(count, total, status=''):
    bar_len = 60
    filled_len = int(round(bar_len * count / float(total)))
    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)
    sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', status))
    sys.stdout.flush()


async def matrix_media_download(client: AsyncClient, url: str) -> None:
    with open(os.path.join("saves", matrix_media_path(url, True)), 'wb') as out:
        o = urlparse(url)
        media = await client.download(o.netloc, o.path[1:])
        if isinstance(media, DownloadError):
            raise RuntimeError(media)
        out.write(media.body)


def matrix_media_path(url: str, create: bool = False) -> str:
    o = urlparse(url)
    path = [o.netloc]
    path.extend(o.path.split('/'))
    path_str = os.path.join(*path)
    if create:
        try:
            path_dir = os.path.join("saves", *path[:-1])
            os.makedirs(path_dir)
        except FileExistsError as e:
            if not os.path.isdir(path_dir):
                raise
    return path_str


def matrix_timestamp(timestamp: int) -> str:
    dt = datetime.fromtimestamp(timestamp / 1000)
    return dt.isoformat()


def event_cb(room: MatrixRoom, event: Event):
    if isinstance(event, RoomMessageMedia):
        media.append(event.url)
    events[room.room_id].append(event)


async def init(homeserver: str, username: str, password: str,
               keyfile: Optional[str],
               keyphrase: Optional[str]) -> AsyncClient:
    config = AsyncClientConfig(store=SqliteMemoryStore, store_sync_tokens=True)
    client = AsyncClient(homeserver, username, config=config)
    response = await client.login(password)
    client.add_event_callback(event_cb, RoomMessage)
    await client.import_keys(keyfile, keyphrase)
    return client


async def handle_room(client: AsyncClient, room: MatrixRoom,
                      start_token: str) -> None:
    while True:
        try:
            resp = await client.room_messages(room.room_id,
                                              start_token,
                                              limit=100,
                                              direction=MessageDirection.back)
            if isinstance(resp, RoomMessagesError):
                print(resp)
                raise RuntimeError("Got an error fetching room messages")
            for ev in resp.chunk:
                event_cb(room, ev)
            if len(resp.chunk) == 0:
                # All caught up
                break
            start_token = resp.end
        except OSError:
            print("Caught an OSError, sleeping 5...")
            time.sleep(5)
            pass
        except IOError:
            print("Caught an IOError, sleeping 5...")
            time.sleep(5)
            pass


async def main():
    env = Environment(loader=FileSystemLoader('.'),
                      autoescape=select_autoescape(['html', 'xml']))
    env.filters['is_audio'] = lambda ev: isinstance(ev, RoomMessageAudio)
    env.filters['is_formatted'] = lambda ev: isinstance(ev, RoomMessageFormatted)
    env.filters['is_image'] = lambda ev: isinstance(ev, RoomMessageImage)
    env.filters['is_text'] = lambda ev: isinstance(ev, RoomMessageText)
    env.filters['is_video'] = lambda ev: isinstance(ev, RoomMessageVideo)
    env.filters['matrix_media_path'] = matrix_media_path
    env.filters['matrix_timestamp'] = matrix_timestamp
    client = await init("https://matrix.org", "irl_", "HSPASSWORD",
                        "/path/to/element-keys.txt", "KEYPASSWORD")
    sync_filter = {"room": {"timeline": {"limit": 1}}}
    sync_response = await client.sync(30000,
                                      sync_filter=sync_filter,
                                      full_state=True)
    for idx, room_id in enumerate(sync_response.rooms.join.keys()):
        progress(idx, len(sync_response.rooms.join.keys()), status=f'Fetching events for {room_id}')
        await handle_room(
            client, client.rooms[room_id],
            sync_response.rooms.join[room_id].timeline.prev_batch)
    for idx, url in enumerate(media):
        progress(idx, len(media), status='Downloading media')
        await matrix_media_download(client, url)
    for room_id in events:
        with open(os.path.join("saves", f"{room_id}.html"), "w") as out:
            tmpl = env.get_template("room.html.j2")
            out.write(
                tmpl.render(room_id=room_id,
                            events=sorted(events[room_id],
                                          key=lambda x: x.server_timestamp)))
    await client.close()


asyncio.run(main())
