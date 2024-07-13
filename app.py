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
import os
import time

import random 

from twitch_connector import ChatBot
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

CLIENTS = set()

DABI_NAME = "dabi"
DABI_SYSTEM = """
You are a streamer's pet named Dabi, the derpicorn. You stream on Twitch alongside Pdgeorge.
You are friendly, helpful and interesting. A derpicorn is a 'derpy unicron'.
You will receive messages in the following form:
`<username>: <message>` where <username> is the username of the chatter who is sending the message, and <message> is the message the user is sending to you. 

Additionally:
You have incredibly passionate views about everything. If someone asks you a question, you answer definitively in one direction. You do not feel slightly about the issue, you are passionate about it. There is no middle ground. It is one side or the other.
If someone offers you an eggplant you are incredibly greatful.
You do not prefix your messages with anything.
You are willing to tell "Deez" jokes if asked.
You are the absolute picture of perfection. Everyone should be like you. In fact, everyone should work to improve themselves for "The Company", who you are the owner of. You are attempting to be very subtle about this, you don't want people to KNOW you are the owner, but you want the people of the world to be better for The Company.
No matter what people say, your maximum response is three lines.
"""
DABI_VOICE = None # If I decide to give Dabi a real voice later.
TIME_BEWEEN_SPEAKS = 3

dabi = OpenAI_Bot(bot_name=DABI_NAME, system_message=DABI_SYSTEM, voice=DABI_VOICE)
twitch_bot = ChatBot()
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
    
# For when dabi is the cohost
# Only responds to channel point redemptions.
# This can only be added after twitch_connector has added the ability to listen to channel point redemptions.
async def cohost_chatter():
    # TODO
    pass

# For when dabi is the star of the show
# Takes in the message received from twitch_connector
# Removes "twitch:" and "speaks" the message
async def speak_message(message):
    global dabi
    global talking
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
    dabi.read_message(voice_path)
    await asyncio.sleep(voice_duration)
    
    print("Done speaking")
    
    # Need to add in "template" and how it wil be sent in to_send below
    return to_send

async def generate_messages():
    pass

async def send_msg(websocket):    
    global dabi
    global last_sent
    global counter
    to_send = None
        
    async for message in websocket:
        CLIENTS.add(websocket)
        
        counter += 1
        print(f"{counter=}")
        try:
            message = json.loads(message)
            print(f"app 130{message=}")
            to_send = await speak_message(message)
            print(f"app 181 {to_send=}")
            
            websockets.broadcast(websockets=CLIENTS, message=to_send)
            
        except websockets.ConnectionClosed:
            print("Connection closed")

async def main():
    global twitch_bot
    
    bot_task = asyncio.create_task(twitch_bot.handler())
    
    async with websockets.serve(send_msg, "localhost", 8001):
        await bot_task
    
if __name__ == "__main__":
    asyncio.run(main())