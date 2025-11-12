import sqlite3

def init_db():
    conn = sqlite3.connect('smm_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, coins INTEGER DEFAULT 100, referred_by INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, service TEXT, quantity INTEGER, status TEXT)''')
    conn.commit()
    conn.close()

def ensure_user(user_id):
    conn = sqlite3.connect('smm_bot.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, coins) VALUES (?, 100)", (user_id,))
    conn.commit()
    conn.close()

def get_coins(user_id):
    ensure_user(user_id)
    conn = sqlite3.connect('smm_bot.db')
    c = conn.cursor()
    c.execute("SELECT coins FROM users WHERE user_id=?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 100

def add_coins(user_id, amount):
    ensure_user(user_id)
    conn = sqlite3.connect('smm_bot.db')
    c = conn.cursor()
    c.execute("UPDATE users SET coins = coins + ? WHERE user_id=?", (amount, user_id))
    conn.commit()
    conn.close()

def deduct_coins(user_id, amount):
    ensure_user(user_id)
    if get_coins(user_id) >= amount:
        add_coins(user_id, -amount)
        return True
    return False

def add_referral(referrer_id, new_user_id):
    add_coins(referrer_id, 200)
