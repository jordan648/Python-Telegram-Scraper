#This is a script to scrape messages from a Telegram channel using the Telethon library. It includes functions to join a channel and scrape messages.
#Install the Telethon library using the pip install telethon command in power shell or terminal.
#For educational purposes only. Use responsibly and ethically.

from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
import os
import asyncio
import json

#For your api_id and your api_hash you have two options.
#1. copy and paste the api_id and api_hash from my.telegram.org directly into the variables below.
#2. Create a .env file with the api_id and api_hash variables and set them to your api_id and api_hash from my.telegram.org.

api_id = 28696114

api_hash = '2adbd87c2b4dabf9fab4405d0a820450'

#By default, Telethon will use the session name 'anon' to store your session information.
#You can change the session name below to anything you want. It will not effect the functionality.

client = TelegramClient('anon', api_id, api_hash)

async def join_channel(client, channel_link):
    try:
        await client(JoinChannelRequest(channel_link))
        print(f"Successfully joined {channel_link}")
    except Exception as e:
        print(f"Failed to join {channel_link}; Error: {e}")

#Modify the amount of messages to scrape by adjusting the limit parameter in the scrape_messages function below. The default is 100 messages.

async def scrape_messages(client, channel_link, limit=100, output_file='scraped_messages.txt'):
    await client.start()
    try:
        channel = await client.get_input_entity(channel_link)
        count = 0 # Initialize message count
        with open(output_file, 'w', encoding='utf-8') as f:
            async for message in client.iter_messages(channel, limit=limit): 
                if message.text: 
                    f.write(message.text + '\n')
                    count += 1
                    print(f"Message {count}: {message.text}") # Print message count
        print(f"Scraped {count} messages from {channel_link} and saved to {output_file}") 
    except Exception as e:
        print(f"Failed to scrape messages from {channel_link}; Error: {e}")

async def main():
        #Reads channel links from a JSON file
    with open('channel_links.json', 'r') as f:
        data = json.load(f)
        channel_link = data.get('channel_link', [])

    if not channel_link:
        print("No channel links provided in JSON file.")
        return
    for channel_link in channel_link:
        await join_channel(client, channel_link)
        output_file = f"scraped_messages_{channel_link.split('/')[-1]}.txt" # Create a unique output file name for each channel
        await scrape_messages(client, channel_link, limit=100, output_file=output_file)

with client:
    client.loop.run_until_complete(main())