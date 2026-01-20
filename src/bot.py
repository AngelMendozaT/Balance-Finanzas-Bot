import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from db import get_transactions_df, update_transaction_category, get_categories

# NOTE: THIS IS A TEMPLATE. 
# You need to put your actual TELEGRAM_BOT_TOKEN here or in an env variable.
BOT_TOKEN = "7686254070:AAFPbl9LgLIMF_mIB8KDi1ScoEByD8Uc1V4"

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👋 Hola! Soy tu bot de Finanzas. Te avisaré cuando haya gastos sin clasificar (como Yapes)."
    )

async def check_pending_transactions(context: ContextTypes.DEFAULT_TYPE, chat_id=None):
    """Scheduled job to check DB for unclassified items."""
    df = get_transactions_df()
    pending = df[df['status'] == 'pending_classification']
    
    # In a real app, you'd store the user's chat_id in the DB or config.
    # We allow passing chat_id explicitly (from manual message) or getting it from job (scheduled)
    if chat_id is None and context.job:
        chat_id = context.job.chat_id
    
    if chat_id is None:
        print("Warning: No chat_id found for checking transactions.")
        return
    
    for index, row in pending.iterrows():
        # Create buttons for categories
        cats = get_categories()
        # Limit to first 4 for UI simplicity + "Other"
        keyboard = [
            [InlineKeyboardButton(c, callback_data=f"cat_{row['id']}_{c}") for c in cats[:3]],
            [InlineKeyboardButton(c, callback_data=f"cat_{row['id']}_{c}") for c in cats[3:6]]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        msg = f"⚠️ **Gasto sin clasificar**\n\n💰 **S/ {row['amount']}**\n📅 {row['date']}\n📝 {row['description']}\nℹ️ Fuente: {row['source']}"
        
        await context.bot.send_message(chat_id=chat_id, text=msg, reply_markup=reply_markup)
        
        # Don't spam, maybe just 1 at a time or create a queue mechanism. 
        # For prototype, we break after 1 to verify flow.
        break 

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    # format: cat_{id}_{category}
    parts = data.split('_')
    if len(parts) >= 3 and parts[0] == 'cat':
        tx_id = parts[1]
        category = parts[2]
        
        # Update DB
        
        if update_transaction_category(tx_id, category):
            await query.edit_message_text(text=f"✅ Clasificado como: **{category}**")
        else:
            await query.edit_message_text(text=f"❌ Error al actualizar Google Sheets. Revisa la terminal del bot.")

# --- KEEP ALIVE FOR RENDER FREE TIER ---
from flask import Flask
from threading import Thread
import os

flask_app = Flask('')

@flask_app.route('/')
def home():
    return "I am alive! 🤖"

def run_http():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_http)
    t.start()
# ---------------------------------------

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages as new pending transactions."""
    text = update.message.text
    chat_id = update.effective_chat.id
    
    import re
    amounts = re.findall(r'\d+(?:\.\d+)?', text)
    amount = float(amounts[0]) if amounts else 0.0
    
    # Clean description: Remove the extracted number from the text
    description = text
    if amounts:
        # Simple replace (careful if number appears twice, but good enough for v1)
        description = text.replace(amounts[0], "", 1).strip()
        
    # Default description if empty
    if not description:
        description = "Gasto General"
    
    # Clean up extra spaces or punctuation
    description = description.strip(" .-,")
    if not description: description = "Gasto General" # Double check
    
    from db import add_transaction
    from datetime import datetime
    
    add_transaction(
        date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        amount=amount,
        description=description,
        source="Telegram Bot",
        category="Otros",
        status="pending_classification"
    )
    
    # Trigger the classification flow immediately
    await check_pending_transactions(context, chat_id=chat_id)
    
    # Acknowledge
    # await update.message.reply_text(f"📝 Gasto registrado: S/ {amount}. Clasifícalo arriba 👆")

if __name__ == '__main__':
    if BOT_TOKEN == "YOUR_TOKEN_HERE":
        print("⚠️ ERROR: Debes poner tu Token de Telegram en boto.py para que funcione.")
    else:
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CallbackQueryHandler(button_handler))
        
        # New: Handle text messages
        from telegram.ext import MessageHandler, filters
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        # Note: in a real deployment we would use JobQueue to check periodically.
        # For testing, you can trigger 'check' commands manually or run a loop.
        
        print("Bot iniciado...")
        
        # Start the dummy server
        keep_alive()
        
        application.run_polling()
