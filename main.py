from dotenv import load_dotenv
import asyncio
import multiprocessing
import time
import twitch_connector
import twitch_event
import follow_websocketsender
import discord_bot
import app 

import random

# Historical test/example
def print_test(queue):
    while True:
        if queue.qsize() > 0:
            message = queue.get()
            print(f"main.py print_twitch: {message=}")
        else:
            time.sleep(1)

async def main():
    try:
        ### QUEUES ###
        twitch_queue = multiprocessing.Queue()
        # discord_queue = multiprocessing.Queue()

        ### INGESTORS ###
        # twitch_bot_process = multiprocessing.Process(target=twitch_connector.start_bot, args=("assist", twitch_queue,))
        # twitch_bot_process.start()
        
        event_process = multiprocessing.Process(target=twitch_event.start_events, args=(twitch_queue,))
        event_process.start()

        discord_process = multiprocessing.Process(target=discord_bot.start_bot, args=(twitch_queue,))
        discord_process.start()
        
        ### MAIN APP ###
        app_process = multiprocessing.Process(target=app.pre_main, args=(twitch_queue,))
        app_process.start()
        app_process.join()

        # follow_sender = multiprocessing.Process(target=follow_websocketsender.pre_main, args=(follow_queue,))
        # follow_sender.start()
    except KeyboardInterrupt as kb_interrupt:
        print(f"[!] Keyboard interrupt.\n{kb_interrupt}")
        event_process.join()
        event_process.terminate()
        event_process.close()
        
        # discord_process.join()
        # discord_process.terminate()
        # discord_process.close()
        
        app_process.join()
        app_process.terminate()
        app_process.close()
    
if __name__ == "__main__":
    asyncio.run(main())
