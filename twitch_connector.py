from dotenv import load_dotenv # python-dotenv
import os
import time
import socket
from emoji import demojize

load_dotenv()

SERVER = "irc.chat.twitch.tv"
PORT = 6667
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
NICKNAME = os.getenv("BOT_NICK")
# CHANNEL = os.getenv("CHANNEL")
CHANNEL = "megaa"

class Bot():
    
    def __init__(self):
        self.sock = socket.socket()
        self.sock.connect((SERVER, PORT))
        self.join()
        
    def join(self):
        self.sock.send(f"PASS oauth:{ACCESS_TOKEN}\n".encode('utf-8'))
        self.sock.send(f"NICK {NICKNAME}\n".encode('utf-8'))
        self.sock.send(f"JOIN #{CHANNEL}\n".encode('utf-8'))

    def listen_for_msg(self):
        resp = self.sock.recv(2048).decode('utf-8')
        if resp.startswith('PING'):
            self.sock.send("PONG\n".encode('utf-8'))
            return
        elif len(resp) > 0:
            resp = demojize(resp)
            return resp

def main():
    bot = Bot()
    print("started?")
    while True:
        resp = bot.listen_for_msg()
        print(resp)

if __name__ == "__main__":
    main()