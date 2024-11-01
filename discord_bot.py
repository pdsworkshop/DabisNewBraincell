# https://guide.pycord.dev/voice/receiving
import io
import discord
import os
import json
from discord.ext import commands
import speech_recognition as sr
from dotenv import load_dotenv
import tbone_transcriber
import asyncio

load_dotenv()

DISCORD_TOKEN = os.environ.get('CYRA_DISCORD')

# Create the bot
intents = discord.Intents.all()
intents.message_content = True
bot = discord.Bot()
connections = {}

global_discord_queue = None

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(name="hello", description="Say hello to the bot!")
async def hello(ctx: discord.ApplicationContext):
    await ctx.respond("Hey!")

@bot.slash_command(name='ping', description="Ping from Cyra")
async def ping(ctx: discord.ApplicationContext):
    await ctx.respond("pong")

@bot.slash_command()
async def record(ctx: discord.ApplicationContext):  # If you're using commands.Bot, this will also work.
    await ctx.respond(f"You are currently in {ctx.author.voice.channel.name}")
    voice = ctx.author.voice
    if not voice:
        await ctx.respond("You aren't in a voice channel!")
    vc = await voice.channel.connect()  # Connect to the voice channel the author is in.
    connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

    vc.start_recording(
        discord.sinks.WaveSink(),  # The sink type to use.
        once_done,  # What to do once done.
        ctx.channel  # The channel to disconnect from.
    )
    await ctx.respond("Started recording!")
    await asyncio.sleep(10)
    await stop_recording(ctx)

# @bot.command()
async def stop_recording(ctx: discord.ApplicationContext):
    if ctx.guild.id in connections:  # Check if the guild is in the cache.
        vc = connections[ctx.guild.id]
        vc.stop_recording()  # Stop recording, and call the callback (once_done).
        # del connections[ctx.guild.id]  # Remove the guild from the cache.
        # await ctx.delete()  # And delete.
        await ctx.respond("Done")
    else:
        await ctx.respond("I am currently not recording here.")  # Respond with this if we aren't recording.

async def save_files(files):
    saved_files = []
    for file in files:
        with open(file.filename, "wb") as f:
                f.write(file.fp.read())
                saved_files.append(file.filename)
    return saved_files

async def once_done(sink: discord.sinks, channel: discord.TextChannel, *args):  # Our voice client already passes these in.
    returned_transcription = {}
    saved_files = []
    recorded_users = [  # A list of recorded users
        f"<@{user_id}>"
        for user_id, audio in sink.audio_data.items()
    ]
    # await sink.vc.disconnect()  # Disconnect from the voice channel.
    
    files = [discord.File(audio.file, f"{user_id}.{sink.encoding}") for user_id, audio in sink.audio_data.items()]  # List down the files.
    for file in files:
        with open(file.filename, "wb") as f:
            f.write(file.fp.read())
            saved_files.append(file.filename)
        # await save_files(files)
    returned_transcription = tbone_transcriber.transcriber(saved_files)
    # print(f"d_b.py: pre loop: {returned_transcription}")
    for transcription in returned_transcription:
        print(f"d_b.py: for t in r_t: {transcription=}")

        # For Twitch
        transcription["formatted_msg"] = f"twitch:{transcription["msg_user"]}: {transcription["msg_msg"]}"
        transcription["msg_server"] = "pdgeorge"
        to_send = transcription

        print(f"{to_send=}")
        # Need to add in a basic "convert user ID to name" function here.
        # Don't need to hard code the things, can make it load from file for Discord ID/Name Key/Value pairs.
        global_discord_queue.put(json.dumps(to_send))
        
    await channel.send(f"Transcription for this message:\n\n{transcription["msg_msg"]}")  # Send a message with the transcription.

def start_bot(discord_queue):
    global global_discord_queue
    global_discord_queue = discord_queue
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    # To run the bot quickly
    import multiprocessing
    discord_queue = multiprocessing.Queue()
    start_bot(discord_queue)

    # For whatever we want to test.
    # asyncio.run(test())