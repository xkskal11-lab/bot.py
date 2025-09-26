import telebot
from telebot import types
import random
import time

TOKEN = "8352035006:AAECUhFBsvSnwb9X_EPrIZPNgmiWHKpKyek"
DEVELOPER = "PXU_12"
bot = telebot.TeleBot(TOKEN)

# 🔹 بيانات الروليت
roulettes = {}
chat_locked = {}
muted_users = {}
banned_users = {}
global_banned_messages = set()

# ===== حماية من توقف البوت =====
def safe_handler(func):
    def wrapper(message):
        try:
            func(message)
        except Exception as e:
            print(f"خطأ في الهاندلر: {e}")
    return wrapper

# ===== لعبة الروليت =====
@bot.message_handler(func=lambda m: m.text and m.text.lower().startswith("روليت"))
@safe_handler
def start_roulette(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    # تحقق إذا يوجد روليت شغال
    if chat_id in roulettes:
        bot.reply_to(message, "⚠️ يوجد روليت شغال. ارسل 'انهاء الروليت' لبدء جديد.")
        return

    # تحقق مشرف
    member = bot.get_chat_member(chat_id, user_id)
    if member.status not in ["administrator", "creator"]:
        bot.reply_to(message, "❌ فقط المشرفين والمالك يقدرون يسوون روليت.")
        return

    try:
        num_winners = int(message.text.split()[1])
    except:
        bot.reply_to(message, "❌ اكتب الرقم بعد كلمة روليت.")
        return

    # تهيئة بيانات اللعبة
    roulette = {
        "owner": user_id,
        "players": [],
        "num_winners": num_winners,
        "msg_id": None
    }

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("مشاركة", callback_data=f"join_{chat_id}"))
    markup.add(types.InlineKeyboardButton("بدء اللعبة", callback_data=f"start_{chat_id}"))

    text = f"""• مرحباً بكم في لعبة الروليت 👑

- يمكنكم التسجيل فيها عن طريق ضغط زر مشاركة

• عدد اللاعبين : 0
-"""
    msg = bot.send_message(chat_id, text, reply_markup=markup)
    roulette["msg_id"] = msg.message_id
    roulettes[chat_id] = roulette

# انضمام للعبة
@bot.callback_query_handler(func=lambda call: call.data.startswith("join_"))
def join_roulette(call):
    chat_id = int(call.data.split("_")[1])
    if chat_id not in roulettes:
        bot.answer_callback_query(call.id, "🚫 لا يوجد لعبة حالياً.", show_alert=True)
        return

    roulette = roulettes[chat_id]
    user_id = call.from_user.id

    if user_id in roulette["players"]:
        bot.answer_callback_query(call.id, "✅ انت مشارك بالفعل.", show_alert=True)
        return

    roulette["players"].append(user_id)
    bot.answer_callback_query(call.id, "تم انضمامك للروليت✅", show_alert=True)

    text = f"""• مرحباً بكم في لعبة الروليت 👑

- يمكنكم التسجيل فيها عن طريق ضغط زر مشاركة

• عدد اللاعبين : {len(roulette['players'])}
-"""
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("مشاركة", callback_data=f"join_{chat_id}"))
    markup.add(types.InlineKeyboardButton("بدء اللعبة", callback_data=f"start_{chat_id}"))
    bot.edit_message_text(text, chat_id, roulette["msg_id"], reply_markup=markup)

# بدء اللعبة
@bot.callback_query_handler(func=lambda call: call.data.startswith("start_"))
def start_game(call):
    chat_id = int(call.data.split("_")[1])
    if chat_id not in roulettes: return

    roulette = roulettes[chat_id]
    user_id = call.from_user.id

    if user_id != roulette["owner"]:
        bot.answer_callback_query(call.id, "❌ فقط من أنشأ اللعبة يقدر يبدأها.", show_alert=True)
        return

    if len(roulette["players"]) < roulette["num_winners"]:
        bot.answer_callback_query(call.id, "⚠️ عدد المشاركين أقل من عدد الفائزين.", show_alert=True)
        return

    winners = random.sample(roulette["players"], roulette["num_winners"])
    try:
        bot.delete_message(chat_id, roulette["msg_id"])
    except: pass

    text = "• الفائز في لعبة الروليت 🥳:\n\n"
    for i, w_id in enumerate(winners, 1):
        user = bot.get_chat_member(chat_id, w_id).user
        text += f"{i}- [{user.first_name}](tg://user?id={user.id})\n"

    bot.send_message(chat_id, text, parse_mode="Markdown")
    del roulettes[chat_id]

# انهاء الروليت
@bot.message_handler(func=lambda m: m.text.lower() == "انهاء الروليت")
@safe_handler
def end_roulette(message):
    chat_id = message.chat.id
    if chat_id in roulettes:
        try: bot.delete_message(chat_id, roulettes[chat_id]["msg_id"])
        except: pass
        del roulettes[chat_id]
        bot.reply_to(message, "تم إنهاء لعبة الروليت ✅")
    else:
        bot.reply_to(message, "🚫 لا يوجد لعبة حالياً.")

# ===== أوامر الإدارة =====
def restrict_user(chat_id, user_id, can_send=True):
    bot.restrict_chat_member(chat_id, user_id,
        can_send_messages=can_send,
        can_send_media_messages=can_send,
        can_send_other_messages=can_send,
        can_add_web_page_previews=can_send)

@bot.message_handler(func=lambda m: m.reply_to_message and m.text.lower() == "كتم")
@safe_handler
def mute_user(message):
    chat_id = message.chat.id
    if not is_admin(message): return
    user_id = message.reply_to_message.from_user.id
    if muted_users.get(user_id):
        bot.reply_to(message, "⚠️ العضو مكتوم بالفعل.")
        return
    restrict_user(chat_id, user_id, can_send=False)
    muted_users[user_id] = True
    bot.reply_to(message, f"🔇 تم كتم {message.reply_to_message.from_user.first_name} نهائياً.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text.lower() == "الغاء الكتم")
@safe_handler
def unmute_user(message):
    chat_id = message.chat.id
    if not is_admin(message): return
    user_id = message.reply_to_message.from_user.id
    if not muted_users.get(user_id):
        bot.reply_to(message, "⚠️ العضو ليس مكتوم.")
        return
    restrict_user(chat_id, user_id, can_send=True)
    del muted_users[user_id]
    bot.reply_to(message, f"✅ تم الغاء كتم {message.reply_to_message.from_user.first_name}.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text.lower() == "حظر")
@safe_handler
def ban_user(message):
    chat_id = message.chat.id
    if not is_admin(message): return
    user_id = message.reply_to_message.from_user.id
    if banned_users.get(user_id):
        bot.reply_to(message, "⚠️ العضو محظور بالفعل.")
        return
    bot.ban_chat_member(chat_id, user_id)
    banned_users[user_id] = True
    bot.reply_to(message, f"🚫 تم حظر {message.reply_to_message.from_user.first_name}.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.text.lower() == "الغاء الحظر")
@safe_handler
def unban_user(message):
    chat_id = message.chat.id
    if not is_admin(message): return
    user_id = message.reply_to_message.from_user.id
    if not banned_users.get(user_id):
        bot.reply_to(message, "⚠️ العضو ليس محظور.")
        return
    bot.unban_chat_member(chat_id, user_id)
    del banned_users[user_id]
    bot.reply_to(message, f"✅ تم الغاء الحظر {message.reply_to_message.from_user.first_name}.")

# ===== قفل وفتح الشات =====
@bot.message_handler(func=lambda m: m.text.lower() == "قفل الشات")
@safe_handler
def lock_chat(message):
    chat_id = message.chat.id
    if not is_admin(message): return
    if chat_locked.get(chat_id):
        bot.reply_to(message, "⚠️ الشات مقفول بالفعل.")
        return
    bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=False))
    chat_locked[chat_id] = True
    bot.reply_to(message, "🔒 تم قفل الشات.")

@bot.message_handler(func=lambda m: m.text.lower() == "فتح الشات")
@safe_handler
def unlock_chat(message):
    chat_id = message.chat.id
    if not is_admin(message): return
    if not chat_locked.get(chat_id):
        bot.reply_to(message, "⚠️ الشات مفتوح بالفعل.")
        return
    bot.set_chat_permissions(chat_id, types.ChatPermissions(can_send_messages=True,
        can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True))
    chat_locked[chat_id] = False
    bot.reply_to(message, "🔓 تم فتح الشات.")

# ===== منع عام (للمطور فقط) =====
@bot.message_handler(func=lambda m: m.reply_to_message and m.text.lower() == "منع عام")
@safe_handler
def global_ban(message):
    if message.from_user.username != DEVELOPER: return
    target = message.reply_to_message
    if target.text: global_banned_messages.add(target.text.strip())
    elif target.sticker: global_banned_messages.add(target.sticker.file_unique_id)
    bot.reply_to(message, "✅ تم إضافة الرسالة/ملصق للمنع العام.")

@bot.message_handler(content_types=["text","sticker"])
@safe_handler
def filter_global(message):
    if message.text and message.text.strip() in global_banned_messages:
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "🚫 تم منع هذه الرسالة من قبل المطور.")
    elif message.sticker and message.sticker.file_unique_id in global_banned_messages:
        bot.delete_message(message.chat.id, message.message_id)
        bot.send_message(message.chat.id, "🚫 تم منع هذه الرسالة من قبل المطور.")

# ===== التحقق من المشرف =====
def is_admin(message):
    try:
        member = bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in ["administrator", "creator"]
    except: return False

# ===== الحلقة الرئيسية + حماية إعادة التشغيل =====
while True:
    try:
        print("🚀 البوت شغال...")
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        time.sleep(5)
