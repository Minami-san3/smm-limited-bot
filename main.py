from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import os  # Added for env vars (TOKEN, RENDER_EXTERNAL_HOSTNAME)

# Safe imports (try database/services; fallback for testing)
try:
    from database import init_db, get_coins, add_referral
    from services import SERVICES, place_order
except ImportError as e:
    print(f"Import warning: {e} - Using stubs")
    # Stubs for testing
    def init_db(): pass
    def get_coins(user_id): return 100
    def add_referral(*args): pass
    def place_order(*args): return True, "Test order placed"

TOKEN = os.getenv('TOKEN', '8321583424:AAEbGM9I_twGPty-6qmZmVJIusj3NGQSsAI')  # Env fallback to your token

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    coins = get_coins(user_id)
    if coins == 100:  # First time
        await update.message.reply_text("Welcome! Join @ktgworld for bonuses & referrals (200 coins per friend)!")
    keyboard = [[InlineKeyboardButton("Platforms", callback_data='platforms')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"🛒 SMM Panel | Coins: {coins}\nSelect to start:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'platforms':
        platforms = list(SERVICES.keys())
        keyboard = [[InlineKeyboardButton(p, callback_data=f'plat_{p}')] for p in platforms]
        keyboard.append([InlineKeyboardButton("Back", callback_data='start')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📱 Select Platform:", reply_markup=reply_markup)
    elif query.data.startswith('plat_'):
        platform = query.data[5:]
        services = list(SERVICES[platform].keys())
        keyboard = [[InlineKeyboardButton(s, callback_data=f'serv_{platform}_{s}')] for s in services]
        keyboard.append([InlineKeyboardButton("Back", callback_data='platforms')])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"🔧 Services for {platform}:", reply_markup=reply_markup)
    # TODO: Add service select → prompt /order format

# Order handler (e.g., /order TikTok Followers 100 https://link)
async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 3:
        await update.message.reply_text("Usage: /order <Platform> <Service> <Quantity> <Link>\nE.g., /order TikTok Followers 100 https://tiktok.com/@user")
        return
    platform = context.args[0]
    serv = context.args[1]
    try:
        quantity = int(context.args[2])
        link = ' '.join(context.args[3:])
    except:
        await update.message.reply_text("Invalid quantity/link")
        return
    user_id = update.effective_user.id
    service_name = f"{platform} {serv}"
    success, msg = place_order(service_name, quantity, link, user_id)
    await update.message.reply_text(f"{'✅ ' if success else '❌ '}{msg}")

# Referral (e.g., /refer 123456789 - user_id)
async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        new_user_id = int(context.args[0])
        referrer_id = update.effective_user.id
        add_referral(referrer_id, new_user_id)
        await update.message.reply_text("Referral added! +200 coins to you.")
    else:
        await update.message.reply_text("Usage: /refer <friend_user_id>")

def main():
    init_db()  # Safe call here
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("order", order))
    app.add_handler(CommandHandler("refer", refer))
    app.add_handler(CallbackQueryHandler(button))
    
    # Webhook for Render (always-on)
    port = int(os.environ.get('PORT', 8443))
    webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'smm-limited-bot.onrender.com')}/{TOKEN}"
    app.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=TOKEN,
        webhook_url=webhook_url
    )

if __name__ == '__main__':
    main()
