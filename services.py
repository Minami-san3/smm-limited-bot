import requests
import os

# Try import (safe for solo run; main.py handles full)
try:
    from database import deduct_coins, add_coins
except ImportError:
    # Fallback stubs for testing services.py alone
    def deduct_coins(user_id, amount): return True  # Skip for test
    def add_coins(user_id, amount): pass

# Peakerr API Config (Use env for hosting)
PEAKERR_URL = 'https://peakerr.com/api/add'
PEAKERR_KEY = os.getenv('PEAKERR_KEY', '3868876076f5b6bf11ecf19c63a2a93c')

# Service Rates (coins per 1000 units)
SERVICES = {
    'TikTok': {'Followers': 100, 'Likes': 50, 'Comments': 150},
    'Instagram': {'Followers': 120, 'Likes': 60, 'Comments': 200, 'Views': 40},
    'YouTube': {'Subscribers': 200, 'Likes': 70, 'Comments': 180, 'Views': 30},
    'Twitter': {'Followers': 110, 'Likes': 55, 'Retweets': 90, 'Comments': 160},
    'Facebook': {'Followers': 130, 'Likes': 65, 'Shares': 100, 'Comments': 170},
    'Telegram': {'Members': 80},
    'WhatsApp': {'Channel Members': 90, 'Group Members': 95}
}

# Peakerr Service IDs (Your Real Ones - From Dashboard)
SERVICE_IDS = {
    # TikTok
    'TikTok Followers': 24823,
    'TikTok Likes': 16496,
    'TikTok Comments': 19856,
    # Instagram
    'Instagram Followers': 16350,
    'Instagram Likes': 27238,
    'Instagram Comments': 15665,
    'Instagram Views': 19198,
    # YouTube
    'YouTube Subscribers': 23304,
    'YouTube Likes': 22066,
    'YouTube Comments': 17868,
    'YouTube Views': 13897,
    # Twitter
    'Twitter Followers': 15030,
    'Twitter Likes': 10714,
    'Twitter Retweets': 20892,
    'Twitter Comments': 18032,
    # Facebook
    'Facebook Followers': 24882,
    'Facebook Likes': 15613,
    'Facebook Shares': 3079,
    'Facebook Comments': 19940,
    # Telegram
    'Telegram Members': 14455,
    # WhatsApp
    'WhatsApp Channel Members': 18706,
    'WhatsApp Group Members': 18706,
}

def place_order(service_name, quantity, link, user_id):
    # Parse service (e.g., "TikTok Followers")
    platform = service_name.split(' ', 1)[0] if ' ' in service_name else service_name
    serv = service_name.split(' ', 1)[1] if ' ' in service_name else service_name
    full_service = f"{platform} {serv}"  # e.g., "TikTok Followers"
    
    # Get rate and ID
    rate = SERVICES.get(platform, {}).get(serv, 100)
    service_id = SERVICE_IDS.get(full_service)
    if not service_id:
        return False, "Invalid service—check IDs in dashboard"
    
    cost = (quantity // 1000) * rate + (1 if quantity % 1000 else 0) * (rate // 10)  # Rough per-unit calc
    if not deduct_coins(user_id, cost):
        return False, "Insufficient coins"
    
    # Peakerr API Call (Fixed: 'key' param)
    data = {
        'key': PEAKERR_KEY,  # Fixed empty key
        'action': 'add',
        'service': service_id,
        'link': link,
        'quantity': quantity
    }
    response = requests.post(PEAKERR_URL, data=data)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('error') == 0:  # Success
            order_id = result.get('order')
            print(f"✅ Peakerr order placed: ID {order_id} for {full_service} x{quantity}")
            return True, f"Order {order_id} started! Delivery 1-24h."
        else:
            error_msg = result.get('error_message', 'Unknown error')
            print(f"❌ Peakerr error: {error_msg}")
            # Refund coins on failure
            add_coins(user_id, cost)  # Assume add_coins exists in database.py
            return False, f"Provider error: {error_msg} (Refunded coins)"
    else:
        print(f"❌ HTTP error: {response.status_code}")
        return False, "Connection failed—try later"

# Special handling for TikTok Comments (Generate + Post)
def place_tiktok_comments(quantity, video_url, user_id):
    comments = generate_comments(video_url, quantity)
    success_count = 0
    for comment in comments:
        # Post one comment at a time via Peakerr (adjust if they batch)
        # Note: Peakerr may need 'comment' param—add if available: data['comment'] = comment
        _, msg = place_order('TikTok Comments', 1, video_url, user_id)
        if msg.startswith("Order"):  # Success
            success_count += 1
    return success_count == quantity, f"Posted {success_count}/{quantity} AI comments"

# AI Comments for TikTok (Groq - Use env for hosting)
def generate_comments(video_url, num=10):
    desc = "Fun dance video"  # Placeholder—expand: use requests.get to scrape TikTok desc if needed
    from groq import Groq
    client = Groq(api_key=os.getenv('GROQ_KEY', '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'))
    try:
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": "Generate positive, engaging TikTok comments."},
                {"role": "user", "content": f"Generate exactly {num} short, varied comments for TikTok video about: {desc}. Natural, emoji-friendly."}
            ],
            max_tokens=300,
            temperature=0.7
        )
        comments = [line.strip() for line in response.choices[0].message.content.split('\n') if line.strip()]
        return comments[:num]
    except Exception as e:
        print(f"Groq error: {e}")
        return ["Great video! 🔥", "Love this! 👏", "Amazing! 😍"] * ((num // 3) + 1)
