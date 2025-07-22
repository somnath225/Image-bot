import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json
import os
from datetime import datetime, timedelta
import asyncio
import nest_asyncio

BOT_TOKEN = "8170149621:AAGYeNRnQfA3QtuLe11ccL3Hti7e3p0Ebi8"
DATA_FILE = "user_requests.json"
ALLOWED_USERS_FILE = "allowed_users.json"
DAILY_LIMIT = 15
SUBSCRIPTION_LINK = "http://T.me/Gen_Z_sanemi"

# Load user request data from JSON file
def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

# Save user request data to JSON file
def save_user_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Load allowed users from JSON file
def load_allowed_users():
    if os.path.exists(ALLOWED_USERS_FILE):
        with open(ALLOWED_USERS_FILE, "r") as f:
            return json.load(f)
    return []

# Save allowed users to JSON file
def save_allowed_users(allowed_users):
    with open(ALLOWED_USERS_FILE, "w") as f:
        json.dump(allowed_users, f, indent=4)

# Check if the current day has changed to reset counts
def check_reset_user_data():
    user_data = load_user_data()
    current_date = datetime.utcnow().date().isoformat()
    
    # If the date in the data is not today, reset counts
    if user_data.get("date") != current_date:
        user_data = {"date": current_date, "users": {}}
        save_user_data(user_data)
    return user_data

# /start command response
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! Send me a prompt, I will create a picture for you! (made by: @moddingmaniaaa)")

# /allow command to add a user to the unlimited list (only for bot admin)
async def allow_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Replace this with your Telegram user ID to restrict who can use /allow
    ADMIN_ID = YOUR_ADMIN_TELEGRAM_ID  # Replace with your Telegram ID (integer)
    
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Please provide a Telegram user ID to allow.")
        return
    
    try:
        user_id = int(context.args[0])
        allowed_users = load_allowed_users()
        if user_id not in allowed_users:
            allowed_users.append(user_id)
            save_allowed_users(allowed_users)
            await update.message.reply_text(f"✅ User {user_id} has been allowed unlimited image generation.")
        else:
            await update.message.reply_text(f"ℹ️ User {user_id} is already allowed.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Please provide a numeric Telegram user ID.")

# /remove command to remove a user from the unlimited list (only for bot admin)
async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = YOUR_ADMIN_TELEGRAM_ID  # Replace with your Telegram ID (integer)
    
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("❌ Please provide a Telegram user ID to remove.")
        return
    
    try:
        user_id = int(context.args[0])
        allowed_users = load_allowed_users()
        if user_id in allowed_users:
            allowed_users.remove(user_id)
            save_allowed_users(allowed_users)
            await update.message.reply_text(f"✅ User {user_id} has been removed from unlimited access.")
        else:
            await update.message.reply_text(f"ℹ️ User {user_id} is not in the allowed list.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Please provide a numeric Telegram user ID.")

# Image generation with user limit check
async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    prompt = update.message.text
    
    # Load allowed users
    allowed_users = load_allowed_users()
    
    # Check if user is allowed unlimited access
    if user_id in allowed_users:
        await update.message.reply_text("🖼️ Creating a picture (You're Pro member)...")
    else:
        # Check and reset user data if needed
        user_data = check_reset_user_data()
        user_requests = user_data.get("users", {}).get(str(user_id), 0)
        
        # Check if user has reached the daily limit
        if user_requests >= DAILY_LIMIT:
            await update.message.reply_text(
                f"❌ You have reached the daily limit of {DAILY_LIMIT} image generations. "
                f"Get a subscription for unlimited access: {SUBSCRIPTION_LINK}"
            )
            return
        
        # Increment request count
        user_data["users"][str(user_id)] = user_requests + 1
        save_user_data(user_data)
        await update.message.reply_text(f"🖼️ Creating a picture... (Request {user_requests + 1}/{DAILY_LIMIT})")

    try:
        # Magic Studio API request
        api_url = f"https://magic-studio.ziddi-beatz.workers.dev/?prompt={prompt}"
        response = requests.get(api_url)

        # Check if response is valid and content is an image
        if response.status_code == 200 and response.headers["Content-Type"].startswith("image"):
            await update.message.reply_photo(photo=response.content, caption=f"Join @moddingmaniaaa\n🎨 Prompt: {prompt}")
        else:
            await update.message.reply_text("❌ There was a problem loading the image.")
            await update.message.reply_text(response.text)

    except Exception as e:
        await update.message.reply_text(f"❗ Error:\n{str(e)}")

# Main function to run the bot
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("allow", allow_user))
    app.add_handler(CommandHandler("remove", remove_user))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, generate_image))

    print("🤖 Bot is running 💨...")
    await app.run_polling()

# Termux or async runner
if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())