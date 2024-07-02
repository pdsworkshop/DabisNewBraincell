from dotenv import load_dotenv
import asyncio
import random
import os
import websockets
import re

class ChatBot:
    def __init__(self):
        load_dotenv()
        self.oauth = os.getenv("ACCESS_TOKEN")
        self.nick = os.getenv("BOT_NICK")
        self.channel = os.getenv("CHANNEL")
        self.messages = []
        pattern = r"@(.*?) :.*?.tmi.twitch.tv PRIVMSG #(.*?) :(.*)"
        self.regex_pattern = re.compile(pattern)
        
    async def on_twitch_message(self, ws, message):
        print("message is: " + message)

        if "PRIVMSG" in message:
            message_data = {}
            match = self.regex_pattern.search(message)
            groups = match.groups()
            key_value_pairs = groups[0].split(";")
            for pair in key_value_pairs:
                key, value = pair.split("=", 1)
                message_data[key.replace("-", "_")] = value
            message_data["channel"] = groups[1]
            message_data["message"] = groups[2].rstrip("\r\n")
                
            print(message_data)
            self.messages.append(message_data)
            
        if "PING" in message:
            await ws.send("PONG")

    async def handle_twitch_messages(self, ws):
        async for message in ws:
            await self.on_twitch_message(ws, message)

    async def twitch_give_best(self):
        # Currently just returning a random message
        # We want to later choose the best one
        # TODO: If the best one can't be found then choose random
        to_send = None
        if len(self.messages) == 0:
            return to_send
        else:
            num = random.randint(0, len(self.messages))
            print(self.messages)
            to_send = self.messages[num]
            print(f"{num} was chosen out of {len(self.messages)}")
            self.messages = []
            return to_send

    async def on_error(self, ws, error):
        print(error)
        
    async def on_close(self, ws, close_status_code, close_msg):
        print("### closed connection ###")
        
    async def on_open(self, ws):
        print("### opened connection ###")
        await ws.send("CAP REQ :twitch.tv/membership twitch.tv/tags twitch.tv/commands")
        await ws.send("PASS oauth:" + self.oauth)
        await ws.send("NICK " + self.nick)
        await ws.send("JOIN #" + self.channel)
        print("### connected to Twitch IRC API ###")

    async def handler(self):
        async with websockets.connect("wss://irc-ws.chat.twitch.tv:443") as ws:
            await self.on_open(ws)
            await self.handle_twitch_messages(ws)
    
if __name__ == "__main__":
    bot = ChatBot()
    asyncio.run(bot.handler())