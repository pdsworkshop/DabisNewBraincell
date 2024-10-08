import asyncio
import json
import logging
import os
import requests
import websockets
import random
from bot_openai import OpenAI_Bot
from typing import List, Optional
from runware import Runware, IImageInference, IImage, IError, RunwareAPIError, IPromptEnhance, IEnhancedPrompt
from dotenv import load_dotenv

load_dotenv()

# Change to logging.DEBUG for more output
# logging.basicConfig(level=logging.INFO)

followers = None
not_dabi = None
global_twitch_queue = None

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN') # Generated from your authentication mechanism, make sure it is scoped properly
CHANNEL_ID = os.getenv('CHANNEL_ID')     # The channel ID of the channel you want to join
CLIENT_ID = os.getenv('CLIENT_ID')       # The same Client ID used to generate the access token
RUNWARE_API = os.getenv('RUNWARE_API')
ART_STYLES = [
    "Pixel Art",
    "Anime",
    "3D Rendering",
    "Abstract",
    "Impressionism",
    "Surrealism",
    "Realism",
    "Pop Art",
    "Cartoon",
    "Minimalism",
    "Watercolor",
    "Cyberpunk",
    "Steampunk",
    "Fantasy Art",
    "Comic Book",
    "Cubism",
    "Concept Art",
    "Baroque",
    "Gothic",
    "Graffiti"
]

def on_partial_images(images: List[IImage], error: Optional[IError]) -> None:
    if error:
        print(f"API Error: {error}")
    else:
        print(f"Received {len(images)} partial images")
        for image in images:
            print(f"Partial Image URL: {image.imageURL}")

async def safe_request_images(runware: Runware, request_image: IImageInference):
    try:
        return await runware.imageInference(requestImage=request_image)
    except RunwareAPIError as e:
        print(f"API Error: {e}")
        print(f"Error Code: {e.code}")
        return None
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None

async def reward_new_follow(follower_name):
    global not_dabi
    runware = Runware(api_key=RUNWARE_API)
    await runware.connect()

    art_style = random.choice(ART_STYLES)
    positive_prompt = f"A <<{art_style}>>, plush toy, white unicorn, <<{follower_name} is their name>>, <<{follower_name} themed character>>, <<corporate themed background>> office, city scape, cubical"
    negative_prompt = "cloudy, two horns, rainy, nsfw, five legs, three legs, chinese background"
    
    better_prompt = await not_dabi.send_msg(positive_prompt)
    not_dabi.reset_memory()
    print(f"{positive_prompt=}")
    print(f"{better_prompt=}")

    request_image = IImageInference(
        positivePrompt=better_prompt,
        model="runware:100@1",
        numberResults=1,
        negativePrompt=negative_prompt,
        useCache=False,
        onPartialImages=on_partial_images,
        height=512,
        width=512,
        outputFormat="PNG",
    )
    image_request_result = await safe_request_images(runware, request_image)
    print("============================================================")
    if image_request_result:
        print("first result")
        for image in image_request_result:
            return image.imageURL
    print("============================================================")

async def handle_redemptions(event):
    global global_twitch_queue
    if event.get('payload', {}).get('event', {}).get('reward', {}).get('title', {}) == "Ask Dabi A Q":
        # print("Ask a Q")
        # print(event)
        # print(event.get('payload', {}).get('event', {}).get('user_name', {}))
        # print(event.get('payload', {}).get('event', {}).get('user_input', {}))
        to_send = await extract_message_to_send_points(event)
        print(f"{to_send=}")
        global_twitch_queue.put(json.dumps(to_send))
        print("=====================================")
        print(f"{global_twitch_queue.qsize()=}")
        # for i in range(global_twitch_queue.qsize()):
        #     print(i)
        #     print(global_twitch_queue)
        print("=====================================")

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
            }
        ]
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
            link_received = await reward_new_follow(event.get('payload', {}).get('event', {}).get('user_login', {}))
            followers.append(event.get('payload', {}).get('event', {}).get('user_login', {}))
            follow_to_send = {
                "name": event.get('payload', {}).get('event', {}).get('user_login', {}),
                "received_link": link_received
            }
            global_twitch_queue.put(json.dumps(follow_to_send))
    elif event.get('metadata', {}).get('message_type', {}) == 'notification' and event.get('metadata', {}).get('subscription_type', {}) == 'channel.channel_points_custom_reward_redemption.add':
        ############################################################
        # Right now, we are receiving ALL channel point redemptions.
        await handle_redemptions(event)
        ############################################################
    elif event.get('metadata', {}).get('message_type', {}) == 'notification' and event.get('metadata', {}).get('subscription_type', {}) == 'channel.chat.message' and event.get('payload', {}).get('event', {}).get('channel_points_custom_reward_id', {}) == None:
        # print("=========================Inside channel.chat.message=========================")
        # Add in an if statement to check what mode Dabi is in.
        # If Dabi is in "assist" or "chat" mode, where Dabi will respond to every or almost every chat message.
        # print(event)
        print(event.get('payload', {}).get('event', {}).get('chatter_user_name', {}))
        print(event.get('payload', {}).get('event', {}).get('message', {}).get('text', {}))
        # print(chanpoint_test_thing)
        # print("=========================Inside channel.chat.message=========================")

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
    global not_dabi
    not_dabi = OpenAI_Bot(bot_name="not_dabi", system_message="You are a helpful bot that helps people generate AI images using prompts. You will be given a positive prompt, you will return a better positive prompt. Anything between << >> is incredibly important and MUST NOT be changed. DO NOT include << or >> yourself. You will always add a unique style or flair to each prompt.", voice=None)
    # run here once
    followers = await grab_followers()

    await asyncio.gather(ws_conn())
    asyncio.run(ws_conn())

def start_events(twitch_queue):
    global global_twitch_queue
    global_twitch_queue = twitch_queue
    print("Followbot process has started")
    asyncio.run(main())

def test_main():
    import multiprocessing
    # global global_twitch_queue
    # global global_follow_queue
    # global_follow_queue = multiprocessing.Queue()
    # global_twitch_queue = multiprocessing.Queue()
    print("Running the test version")
    asyncio.run(main())

if __name__ == "__main__":
    try:
        test_main()
    except KeyboardInterrupt:
        print('[❗] Application interrupted. Shutting down...')