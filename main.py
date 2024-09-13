from dotenv import load_dotenv
import asyncio
import multiprocessing
import time
import twitch_connector
import twitch_event_follow
import follow_websocketsender
import app 

import random

# Historical test/example
def print_twitch_test(twitch_queue):
    while True:
        if twitch_queue.qsize() > 0:
            message = twitch_queue.get()
            print(f"main.py print_twitch: {message=}")
        else:
            time.sleep(1)

async def main():
    try:
        twitch_queue = multiprocessing.Queue()
        follow_queue = multiprocessing.Queue()
        
        twitch_bot_process = multiprocessing.Process(target=twitch_connector.start_bot, args=("assist", twitch_queue,))
        twitch_bot_process.start()

        follow_bot_process = multiprocessing.Process(target=twitch_event_follow.start_events, args=(twitch_queue, follow_queue,))
        follow_bot_process.start()

        app_process = multiprocessing.Process(target=app.pre_main, args=(twitch_queue,))
        app_process.start()
        app_process.join()

        # follow_sender = multiprocessing.Process(target=follow_websocketsender.pre_main, args=(follow_queue,))
        # follow_sender.start()
    except KeyboardInterrupt as kb_interrupt:
        print(f"[!] Keyboard interrupt.\n{kb_interrupt}")
        twitch_bot_process.join()
        twitch_bot_process.terminate()
        twitch_bot_process.close()
        
        # app_process.join()
        app_process.terminate()
        app_process.close()
    
if __name__ == "__main__":
    asyncio.run(main())