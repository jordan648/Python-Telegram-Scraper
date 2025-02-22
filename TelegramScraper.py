#This is a script to scrape messages from a Telegram channel using the Telethon library. It includes functions to join a channel and scrape messages.
#Install the Telethon library using the pip install telethon command in power shell or terminal.
#For educational purposes only. Use responsibly and ethically.
import nltk
import signal
import multiprocessing
import pandas as pd
import hashlib
import os
import asyncio
import json
import logging
from dotenv import load_dotenv
from telethon.tl.types import Channel
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer
from nltk.sentiment import SentimentIntensityAnalyzer
from functools import partial
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel
from fuzzywuzzy import fuzz


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

nltk.download('stopwords')
nltk.download('vader_lexicon')
nltk.download('punkt')

#For your api_id and your api_hash you have two options.
#1. copy and paste the api_id and api_hash from my.telegram.org directly into the variables below.
#2. Create a .env file with the api_id and api_hash variables and set them to your api_id and api_hash from my.telegram.org.

api_id = os.getenv("API_ID")

api_hash = os.getenv("API_HASH")

sia = SentimentIntensityAnalyzer()
stemmer = PorterStemmer()
stop_words = set(stopwords.words('english'))

#By default, Telethon will use the session name 'anon' to store your session information.
#You can change the session name below to anything you want. It will not effect the functionality.

client = TelegramClient('anon', api_id, api_hash)



def ensure_nltk_data():
    try:
        nltk.download('stopwords')
        nltk.download('vader_lexicon')
        nltk.download('punkt')
        nltk.download('maxent_ne_chunker')
        nltk.download('words')
        nltk.download('punkt_tab')
        nltk.download('tokenize')
        nltk.download('averaged_perceptron_tagger_eng')
        nltk.download('maxent_ne_chunker_tab')
        logging.info("NLTK data verified and downloaded successfully.")
    except Exception as e:
        logging.error(f"Error downloading NLTK data: {e}")

def analyze_sentiment(message):
    return sia.polarity_scores(message)


def preprocess_keywords(keywords):
    return [stemmer.stem(word) for word in keywords if word.lower() not in stop_words]

def preprocess_message(message):
    words = word_tokenize(message)
    return [stemmer.stem(word.lower()) for word in words if word.lower() not in stop_words]

def named_entity_recognition(message):
    words= word_tokenize(message)
    pos_tags = nltk.pos_tag(words)
    return nltk.ne_chunk(pos_tags)

async def join_channel(client, channel_link):
    try:
        await client(JoinChannelRequest(channel_link))
        logging.info(f"Successfully joined {channel_link}")
    except Exception as e:
        logging.error(f"Failed to join {channel_link}; Error: {e}")

#Modify the amount of messages to scrape by adjusting the limit parameter in the scrape_messages function below. The default is 100 messages.

async def scrape_messages(client, channel_link, limit=100, output_file=None):
    await client.start()
    try:
        channel = await client.get_input_entity(channel_link)
        count = 0 # Initialize message count
        if output_file is None:
            unique_name = hashlib.md5(channel_link.encode()).hexdigest()
            output_file = f"scraped_messages_{unique_name}.csv" # Generate a unique name for the output file based on the channel link

        df = pd.DataFrame(columns=['Message Number', 'Text', 'Sentiment', 'Entities', 'Sentences', 'Words']) # Create a dataframe to store the messages 

        async for message in client.iter_messages(channel, limit=limit): 
            if message.text: 
                count += 1
                #Tokenize the message
                sentences = sent_tokenize(message.text) # Tokenize the message into sentences
                words = word_tokenize(message.text) # Tokenize the message into words
                sentiment = analyze_sentiment(message.text) # Analyze sentiment of the message
                entities = named_entity_recognition(message.text) # Perform named entity recognition on the message
                message_df = pd.DataFrame([{
                    'Message Number': count, 
                    'Text': message.text, 
                    'Sentiment': sentiment, 
                    'Entities': entities, 
                    'Sentences': sentences, 
                    'Words': words
                }]) # Add the message to the dataframe

                df = pd.concat([df, message_df], ignore_index=True) # Concatenate the message dataframe with the main dataframe

                logging.info(f"Message {count}") # Print message count

        df.to_csv(output_file, index=False)
        logging.info(f"Scraped {count} messages from {channel_link} and saved to {output_file}") 
    except Exception as e:
        logging.error(f"Failed to scrape messages from {channel_link}; Error: {e}")

async def search_for_channels_by_messages(client, keywords, message_limit=100, threshold=80):
    matching_channels = []
    async for dialog in client.iter_dialogs():
        if isinstance(dialog.entity, Channel):
            channel = dialog.entity
            async for message in client.iter_messages(channel, limit=message_limit):
                if message.text:
                    for keyword in keywords:
                        if fuzz.partial_ratio(keyword.lower(), message.text.lower()) >= threshold:
                            logging.info(f"Found Keyword '{keyword}' in channel: {dialog.name} ({dialog.entity.id})")
                            matching_channels.append(channel)
                            break
    return matching_channels

async def main():
    ensure_nltk_data()  # Ensure NLTK data is available

        #Reads channel links from a JSON file
    with open('channel_links.json', 'r') as f:
        data = json.load(f)
        channel_link = data.get('channel_link', [])

    if not channel_link:
        logging.error("No channel links provided in JSON file.")
        return
    
    try:
        with open('keywords.json', 'r') as f:
            data = json.load(f)
            keywords = data.get('keywords', [])

    except FileNotFoundError:
        logging.error("No keywords provided in JSON file.")
        return
    
    if not keywords:
        logging.error("No keywords provided in JSON file.")
        return

     #Search for channels matching the keywords
    
    logging.info("Searching for channels by messages...")
    found_channels = await search_for_channels_by_messages(client, keywords)
    logging.info(f"Found {len(found_channels)} channels matching the keywords in messages.")

    unique_channel_links = list(set(channel_link)) + found_channels  # Combine unique channels from JSON and search results

    tasks = []  # List to hold all tasks
    for channel in found_channels:
        channel_link = f"https://t.me/{channel.username}" if channel.username else None
        if channel_link:
            unique_channel_links.append(channel_link)  # Add the channel link to the list

    for channel_link in unique_channel_links:
        logging.info(f"Joining and scraping {channel_link}...")
        tasks.append(join_channel(client, channel_link)) # Join the channel if not already a member
        tasks.append(scrape_messages(client, channel_link, limit=100)) # Scrape messages from the channel
        await asyncio.sleep(0.1)  # Sleep for 5 seconds to avoid hitting the rate limit

    await asyncio.gather(*tasks)

with client:
    client.loop.run_until_complete(main())