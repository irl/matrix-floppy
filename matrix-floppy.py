import asyncio
from collections import defaultdict
from typing import Optional

from nio import AsyncClient
from nio import AsyncClientConfig
from nio import Event
from nio import MessageDirection
from nio import MatrixRoom
from nio import RoomMessageText
from nio import RoomMessagesError
from nio import SyncResponse
from nio.store import SqliteMemoryStore

events = defaultdict(list)


def event_cb(room: MatrixRoom, event: Event):
    if isinstance(event, RoomMessageText):
        events[room.room_id].append(event)


async def init(homeserver: str, username: str, password: str,
               keyfile: Optional[str],
               keyphrase: Optional[str]) -> AsyncClient:
    config = AsyncClientConfig(store=SqliteMemoryStore, store_sync_tokens=True)
    client = AsyncClient(homeserver, username, config=config)
    response = await client.login(password)
    client.add_event_callback(event_cb, RoomMessageText)
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
            time.sleep(5)
            pass
        except IOError:
            time.sleep(5)
            pass


async def main():
    client = await init("https://matrix.org", "irl_", "HSPASSWORD",
                        "/path/to/element-keys.txt", "KEYPASSWORD")
    sync_filter = {"room": {"timeline": {"limit": 1}}}
    sync_response = await client.sync(30000,
                                      sync_filter=sync_filter,
                                      full_state=True)
    for room_id in sync_response.rooms.join.keys():
        print(f"Fetching events for {room_id}...")
        await handle_room(
            client, client.rooms[room_id],
            sync_response.rooms.join[room_id].timeline.prev_batch)
    for room in events:
        with open(f"saves/{room}.html", "w") as out:
            out.write(f"<h1>{room}</h1>")
            for ev in sorted(events[room], key=lambda x: x.server_timestamp):
                if isinstance(ev, RoomMessageText):
                    out.write(f"<p>{ev.sender}: {ev.body}</p>")
    await client.close()


asyncio.run(main())
