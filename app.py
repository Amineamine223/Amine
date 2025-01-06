import telebot
import requests
import json
from datetime import datetime, timedelta

API_TOKEN = '7882761814:AAH4pJL1PWj71_vLNRkLggK_wZ6ZS7xurIY'  # ضع هنا توكن البوت الخاص بك
bot = telebot.TeleBot(API_TOKEN)

# تحميل بيانات المستخدمين من ملف
def load_user_data():
    try:
        with open('user_data.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# حفظ بيانات المستخدمين إلى ملف
def save_user_data(user_data):
    with open('user_data.json', 'w') as f:
        json.dump(user_data, f)

# إخفاء رقم الهاتف
def hide_phone_number(msisdn):
    return msisdn[:4] + '****' + msisdn[8:]

@bot.message_handler(commands=['start'])
def handle_start(msg):
    chat_id = msg.chat.id
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton(text='📱 إرسال رقم الهاتف 📱', callback_data='send_number'))
    bot.send_message(chat_id, '👋 مرحبًا! الرجاء إرسال رقم هاتف Djezzy الخاص بك الذي يبدأ ب 07', reply_markup=markup)
    bot.send_message(chat_id, "✨ لا تنسى متابعة قناتنا الرسمية فقط 🌟: \n\n🔗 [تابعنا هنا](https://t.me/flexerchannel)")

@bot.callback_query_handler(func=lambda call: call.data == 'send_number')
def handle_send_number(callback_query):
    chat_id = callback_query.message.chat.id
    bot.send_message(chat_id, '📱 الرجاء إرسال رقم هاتفك Djezzy الذي يبدأ بالرقم 07:')
    bot.register_next_step_handler_by_chat_id(chat_id, handle_phone_number)

def handle_phone_number(msg):
    chat_id = msg.chat.id
    text = msg.text
    if text.startswith('07') and len(text) == 10:
        msisdn = '213' + text[1:]
        if send_otp(msisdn):
            bot.send_message(chat_id, '🔢 تم إرسال رمز OTP. الرجاء إدخال الرمز الذي تلقيته:')
            bot.register_next_step_handler_by_chat_id(chat_id, lambda msg: handle_otp(msg, msisdn))
        else:
            bot.send_message(chat_id, '⚠️ حدث خطأ عند إرسال رمز OTP. الرجاء المحاولة مرة أخرى.')
    else:
        bot.send_message(chat_id, '⚠️ الرجاء إدخال رقم صالح يبدأ ب 07 ويحتوي على 10 أرقام.')

def handle_otp(msg, msisdn):
    chat_id = msg.chat.id
    otp = msg.text
    tokens = verify_otp(msisdn, otp)
    if tokens:
        user_data = load_user_data()
        user_data[str(chat_id)] = {
            'username': msg.from_user.username,
            'telegram_id': chat_id,
            'msisdn': msisdn,
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'last_applied': None
        }
        save_user_data(user_data)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(text='🎁 تفعيل هدية Walkwin 🎁', callback_data='walkwingift'))
        bot.send_message(chat_id, '🎉 تم التحقق بنجاح! اختر الإجراء الذي تود القيام به:', reply_markup=markup)
        bot.send_message(chat_id, "✨ لا تنسى متابعة قناتنا الرسمية فقط 🌟: \n\n🔗 [تابعنا هنا](https://t.me/flexerchannel)")
    else:
        bot.send_message(chat_id, '⚠️ الرمز OTP غير صحيح. حاول مرة أخرى.')

@bot.callback_query_handler(func=lambda call: call.data == 'walkwingift')
def handle_walkwingift(callback_query):
    chat_id = callback_query.message.chat.id
    user_data = load_user_data()
    if str(chat_id) in user_data:
        user = user_data[str(chat_id)]
        apply_gift(chat_id, user['msisdn'], user['access_token'], user['username'], callback_query.from_user.first_name)

def apply_gift(chat_id, msisdn, access_token, username, name):
    user_data = load_user_data()
    last_applied = user_data.get(str(chat_id), {}).get('last_applied')
    if last_applied:
        last_applied_time = datetime.fromisoformat(last_applied)
        if datetime.now() - last_applied_time < timedelta(days=1):
            bot.send_message(chat_id, "⚠️ لا يمكنك استخدام الهدية الآن. الرجاء الانتظار حتى مرور 24 ساعة على آخر استخدام.")
            return False

    url = f'https://apim.djezzy.dz/djezzy-api/api/v1/subscribers/{msisdn}/subscription-product'
    gift_code = 'GIFTWALKWIN1GO'
    payload = {
        'data': {
            'id': 'GIFTWALKWIN',
            'type': 'products',
            'meta': {
                'services': {
                    'steps': 10000,
                    'code': gift_code,
                    'id': 'WALKWIN'
                }
            }
        }
    }
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Connection': 'Keep-Alive',
        'Content-Type': 'application/json; charset=utf-8',
        'Authorization': f'Bearer {access_token}'
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()
        if response_data['message'] == f"the subscription to the product {gift_code} successfully done":
            hidden_phone = hide_phone_number(msisdn)
            success_message = (
                f"🎉 تم تفعيل الهدية بنجاح: {gift_code}! استمتع بها.\n\n"
                f"📣 تفاصيل المستخدم:\n"
                f"👤 الاسم: {name}\n"
                f"🧑‍💻 المستخدم: @{username}\n"
                f"📞 الرقم: {hidden_phone}\n"
            )
            bot.send_message(chat_id, success_message)

            # إرسال الرسالة إلى المجموعة
            group_chat_id = "@flexerxdbot"  # معرف المجموعة
            bot.send_message(group_chat_id, success_message)

            bot.send_message(chat_id, "✨ لا تنسى متابعة قناتنا الرسمية فقط 🌟: \n\n🔗 [تابعنا هنا](https://t.me/flexerchannel)")
            
            user_data[str(chat_id)]['last_applied'] = datetime.now().isoformat()
            save_user_data(user_data)
            return True
        else:
            bot.send_message(chat_id, f"⚠️ حدث خطأ: {response_data.get('message', 'غير معروف')}")
            return False
    except requests.RequestException as error:
        print('Error applying gift:', error)
        bot.send_message(chat_id, "⚠️ حدث خطأ أثناء تطبيق الهدية.")
        return False

# إرسال OTP
def send_otp(msisdn):
    url = 'https://apim.djezzy.dz/oauth2/registration'
    payload = f'msisdn={msisdn}&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&scope=smsotp'
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Connection': 'close',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'no-cache'
    }
    try:
        response = requests.post(url, data=payload, headers=headers)
        print('Send OTP Response:', response.json())
        return True
    except requests.RequestException as error:
        print('Error sending OTP:', error)
        return False

# التحقق من OTP
def verify_otp(msisdn, otp):
    url = 'https://apim.djezzy.dz/oauth2/token'
    payload = f'otp={otp}&mobileNumber={msisdn}&scope=openid&client_id=6E6CwTkp8H1CyQxraPmcEJPQ7xka&client_secret=MVpXHW_ImuMsxKIwrJpoVVMHjRsa&grant_type=mobile'
    headers = {
        'User-Agent': 'Djezzy/2.6.7',
        'Connection': 'close',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'no-cache'
    }
    try:
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as error:
        print('Error verifying OTP:', error)
        return None

# تشغيل البوت
print('✅ البوت شغال...')
bot.polling()