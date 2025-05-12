import discord
from historical import *
from config import DISCORD_TOKEN

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


def list_commands():
    highest = 5
    commands = [
        "/commands: lists all available commands\n",
        f"/top sentiment: returns the {highest} stocks with the highest sentiment for the day\n",
        f"/top predictions: returns the {highest} stocks with the highest predicted price increase",
    ]
    message = ""

    return "```" + message.join(commands) + "```"


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("/commands"):
        commands = list_commands()
        await message.channel.send(commands)

    if message.content.startswith("$hello"):
        await message.channel.send("Hello!")

    if message.content.startswith("/top sentiment"):
        await message.channel.send("Getting top sentiment today...")
        # await message.channel.send()

    if message.content.startswith("/top predictions"):
        await message.channel.send("Getting top predictions...")


client.run(DISCORD_TOKEN)
