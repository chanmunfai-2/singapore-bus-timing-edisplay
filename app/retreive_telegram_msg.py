import asyncio
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (ApplicationBuilder, ContextTypes, MessageHandler,
                          filters)

# Load environment variables
load_dotenv()

TOKEN = "8689214344:AAGjQ9vDouN1yxVkjq5TdEi_NfTrHs-dBFg"

# ✅ Only this Telegram user can control the Pi
ALLOWED_ID = int(os.getenv('ALLOWED_TELEGRAM_ID'))  

OUTPUT_FILE = "telegram_msg.txt"
# OUTPUT_FILE = "/home/pi/singapore-bus-timing-edisplay/telegram_msg.txt"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    # 🔒 Security check
    if user_id != ALLOWED_ID:
        print(f"Blocked user: {user_id}")
        await update.message.reply_text("Unauthorized access.")
        return

    print("Telegram received:", text)

    # Write message to shared file
    with open(OUTPUT_FILE, "w", encoding = "utf-8") as f:
        f.write(text)

    await update.message.reply_text("Message sent to Raspberry Pi display!")

def run_bot():
    # Create event loop for this thread 
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT, handle_message)
    )

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    run_bot()