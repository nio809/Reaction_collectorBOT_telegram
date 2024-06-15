import telebot
import asyncio
import json
from telethon.sync import TelegramClient
from telethon import functions, types
import io

# Telegram Bot setup
BOT_TOKEN = '______________'
bot = telebot.TeleBot(BOT_TOKEN)

# Telethon Client setup
API_ID = "__________"
API_HASH = '___________'

# Initialize a global dictionary for caching user details
user_cache = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Please give me a message link.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    msg_link = message.text
    try:
        parts = msg_link.split('/')
        msg_id = int(parts[-1])
        identifier = parts[-2] if parts[-3] == 't.me' else ""
        if identifier:
            asyncio.run(log_message_reactions(msg_id, message.chat.id, msg_link, identifier))
        else:
            bot.reply_to(message, "Please provide a valid message link.")
    except ValueError:
        bot.reply_to(message, "Please provide a valid message link.")
    except Exception as e:
        bot.reply_to(message, f"An error occurred: {str(e)}")

async def log_message_reactions(message_id, chat_id, msg_link, identifier):
    content_stream = io.BytesIO()
    username_set = set()
    async with TelegramClient('session_name', API_ID, API_HASH) as client:
        entity = await client.get_entity(identifier)
        offset = ''
        while True:
            result = await client(functions.messages.GetMessageReactionsListRequest(
                peer=entity,
                id=message_id,
                limit=100,
                offset=offset
            ))
            if not result.reactions:
                break
            for reaction in result.reactions:
                user_id = reaction.peer_id.user_id
                if user_id in user_cache:
                    username = user_cache[user_id]
                else:
                    user_entity = await client.get_entity(reaction.peer_id)
                    username = user_entity.username
                    # Cache the username for future use
                    if username:
                        user_cache[user_id] = username
                if username:
                    username_set.add(username)
            offset = result.next_offset
            if not offset:
                break
        content_stream.write(f"Message Link: {msg_link}\nChannel/Group: @{identifier}\n\n".encode('utf-8'))
        for username in username_set:
            content_stream.write(f"{username}\n".encode('utf-8'))
        content_stream.seek(0)  
        bot.send_document(chat_id, ('reaction_results.txt', content_stream, 'text/plain'))

print(bot.get_me())
bot.infinity_polling()
