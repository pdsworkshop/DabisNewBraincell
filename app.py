#!/usr/bin/env python

import asyncio
import json
import websockets
import sqlite3
import os

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
# Listening to Twitch Chat, every message, and responding to it.
# For now: Listen to every message. Later: When there is a LOT of messages, collect 3-5 at a time and only respond to randomly 1 of them.
async def chat_chatter():
    global twitch_bot
    twitch_msg = await twitch_bot.twitch_give_best() # Will return 'best' message.
    formatted_msg = None
    response = None
    global dabi
    
    if twitch_msg == None:
        return
    
    print(twitch_msg)
    
    if twitch_msg["message"][0] == "!":
        # Only pdgeorge can mindwipe the Dab.
        if twitch_msg["message"].find("reset") and twitch_msg["user_id"].find("54654420"):
            print(dabi.chat_history)
            dabi.reset_memory()
            print(dabi.chat_history)
            twitch_msg["message"] = 'PING'
    
    if twitch_msg["message"].find("🤖") > -1 or twitch_msg["user_id"].find("100135110") > -1 or twitch_msg["message"][0] == "," or twitch_msg["message"][0] == "@":
        twitch_msg["message"] = 'PING'
        print("Found a bot message!")
    
    # All done!
    if twitch_msg["message"].find('PING') < 0:
        msg_username = twitch_msg["display_name"]
        msg_server = twitch_msg["channel"]
        msg_msg = twitch_msg["message"]
        formatted_msg = f"{msg_username}: {msg_msg}"

    if formatted_msg != None:
        response = await dabi.send_msg(formatted_msg)
        # response = f"Dabi responded to: {formatted_msg}"
        print(response)
        await db_insert(table_name=msg_server, username=msg_username, message=msg_msg, response=response)
        
    # await websocket.send(json.dumps(OPEN_MOUTH))
    # x = await websocket.recv()
    # print(f"{x=}")
    return response
    # return response

async def generate_messages():
    pass
        
async def send_msg(websocket):
    try:
        global dabi
        global last_sent
        global counter
        counter += 1
        print(f"{counter=}")
        
        response = await chat_chatter()
        if response == None:
            if last_sent == CLOSE_MOUTH:
                return
            last_sent = CLOSE_MOUTH
            # await asyncio.sleep(0.1)
            await websocket.send(json.dumps(CLOSE_MOUTH))
            # x = await websocket.recv()
            return
        to_send = OPEN_MOUTH
        to_send["message"] = response
        
        last_sent = to_send
        
        print(f"{to_send=}")
        # await asyncio.sleep(0.1)
        await websocket.send(json.dumps(to_send))
        # x = await websocket.recv()
        # await asyncio.sleep(0.1)
        
        # Audio making
        voice_path, voice_duration = dabi.create_se_voice(dabi.se_voice, response)
        dabi.read_message(voice_path)
        await asyncio.sleep(voice_duration)
        # await asyncio.sleep(0.1)
        
        if os.path.exists(voice_path):
            os.remove(voice_path)
            # await asyncio.sleep(0.1)
        else:
            print(f"Something went wrong with {voice_path}")
            
        to_send = CLOSE_MOUTH
        last_sent = to_send
        print("============================================================================")
        print(f"{to_send=}")
        print("============================================================================")
        await websocket.send(json.dumps(to_send))
        # x = await websocket.recv()
        await asyncio.sleep(TIME_BEWEEN_SPEAKS)
        
    except websockets.ConnectionClosed:
        print("Connection closed")

async def main():
    global twitch_bot
    
    bot_task = asyncio.create_task(twitch_bot.handler())
    
    async with websockets.serve(send_msg, "", 8001):
        await bot_task
    
    # await asyncio.gather(bot_task, websocket_task)

if __name__ == "__main__":
    asyncio.run(main())