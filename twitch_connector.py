from dotenv import load_dotenv
import asyncio
import random
import os
import websockets
import re
import json

class ChatBot:
    def __init__(self):
        load_dotenv()
        self.oauth = os.getenv("ACCESS_TOKEN")
        self.nick = os.getenv("BOT_NICK")
        self.channel = os.getenv("CHANNEL")
        self.messages = []
        pattern = r"@(.*?) :.*?.tmi.twitch.tv PRIVMSG #(.*?) :(.*)"
        self.regex_pattern = re.compile(pattern)
        
    async def convert_to_ping(self, twitch_msg):
        if twitch_msg["message"][0] == "!":
            # Only pdgeorge can mindwipe the Dab.
            if twitch_msg["message"].find("reset") and twitch_msg["user_id"].find("54654420"):
                self.reset_memory()
                twitch_msg["message"] = 'RESET'
        
        if twitch_msg["message"].find("🤖") > -1 or twitch_msg["user_id"].find("100135110") > -1 or twitch_msg["message"][0] == "," or twitch_msg["message"][0] == "@":
            twitch_msg["message"] = 'PING'
            print("Found a bot message!")
            
        return twitch_msg
    
    async def format_twitch_msg(self, twitch_msg):
        formatted_msg = None
        
        if twitch_msg["message"].find("PING") < 0:
            msg_username = twitch_msg["display_name"]
            msg_server = twitch_msg["channel"]
            msg_msg = twitch_msg["message"]
            formatted_msg = f"twitch:{msg_username}: {msg_msg}"
            
            formatted_return = {
                "msg_user": msg_username,
                "msg_server": msg_server,
                "msg_msg": msg_msg,
                "formatted_msg": formatted_msg
            }
            
            return formatted_return
    
    async def on_twitch_message(self, twitch_ws, message, twitch_queue):
            
        # Highest priority, PING/PONG should occur before anything else.
        if "PING" in message:
            print(message)
            await twitch_ws.send("PONG :tmi.twitch.tv")

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
                
            message_data = await self.convert_to_ping(message_data)
            message_data = await self.format_twitch_msg(message_data)
            print(f"{message_data=}")
            
            self.messages.append(message_data)
            
            await self.forward_message(twitch_queue)
            
            # websocket = websockets.connect("ws://localhost:8001")
         
    async def handle_twitch_messages(self, twitch_ws, twitch_queue):
        async for message in twitch_ws:
            await self.on_twitch_message(twitch_ws, message, twitch_queue)

    async def twitch_give_best(self):
        # Currently just returning a random message
        # We want to later choose the best one
        # TODO: If the best one can't be found then choose random
        num = None
        to_send = None
        try:
            if len(self.messages) == 0:
                return to_send
            else:
                num = random.randint(0, len(self.messages)-1)
                to_send = self.messages[num]
                self.messages.pop(num)
                if len(self.messages) > 3:
                    print("over 3?")
                    self.messages = []
                return to_send
        except Exception as exception:
            print(f"{exception}")
            print(f"{self.messages=}")
            print(f"{num=}")

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

    async def forward_message(self, twitch_queue):
        to_send = await self.twitch_give_best()
        if to_send:
            print(f"Queueing message: {to_send=}")
            twitch_queue.put(json.dumps(to_send))
        await asyncio.sleep(1)

    async def handler(self, twitch_queue):
        # Make connection to Twitch
        async with websockets.connect("wss://irc-ws.chat.twitch.tv:443") as twitch_ws:
            await self.on_open(twitch_ws)
            twitch_task = asyncio.create_task(self.handle_twitch_messages(twitch_ws, twitch_queue))
            
            await twitch_task
            
    def handler_handler(self, twitch_queue):
        asyncio.run(self.handler(twitch_queue))
            
if __name__ == "__main__":
    bot = ChatBot()
    asyncio.run(bot.handler())