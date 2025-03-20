import logging
from telegram import Update, InputFile, ChatPermissions
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackContext
import sqlite3
import requests
import os

# Basic configurations
TOKEN = "YOUR_BOT_TOKEN"
ADMIN_IDS = [123456789]  # Admin user IDs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Database setup
conn = sqlite3.connect('bot.db', check_same_thread=False)
c = conn.cursor()

# Create tables
c.execute('''CREATE TABLE IF NOT EXISTS users 
             (user_id INTEGER PRIMARY KEY, username TEXT, joined_at DATETIME)''')

c.execute('''CREATE TABLE IF NOT EXISTS mandatory_channels 
             (channel_id INTEGER PRIMARY KEY, invite_link TEXT, is_private BOOLEAN)''')

c.execute('''CREATE TABLE IF NOT EXISTS ads 
             (ad_id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, media BLOB)''')

c.execute('''CREATE TABLE IF NOT EXISTS optional_channels 
             (channel_id INTEGER PRIMARY KEY, invite_link TEXT)''')

conn.commit()

# -------------------- Helper Functions --------------------
def check_membership(update: Update, context: CallbackContext):
    """Verify if user has joined all mandatory channels"""
    user_id = update.effective_user.id
    c.execute("SELECT channel_id, is_private FROM mandatory_channels")
    mandatory_channels = c.fetchall()
    
    for channel_id, is_private in mandatory_channels:
        try:
            member = context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            print(f"Membership check error: {e}")
            return False
    return True

# -------------------- User Commands --------------------
def start(update: Update, context: CallbackContext):
    """Handle /start command"""
    user = update.effective_user
    if not check_membership(update, context):
        update.message.reply_text("❌ You must join mandatory channels to use the bot!")
        return
    
    # Save user data
    c.execute("INSERT OR IGNORE INTO users (user_id, username, joined_at) VALUES (?,?,datetime('now'))",
              (user.id, user.username))
    conn.commit()
    
    update.message.reply_text("Welcome! Please send your desired URL.")

def handle_url(update: Update, context: CallbackContext):
    """Process user-submitted URLs"""
    if not check_membership(update, context):
        return
    
    url = update.message.text
    try:
        # File download logic (to be implemented)
        # file_path = download_file(url)
        
        # Send file to user
        # context.bot.send_document(chat_id=update.effective_chat.id, document=InputFile(file_path))
        
        # Send random ad
        c.execute("SELECT content FROM ads ORDER BY RANDOM() LIMIT 1")
        ad = c.fetchone()
        if ad:
            update.message.reply_text(ad[0])
            
    except Exception as e:
        update.message.reply_text("❌ Error processing request")

# -------------------- Admin Commands --------------------
def admin_stats(update: Update, context: CallbackContext):
    """Show bot statistics"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    c.execute("SELECT COUNT(*) FROM users")
    user_count = c.fetchone()[0]
    
    stats_text = f"📊 Bot Statistics:\nTotal Users: {user_count}"
    update.message.reply_text(stats_text)

def add_ad(update: Update, context: CallbackContext):
    """Add new advertisement (to be implemented)"""
    pass

def broadcast(update: Update, context: CallbackContext):
    """Broadcast messages (to be implemented)"""
    pass

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # User command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(None, handle_url))

    # Admin command handlers
    dp.add_handler(CommandHandler("stats", admin_stats))
    dp.add_handler(CommandHandler("add_ad", add_ad))
    dp.add_handler(CommandHandler("broadcast", broadcast))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()