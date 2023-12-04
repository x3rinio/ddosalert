import discord
from discord.ext import commands, tasks
import psutil
import asyncio

#Bot token
TOKEN = 'token'

#log channel ID
CHANNEL_ID = 123456789123456789

#Alert cpu & request settings
CPU_THRESHOLD = 50
REQUEST_THRESHOLD = 10000
MIN_CPU_USAGE = 10  #when CPU usage drops below the value you specify, it sends a message that the attack is over.

#intents
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.presences = True  #Presence
client = commands.Bot(command_prefix="!", intents=intents)

#first
initial_message_id = None

#send messages & update
async def send_and_update_message():
    global initial_message_id

    channel = client.get_channel(CHANNEL_ID)

    while True:
        #cpu
        cpu_usage = psutil.cpu_percent(interval=1)

        #request
        connections = psutil.net_connections(kind="inet4")
        request_count = sum(1 for conn in connections if conn.laddr.port == 80 and conn.status == psutil.CONN_ESTABLISHED)

        #embed
        color = discord.Color.red() if cpu_usage > CPU_THRESHOLD or request_count > REQUEST_THRESHOLD else discord.Color.green()
        status_message = "Unexpected traffic detected" if color == discord.Color.red() else "Safe"
        embed = discord.Embed(color=color)
        embed.add_field(name="CPU", value=f"{cpu_usage}%", inline=True)
        embed.add_field(name="Requests", value=request_count, inline=True)
        embed.add_field(name="Status", value=status_message, inline=False)
        embed.set_footer(text="Data is updated instantly")

        if initial_message_id:
            message = await channel.fetch_message(initial_message_id)
            await message.edit(embed=embed)
            #print("messages updated.")
        else:
            message = await channel.send(embed=embed)
            initial_message_id = message.id
            #print("send log messages.")

        await asyncio.sleep(1)  #Message update interval

@client.event
async def on_ready():
    global initial_message_id
    print(f'We have logged in as {client.user}')
    #activity = discord.Activity(type=discord.ActivityType.watching, name="X")
    #await client.change_presence(activity=activity)

    #delete bot's old messages
    await cleanup_messages()

    #update function
    await send_and_update_message()

#function
async def cleanup_messages():
    global initial_message_id
    channel = client.get_channel(CHANNEL_ID)

    #check bot messages
    bot_messages = [message async for message in channel.history() if message.author == client.user]

    #delete bot's old messages
    await channel.delete_messages(bot_messages)

    initial_message_id = None
    #print("Bot messages have been cleared.")

#run
client.run(TOKEN)
