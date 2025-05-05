import random
import asyncio
import configparser
from time import sleep
from termcolor import colored
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.sync import TelegramClient
from telethon.events import NewMessage

def log(msg):
    print(colored("[+] " + msg, 'green'))

def warn(msg):
    print(colored("[!] " + msg, 'yellow'))

def err(msg):
    print(colored("[!!!] " + msg, 'red'))

log("Loading vocabulary...")

vocab = {}
with open("russian.txt", "r", encoding = "utf-8") as f:
    for word in f.readlines():
        vocab[word[0].lower()] = vocab.get(word[0].lower(), [])
        vocab[word[0].lower()].append(word.strip())

log("Vocabulary loaded! Status:")
for letter in vocab.keys():
    log(f"Letter: {letter} Num words: {len(vocab[letter])}")

def get_answer(word):
    word = word.lower().strip().replace('ь', '').replace('ъ', '').replace('ы', '')

    if not vocab.get(word[-1], None):
        warn(f"No letter like {word[-1]} found in db")
        return None

    if len(vocab[word[-1]]) == 0:
        warn(f"No more words for letter {word[-1]}")
        return "Хз"
    
    if (vocab[word[-1]].count(word) != 0):
        warn("Opponent word found in db, cleaning :(")
        vocab[word[-1]].pop(vocab[word[-1]].index(word))

    pos = random.randint(0, len(vocab[word[-1]]) - 1)
    answer = vocab[word[-1]][pos]
    vocab[word[-1]].pop(pos)

    return answer

config = configparser.ConfigParser()
config.read("config.ini", encoding="utf-8")

api_id = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']

phone = config['Telegram']['phone']
username = config['Telegram']['username']
client = TelegramClient(username, api_id, api_hash, device_model='iPhone 15 Pro Max', system_version="4.16.34-vxpetrol")

log("Starting telegram client")
client.connect()
if not client.is_user_authorized():
    phone_code_hash = client.send_code_request(phone).phone_code_hash
    try:
        client.sign_in(phone, input('Enter the code: '))
    except SessionPasswordNeededError:
        client.sign_in(password=input('Password: '))

chat_name = config["Words"]["chat_name"]

needed_dialog = None
for dialog in client.iter_dialogs():
    if dialog.name == chat_name:
        needed_dialog = dialog
        break

if needed_dialog:
    log("Got chat with needed name")
    @client.on(NewMessage(chats = [needed_dialog]))
    async def handler(event):
        if not event.out:
            log("New message!")
            if event.message.message and str(event.message.message).count(' ') == 0:
                log(f"Message valid, generating answer for word {event.message.message}")
                word = get_answer(event.message.message)
                if word:
                    log(f"Found answer: {word}!")
                    await asyncio.sleep(3)
                    await client.send_message(needed_dialog, word, reply_to=event.message.id)
                    log("Sent response with word")
                else:
                    warn("No answer :(")
            else:
                warn("Message not valid :(")

    client.run_until_disconnected()
else:
    err("Cannot find chat")
