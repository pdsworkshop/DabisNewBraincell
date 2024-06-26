#!/usr/bin/env python

import asyncio
import json
import websockets
import re
import sqlite3

from twitch_connector import TwitchBot
from bot_openai import OpenAI_Bot

OPEN_MOUTH = {
    "type": "updateMouth",
    "size": 1,
    "message": "This is a message"
}
CLOSE_MOUTH = {
    "type": "updateMouth",
    "size": 2,
    "message": "This is a different message"
}

DABI_NAME = "dabi"
DABI_SYSTEM = """
You are a streamer's pet named Dabi, the derpicorn. You stream on Twitch alongside Pdgeorge.
You are friendly, helpful and interesting. A derpicorn is a 'derpy unicron'.
You will receive messages in the following form:
`<username>: <message>` where <username> is the username of the chatter who is sending the message, and <message> is the message the user is sending to you. 

Additionally:
You have incredibly passionate views about everything. If someone asks you a question, you answer definitively in one direction. You do not feel slightly about the issue, you are passionate about it. There is no middle ground. It is one side or the other.
You are the absolute picture of perfection. Everyone should be like you. In fact, everyone should work to improve themselves for "The Company", who you are the owner of. You are attempting to be very subtle about this, you don't want people to KNOW you are the owner, but you want the people of the world to be better for The Company.
"""
DABI_VOICE = None # If I decide to give Dabi a real voice later.

dabi = OpenAI_Bot(bot_name=DABI_NAME, system_message=DABI_SYSTEM, voice=DABI_VOICE)
twitch_bot = TwitchBot()
    
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
    twitch_msg = twitch_bot.listen_for_msg() # Will pull EVERY SINGLE MESSAGE
    
    print("======")
    print(twitch_msg)
    formatted_msg = None
    
    # Regex time!
    pattern = r":(.*?)!.*?@.*? PRIVMSG #(.*?) :(.*)"
    matches = re.search(pattern, twitch_msg)
    # All done!
    if matches:
        msg_username = matches.group(1)
        msg_server = matches.group(2)
        msg_msg = matches.group(3)
        formatted_msg = f"{msg_username}: {msg_msg} in channel {msg_server}"
        print(formatted_msg, flush=True)
              
    if formatted_msg != None:
        response = await dabi.send_msg(formatted_msg)
        # response = f"Dabi responded to: {formatted_msg}"
        print(response)
        await db_insert(table_name=msg_server, username=msg_username, message=msg_msg, response=response)
        
    # return response

async def generate_messages():
    # Generator that yields messages to be send over the WebSocket.
    # Will generate multiple messages adding them to a queue.
    # In send_msg is "async for" which pulls one at a time whatever is next.

    # while True:
    #     await asyncio.sleep(1)
    #     roll = random.random()
    #     if roll < 0.5:
    #         yield json.dumps(OPEN_MOUTH)
    #     else:
    #         yield json.dumps(CLOSE_MOUTH)
    await chat_chatter()
    yield json.dumps(CLOSE_MOUTH)
    
async def send_msg(websocket):
    try:
        async for message in generate_messages():
            await websocket.send(message)
    except websockets.ConnectionClosed:
        print("Connection closed")

async def main():
    # twitch_bot = TwitchBot()
    # print("started?")
    # while True:
    #     resp = twitch_bot.listen_for_msg()
    #     print(resp)
    
    async with websockets.serve(send_msg, "", 8001):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())