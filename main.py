import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from fastapi import FastAPI
import uvicorn
import os

BOT_TOKEN = "8642880674:AAErcK9ZsHkrKPVRd1_Ayj59MBnjjFjB4ho"
GROUP_ID = -1003881398546  # Guruh ID

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# =======================
# FSM State
# =======================
class TrustBox(StatesGroup):
    waiting_for_message = State()


# =======================
# /start
# =======================
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.set_state(TrustBox.waiting_for_message)
    await message.answer("📩 Habar yuboring\nAdminlar siz bilan bogʻlanadi\n\n@axetm")


# =======================
# Foydalanuvchi xabari → guruhga forward
# =======================
@dp.message(TrustBox.waiting_for_message)
async def forward_to_group(message: types.Message):
    user = message.from_user

    info = (
        f"🆔 ID: {user.id}\n"
        f"🔗 Username: @{user.username if user.username else 'yo‘q'}"
    )

    # Foydalanuvchi info
    await bot.send_message(GROUP_ID, info)

    # Xabarni forward qilish
    await message.forward(GROUP_ID)


# =======================
# Admin reply → userga
# =======================
@dp.message(lambda message: message.chat.id == GROUP_ID and message.reply_to_message)
async def reply_to_user(message: types.Message):
    replied = message.reply_to_message
    if replied.forward_from:
        user_id = replied.forward_from.id
        await bot.send_message(user_id, message.text)


# =======================
# FastAPI + polling
# =======================
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
