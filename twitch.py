import os
import asyncio
import aiohttp
# from dotenv import load_dotenv

# load_dotenv()


#CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")

# print('clientid', CLIENT_ID)

EVENTSUB_URL = "wss://eventsub.wss.twitch.tv/ws"
API_URL = "https://api.twitch.tv/helix"

BROADCASTERS = [
    {'username': 'AmericanApe', 'userId': None},
    {'username': 'Nation_LIVE', 'userId': None},
    {'username': 'ywalkr', 'userId': None},
    {'username': 'Tank_vJR', 'userId': None},
    {'username': 'Yardmeat', 'userId': None},
    {'username': 'tonistorms', 'userId': None},
    {'username': 'robot_ape', 'userId': None}
]


# async def get_access_token(session):
#     """Get an app access token using Twitch client credentials."""
#     async with session.post(
#         "https://id.twitch.tv/oauth2/token",
#         data={
#             "client_id": CLIENT_ID,
#             "client_secret": CLIENT_SECRET,
#             "grant_type": "client_credentials",
#         },
#     ) as response:
#         response.raise_for_status()
#         data = await response.json()
#         return data["access_token"]


async def get_broadcaster_id(session, token, channel):
    """Resolve the Twitch username to its broadcaster ID."""
    CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
    headers = {
        "Client-Id": CLIENT_ID,
        "Authorization": f"Bearer {token}",
    }

    async with session.get(
        f"{API_URL}/users",
        params={"login": channel},
        headers=headers,
    ) as response:
        response.raise_for_status()
        data = await response.json()

        if not data["data"]:
            raise ValueError(f"Twitch channel not found: {channel}")

        return data["data"][0]["id"]


async def subscribe_to_stream(session, token, broadcaster_id, session_id):
    """Subscribe to stream.online for this broadcaster."""
    CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
    headers = {
        "Client-Id": CLIENT_ID,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    body = {
        "type": "stream.online",
        "version": "1",
        "condition": {
            "broadcaster_user_id": broadcaster_id
        },
        "transport": {
            "method": "websocket",
            "session_id": session_id,
        },
    }

    async with session.post(
        f"{API_URL}/eventsub/subscriptions",
        headers=headers,
        json=body,
    ) as response:
        response.raise_for_status()
        print(f"Subscribed to Twitch stream.online for {broadcaster_id}")


async def twitch_listener(on_stream_online):
    """
    Connect to Twitch EventSub.

    Calls on_stream_online(name, login) when the channel goes live.
    """
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                token = os.getenv('TWITCH_TOKEN')
                broadcaster_ids = [] 
                for b in BROADCASTERS:
                    id = await get_broadcaster_id(session, token, b['username'])
                    broadcaster_ids.append(id)
                
                async with session.ws_connect(EVENTSUB_URL) as ws:
                    print("Connected to Twitch EventSub")

                    keepalive_timeout = 10

                    async for message in ws:
                        if message.type != aiohttp.WSMsgType.TEXT:
                            break

                        data = message.json()
                        metadata = data["metadata"]
                        message_type = metadata["message_type"]

                        if message_type == "session_welcome":
                            session_data = data["payload"]["session"]
                            session_id = session_data["id"]
                            keepalive_timeout = (
                                session_data["keepalive_timeout_seconds"]
                            )

                            for broadcaster_id in broadcaster_ids:
                                await subscribe_to_stream(
                                    session,
                                    token,
                                    broadcaster_id,
                                    session_id,
                                )

                        elif message_type == "notification":
                            subscription_type = (
                                data["payload"]["subscription"]["type"]
                            )

                            if subscription_type == "stream.online":
                                event = data["payload"]["event"]

                                name = event["broadcaster_user_name"]
                                login = event["broadcaster_user_login"]

                                print(f"{name} is now live!")

                                await on_stream_online(name, login)

                        elif message_type == "session_reconnect":
                            # The current connection is being replaced.
                            # Break out and establish a fresh session.
                            print("Twitch requested a reconnect")
                            break

                        elif message_type == "session_keepalive":
                            pass

                        elif message_type == "revocation":
                            print("Twitch subscription revoked:", data)

        except Exception as e:
            print(f"Twitch listener error: {e}")

        print("Reconnecting to Twitch in 5 seconds...")
        await asyncio.sleep(5)