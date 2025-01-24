#This is a script to scrape messages from a Telegram channel using the Telethon library. It includes functions to join a channel and scrape messages.
#Install the Telethon library using the pip install telethon command in power shell or terminal.
#For educational purposes only. Use responsibly and ethically.

from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
import os
import asyncio
import json
from dotenv import load_dotenv
from telethon.tl.types import Channel
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer

load_dotenv()

nltk.download('stopwords')

#For your api_id and your api_hash you have two options.
#1. copy and paste the api_id and api_hash from my.telegram.org directly into the variables below.
#2. Create a .env file with the api_id and api_hash variables and set them to your api_id and api_hash from my.telegram.org.

api_id = os.getenv("API_ID")

api_hash = os.getenv("API_HASH")

stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

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
                    print(f"Message {count}") # Print message count
        print(f"Scraped {count} messages from {channel_link} and saved to {output_file}") 
    except Exception as e:
        print(f"Failed to scrape messages from {channel_link}; Error: {e}")

async def search_for_channels(client, keywords):
    await client.start()
    matching_channels = []

    async for dialog in client.iter_dialogs():
        if isinstance(dialog.entity, Channel):
            channel_name = dialog.name.lower()
            for keyword in keywords:
                if keyword.lower() in channel_name:
                    print(f"Found channel: {dialog.name} ({dialog.entity.id})")
                    matching_channels.append(dialog.entity)
                    break
    return matching_channels

async def main():
        #Reads channel links from a JSON file
    with open('channel_links.json', 'r') as f:
        data = json.load(f)
        channel_link = data.get('channel_link', [])

    if not channel_link:
        print("No channel links provided in JSON file.")
        return
    
    try:
        with open('keywords.json', 'r') as f:
            data = json.load(f)
            keywords = data.get('keywords', [])
    except FileNotFoundError:
        print("No keywords provided in JSON file.")
        return
    
    if not keywords:
        print("No keywords provided in JSON file.")
        return

     #Search for channels matching the keywords
    
    print("Searching for channels...")
    found_channels = await search_for_channels(client, keywords)
    print(f"Found {len(found_channels)} channels matching the keywords.")

    all_channels = list(set(channel_link)) + found_channels  # Combine unique channels from JSON and search results

    for channel in found_channels:
        channel_link = f"https://t.me/{channel.username}" if channel.username else None
        if channel_link:
            all_channels.append(channel_link)  # Add the channel link to the list

    for channel_link in all_channels:
        print(f"Joining and scraping {channel_link}...")
        await join_channel(client, channel_link) # Join the channel if not already a member

        await asyncio.sleep(5)  # Sleep for 5 seconds to avoid hitting the rate limit

        output_file = f"scraped_messages_{channel_link.split('/')[-1]}.txt" # Create a unique output file name for each channel
        await scrape_messages(client, channel_link, limit=100, output_file=output_file)  # Scrape messages from the channel

        await asyncio.sleep(5)  # Sleep for 5 seconds to avoid hitting the rate limit

with client:
    client.loop.run_until_complete(main())