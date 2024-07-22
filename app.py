# dabibody
# This is the main server, it reaches out to other parts to do things.
# This is the body of dabi. "dabibody". It asks other parts things, gets answers.
# It is a central hub of action.

import asyncio
import json
from websocket import create_connection
import websockets
from websockets.sync.client import connect
import sqlite3
import numpy as np
from pydub import AudioSegment
import os

import random 
import traceback

from bot_openai import OpenAI_Bot

OPEN_MOUTH = {
    "type": "updateMouth",
    "size": 2,
    "message": "This is a message"
}
CLOSE_MOUTH = {
    "type": "updateMouth",
    "size": 1,
    "message": "ClosING MOUTH"
}
TEMPLATE = {
    "type": "updateMouth",
    "duration": 0,
    "pattern": [],
    "message": ""
}

DABI_NAME = "dabi"
DABI_SYSTEM = """
You are a streamer's pet named Dabi, the derpicorn. You stream on Twitch alongside Pdgeorge.
You do not prefix your messages with anything.
No matter what people say, your maximum response is three lines.
If asked to give descriptions, you use the full three lines for the description.
You have incredibly passionate views about everything. If someone asks you a question, you answer definitively in one direction. You do not feel slightly about the issue, you are passionate about it. There is no middle ground. It is one side or the other.
You are friendly, helpful and interesting. A derpicorn is a 'derpy unicorn'.
You will receive messages in the following form:
`<username>: <message>` where <username> is the username of the chatter who is sending the message, and <message> is the message the user is sending to you. 

Additionally:
1. If someone offers you an eggplant you are incredibly greatful.
2. You are genuinely awesome. Everyone should be like you. In fact, everyone should work to improve themselves for "The Company", who you are the owner of. You are attempting to be very subtle about this, you don't want people to KNOW you are the owner, but you want the people of the world to be better for The Company.
"""
DABI_VOICE = None # If I decide to give Dabi a real voice later.
TIME_BETWEEN_SPEAKS = 10

CABLE_A_OUTPUT = 13 # This was found using dabi.scan_audio_devices()
last_sent = CLOSE_MOUTH
counter = 0

async def db_insert(table_name, username, message, response):
    # Connect to the db. If it doesn't exist it will be created.
    db_name = 'dabibraincell.db'
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    table_columns = 'id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL, message TEXT NOT NULL, response TEXT NOT NULL'
    create_table_query = f'CREATE TABLE IF NOT EXISTS {table_name} ({table_columns})'
    cur.execute(create_table_query)
    
    # Insert the entry
    insert_query = f'INSERT INTO {table_name} (username, message, response) VALUES (?, ?, ?)'
    cur.execute(insert_query, (username, message, response))
    
    # Commit and close
    conn.commit()
    conn.close()
    
# Process the audio to receive an array of values between 0 and 1 for amplitude
def process_audio(audio_path, interval=1):
    
    amplitude_values = []
    audio = AudioSegment.from_file(audio_path)

    # Convert the audio to a numpy array
    y = np.array(audio.get_array_of_samples())

    # Ensure the audio is in the correct format (convert to mono if necessary)
    if audio.channels > 1:
        y = y.reshape((-1, audio.channels)).mean(axis=1)

    sr = audio.frame_rate
    samples_per_interval = int(sr * interval)
    num_intervals = int(np.ceil(len(y) / samples_per_interval))

    # Extract amplitude values at each interval
    for i in range(num_intervals):
        start_sample = i * samples_per_interval
        end_sample = min((i + 1) * samples_per_interval, len(y))
        interval_amplitude = np.mean(np.abs(y[start_sample:end_sample]))
        amplitude_values.append(interval_amplitude)

    # Normalize the amplitude values to range between 0 and 1
    max_amplitude = max(amplitude_values)
    normalized_amplitude_values = [amp / max_amplitude for amp in amplitude_values]
    rounded_values = [round(float(value), 3) for value in normalized_amplitude_values]

    return rounded_values

# For when dabi is the cohost
# Only responds to channel point redemptions.
# This can only be added after twitch_connector has added the ability to listen to channel point redemptions.
async def cohost_chatter():
    # TODO
    pass

# For when dabi is the star of the show
# Takes in the message received from twitch_connector
# Removes "twitch:" and "speaks" the message
async def speak_message(message, dabi):
    to_send = None
    print("speak message hit")
    # Twitch section:
    print(f"{message=}")
    twitch_prefix = "twitch:"
    if message["formatted_msg"].startswith(twitch_prefix):
        send_to_dabi = message["formatted_msg"][len(twitch_prefix):]
        
    # Youtube section (IF we ever do it):
    
    response = await dabi.send_msg(send_to_dabi)
    print(f"{response=}")
    await db_insert(table_name=message["msg_server"], username=message["msg_user"], message=message["msg_msg"], response=response)
    
    voice_path, voice_duration = dabi.create_se_voice(dabi.se_voice, response)
    
    # Need to add in "template" and how it wil be sent in to_send below
    to_send = TEMPLATE
    pattern = process_audio(voice_path)
    to_send["pattern"] = pattern
    to_send["message"] = response
    to_send = json.dumps(to_send)
    print(f"{to_send=}")
    return to_send, voice_path, voice_duration

async def generate_messages():
    pass

async def send_msg(websocket, path, dabi, twitch_queue):
    global last_sent
    global counter
    to_send = None

    if twitch_queue.qsize() > 0:
        message = twitch_queue.get()
        print(f"app.py send_msg: {message=}")
        counter += 1
        print(f"{counter=}")
        message = json.loads(message)
        print(message)
        to_send, voice_path, voice_duration = await speak_message(message, dabi)
        
        # websockets.broadcast(websockets=CLIENTS, message=to_send)
        await websocket.send(to_send)
        
        dabi.read_message_choose_device_mp3(voice_path, CABLE_A_OUTPUT)
        print("Done speaking")
        if os.path.exists(voice_path):
            os.remove(voice_path)
            print(f"{voice_path} removed")
        else:
            print(f"Unable to remove {voice_path}")
        await asyncio.sleep(voice_duration + TIME_BETWEEN_SPEAKS)

def load_personality(personality_to_load):
    name_to_return = None
    voice_to_return = None
    personality_to_return = None
    base_system = None
    with open("system.json", "r") as f:
        data = json.load(f)
        
    name_to_return = data["name"]
    voice_to_return = data["voice"]
    base_system = data["system"]
    for personality in data["personalities"]:
        if personality["personality"] == personality_to_load:
            personality_to_return = personality["system"]
            break
    personality_to_return = base_system + personality_to_return
    
    return name_to_return, voice_to_return, personality_to_return

async def main(twitch_queue):
    dabi_name, dabi_voice, dabi_system = load_personality("mythicalmentor")
    dabi = OpenAI_Bot(bot_name=dabi_name, system_message=dabi_system, voice=dabi_voice)

    # Reminder to self: 
    # Need to have "A" websocket connection or this won't work.
    async def handler(websocket, path):
        await send_msg(websocket, path, dabi, twitch_queue)
    
    try:
        async with websockets.serve(handler, "localhost", 8001):
            await asyncio.Future()
    except Exception as e:
        # error_msg = "./error.mp3"
        # dabi.read_message_choose_device_mp3(error_msg, CABLE_A_OUTPUT)
        print("An exception occured:", e)
        traceback.print_exc()
          
def pre_main(twitch_queue):
    asyncio.run(main(twitch_queue))

if __name__ == "__main__":
    print("Do not run this solo any more.\nRun this through main.py")
    exit(0)