import asyncio
import json
import logging
import os
import requests
import websockets
import random
from bot_openai import OpenAI_Bot
from dotenv import load_dotenv

load_dotenv()

# Change to logging.DEBUG for more output
# logging.basicConfig(level=logging.INFO)

followers = None
global_twitch_queue = None
global_chat_mode = False

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN') # Generated from your authentication mechanism, make sure it is scoped properly
CHANNEL_ID = os.getenv('CHANNEL_ID')     # The channel ID of the channel you want to join
CLIENT_ID = os.getenv('CLIENT_ID')       # The same Client ID used to generate the access token

async def handle_twitch_msg(event):
    global global_twitch_queue

    to_send = await extract_message_to_send_chat(event)
    print(f"handle_twitch_msg {to_send=}")
    global_twitch_queue.put(json.dumps(to_send))

async def extract_message_to_send_chat(event):
    formatted_msg = None
    formatted_return = None

    msg_username = event.get('payload', {}).get('event', {}).get('chatter_user_login', {})
    msg_msg = event.get('payload', {}).get('event', {}).get('message', {}).get('text', {})
    msg_server = event.get('payload', {}).get('event', {}).get('broadcaster_user_login', {})
    formatted_msg = f"twitch:{msg_username}: {msg_msg}"

    formatted_return = {
                "msg_user": msg_username,
                "msg_server": msg_server,
                "msg_msg": msg_msg,
                "formatted_msg": formatted_msg
            }
    
    print(formatted_return)
    return formatted_return

async def handle_sub(event):
    global global_twitch_queue

    to_send = await extract_message_to_sub(event)
    print(f"handle_twitch_msg {to_send=}")
    global_twitch_queue.put(json.dumps(to_send))

async def extract_message_to_sub(event):
    formatted_msg = None
    formatted_return = None

    msg_username = event.get('payload', {}).get('event', {}).get('user_login', {})
    msg_msg = "Has just subscribbed because they are a WIDEGIGACHAD"
    msg_server = event.get('payload', {}).get('event', {}).get('broadcaster_user_login', {})
    formatted_msg = f"twitch:{msg_username}: {msg_msg}"

    formatted_return = {
                "msg_user": msg_username,
                "msg_server": msg_server,
                "msg_msg": msg_msg,
                "formatted_msg": formatted_msg
            }
    
    print(formatted_return)
    return formatted_return

async def handle_redemptions(event):
    global global_twitch_queue
    if event.get('payload', {}).get('event', {}).get('reward', {}).get('title', {}) == "Ask Dabi A Q":

        to_send = await extract_message_to_send_points(event)
        print(f"handle_redemptions {to_send=}")
        global_twitch_queue.put(json.dumps(to_send))

async def extract_message_to_send_points(event):
    formatted_msg = None
    formatted_return = None

    msg_username = event.get('payload', {}).get('event', {}).get('user_name', {})
    msg_msg = event.get('payload', {}).get('event', {}).get('user_input', {})
    msg_server = event.get('payload', {}).get('event', {}).get('broadcaster_user_login', {})
    formatted_msg = f"twitch:{msg_username}: {msg_msg}"

    formatted_return = {
                "msg_user": msg_username,
                "msg_server": msg_server,
                "msg_msg": msg_msg,
                "formatted_msg": formatted_msg
            }
    
    return formatted_return

async def on_message(ws, message):
    global followers
    global global_twitch_queue
    global global_chat_mode
    event = json.loads(message)
    if event['metadata']['message_type'] == 'session_welcome':
        session_id = event['payload']['session']['id']
        print(f'{session_id=}')
        subscribe_array = [
            {
            'type': 'channel.follow',
            'version': '2',
            'condition': {
                'broadcaster_user_id': CHANNEL_ID,
                'moderator_user_id': CHANNEL_ID
            },
            'transport': {
                'method': 'websocket',
                'session_id': f'{session_id}',
            }
            },{
                "type": "channel.channel_points_custom_reward_redemption.add",
                "version": "1",
                'condition': {
                    "broadcaster_user_id": CHANNEL_ID,
                    'user_id': CHANNEL_ID
                },
                'transport': {
                    'method': 'websocket',
                    'session_id': f'{session_id}',
                }
            },{
                "type": "channel.subscribe",
                "version": "1",
                'condition': {
                    "broadcaster_user_id": CHANNEL_ID,
                    'user_id': CHANNEL_ID
                },
                'transport': {
                    'method': 'websocket',
                    'session_id': f'{session_id}',
                }
            }
        ]
        if global_chat_mode == True:
            subscribe_array.append({
                'type': 'channel.chat.message',
                'version': '1',
                'condition': {
                    "broadcaster_user_id": CHANNEL_ID,
                    'user_id': CHANNEL_ID
                },
                'transport': {
                    'method': 'websocket',
                    'session_id': f'{session_id}',
                }
            })
        for subscribe in subscribe_array:
            print(subscribe)
            response = requests.post(
                'https://api.twitch.tv/helix/eventsub/subscriptions',
                headers={
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Client-Id': CLIENT_ID,
                    'Content-Type': 'application/json',
                    'Accept': 'application/vnd.twitchtv.v5+json',
                },
                data=json.dumps(subscribe)
            )
            print(f'{response.content=}')
    
    elif event.get('metadata', {}).get('message_type', {}) == 'session_keepalive':
        pass
    elif event.get('metadata', {}).get('message_type', {}) == 'notification' and event.get('metadata', {}).get('subscription_type', {}) == 'channel.follow':
        # print(f'[🔔] Event:\n{event}')
        if event.get('payload', {}).get('event', {}).get('user_login', {}) not in followers:
            followers.append(event.get('payload', {}).get('event', {}).get('user_login', {}))
            follow_to_send = {
                "msg_user": event.get('payload', {}).get('event', {}).get('user_login', {}),
                "msg_server": event.get('payload', {}).get('event', {}).get('broadcaster_user_login', {}),
                "msg_msg": "Has just followed!",
                "formatted_msg": f"twitch:{event.get('payload', {}).get('event', {}).get('user_login', {})}: Has just followed!"
            }
            global_twitch_queue.put(json.dumps(follow_to_send))
            print("========================follow_to_send===================")
            print(json.dumps(follow_to_send))
            print(event)
            print("========================follow_to_send===================")
    elif event.get('metadata', {}).get('message_type', {}) == 'notification' and event.get('metadata', {}).get('subscription_type', {}) == 'channel.channel_points_custom_reward_redemption.add':
        ############################################################
        # Right now, we are receiving ALL channel point redemptions.
        await handle_redemptions(event)
        ############################################################
    elif event.get('metadata', {}).get('message_type', {}) == 'notification' and event.get('metadata', {}).get('subscription_type', {}) == 'channel.chat.message' and event.get('payload', {}).get('event', {}).get('channel_points_custom_reward_id', {}) == None:
        # print("=========================Inside channel.chat.message=========================")
        # Add in an if statement to check what mode Dabi is in.
        # If Dabi is in "assist" or "chat" mode, where Dabi will respond to every or almost every chat message.
        await handle_twitch_msg(event)
        # print(event.get('payload', {}).get('event', {}).get('chatter_user_name', {}))
        # print(event.get('payload', {}).get('event', {}).get('message', {}).get('text', {}))
        # print(chanpoint_test_thing)
        # print("=========================Inside channel.chat.message=========================")
    elif event.get('metadata', {}).get('message_type', {}) == 'notification' and event.get('metadata', {}).get('subscription_type', {}) == 'channel.subscribe':
        print("==========================================================")
        print("Received subscription in the form of:")
        print(event)
        await handle_sub(event)
        print("==========================================================")
    else:
        print(event)

async def ws_conn():
    url = 'wss://eventsub.wss.twitch.tv/ws'
    async with websockets.connect(url) as ws:
        print('[ℹ️] Connected to WebSocket')
        try:
            while True:
                message = await ws.recv()
                await on_message(ws, message)
        except websockets.ConnectionClosed as e:
            print(f'[❗] WebSocket closed: {e}')
        finally:
            print('[ℹ️] Closing WebSocket connection...')

async def grab_followers():
    all_followers = []
    cursor = None

    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {ACCESS_TOKEN}',
    }
    
    url = f'https://api.twitch.tv/helix/channels/followers?broadcaster_id={CHANNEL_ID}'

    while True:
        params = {'after': cursor} if cursor else {}
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        # Collect user_login from the current page
        all_followers.extend([follower['user_login'] for follower in data['data']])

        cursor = data.get('pagination', {}).get('cursor', {})

        if not cursor:
            print(f"{data.get('total', {})=}")
            break

    return all_followers

async def main():
    global followers
    # run here once
    followers = await grab_followers()

    await asyncio.gather(ws_conn())
    asyncio.run(ws_conn())

def start_events(twitch_queue, chat_mode):
    global global_twitch_queue
    global global_chat_mode
    global_twitch_queue = twitch_queue
    global_chat_mode = chat_mode
    print("TwitchEvent process has started")
    asyncio.run(main())

async def test_main():
    import multiprocessing
    global global_twitch_queue
    global_twitch_queue = multiprocessing.Queue()
    # print("Running the test version")
    # asyncio.run(main())
    event = {"metadata": {"message_id": "tNd9S_fqeIIAQ-lYje6gCLkj_djvNYnbg6eewHva_LY=", "message_type": "notification", "message_timestamp": "2024-11-24T09:27:17.345Z", "subscription_type": "channel.subscribe", "subscription_version": "1"}, "payload": {"subscription": {"id": "3b72ed7d-3e1c-4780-91f7-9a50e2f279d3", "status": "enabled", "type": "channel.subscribe", "version": "1", "condition": {"broadcaster_user_id": "54654420"}, "transport": {"method": "websocket", "session_id": "AgoQg3GTuTNjTCqQFPZWFVeEqRIGY2VsbC1h"}, "created_at": "2024-11-24T09:25:43.241687839Z", "cost": 0}, "event": {"user_id": "921771386", "user_login": "hezreal_", "user_name": "hezreal_", "broadcaster_user_id": "54654420", "broadcaster_user_login": "pdgeorge", "broadcaster_user_name": "Pdgeorge", "tier": "1000", "is_gift": True}}}
    await handle_sub(event)
    print("About to get from queue")
    print(global_twitch_queue.get())

if __name__ == "__main__":
    try:
        asyncio.run(test_main())
    except KeyboardInterrupt:
        print('[❗] Application interrupted. Shutting down...')