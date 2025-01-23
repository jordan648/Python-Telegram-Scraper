#This is a script to scrape messages from a Telegram channel using the Telethon library. It includes functions to join a channel and scrape messages.
#Install the Telethon library using the pip install telethon command in power shell or terminal.
#For educational purposes only. Use responsibly and ethically.

from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
import os

api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')

client = TelegramClient('anon', api_id, api_hash)

async def join_channel(client, channel_link):
    try:
        await client(JoinChannelRequest(channel_link))
        print(f"Successfully joined {channel_link}")
    except Exception as e:
        print(f"Failed to join {channel_link}: {e}")

#modify the amount of messages to scrape by adjusting the limit parameter in the scrape_messages function below. The default is 100 messages.

async def scrape_messages(client, channel_link, limit=100):
    await client.start()
    channel = await client.get_input_entity(channel_link)
    async for message in client.iter_messages(channel, limit=limit):
        #Prints the message contents
        print(message.stringify())

async def main():

    # add a variable here to store the channel link
        # example: channel_link = 'https://t.me/your_channel_link'

    await join_channel(client, 'https://t.me/your_channel_link')
    await scrape_messages(client, 'https://t.me/your_channel_link', limit=50)

with client:
    client.loop.run_until_complete(main())