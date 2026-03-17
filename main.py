import asyncio
import logging
import json
import os
import time

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from fastapi import FastAPI
import uvicorn

BOT_TOKEN = "8642610734:AAGNdlZYEMOTzuQpzLMpRVvTxTE6GX99I4E"
GROUP_ID = -5235511349  # adminlar guruh IDsi

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

MESSAGES_DB_FILE = "messages_db.json"
last_message_time = {}

class TrustBox(StatesGroup):
    waiting_for_message = State()

def load_messages_db():
    if os.path.exists(MESSAGES_DB_FILE):
        try:
            with open(MESSAGES_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_messages_db(db):
    with open(MESSAGES_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def add_message_link(msg_id, user_data):
    db = load_messages_db()
    db[str(msg_id)] = user_data
    save_messages_db(db)

def get_user_data(msg_id):
    db = load_messages_db()
    return db.get(str(msg_id))

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await message.answer("Botga savolingizni yo‘llang.")
    await state.set_state(TrustBox.waiting_for_message)

@dp.message(TrustBox.waiting_for_message)
async def send_text(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
    now = time.time()

    if user_id in last_message_time and now - last_message_time[user_id] < 10:
        return  # kutish xabari yo‘q

    last_message_time[user_id] = now

    # Foydalanuvchi ma'lumotlari bilan xabar
    text = (
        f"🆔 ID: {user_id}\n"
        f"💻 Username: @{username}\n______________________\n\n"
        f"💬 Murojaat: {message.text}"
    )

    # Guruhga yuborish
    sent = await bot.send_message(GROUP_ID, text)
    add_message_link(sent.message_id, {"user_id": user_id, "username": username, "full_name": full_name})

    # State tozalash
    await state.clear()

# Admin reply
@dp.message(F.chat.id == GROUP_ID, F.reply_to_message)
async def admin_reply(message: types.Message):
    replied_msg_id = message.reply_to_message.message_id
    user_data = get_user_data(replied_msg_id)

    if user_data:
        user_id = user_data.get("user_id")
        await bot.send_message(user_id, message.text)

# FastAPI + Bot
app = FastAPI()

@app.on_event("startup")
async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)
    asyncio.create_task(dp.start_polling(bot, skip_updates=True))

@app.get("/")
def home():
    return {"status": "Bot ishlayapti"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
