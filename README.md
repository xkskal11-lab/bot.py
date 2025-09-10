import logging
import asyncio
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# حط التوكن مالك هنا
TOKEN = "8477570891:AAH8LtHYKN2_omZeYgAARAdOCNyYy3wa5FE"

logging.basicConfig(level=logging.INFO)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("ارسل", callback_data="send_link")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "مرحبٱ بك في بوت تنزيل من تيك توك بدون علامات مائية 🌹\n\nارسل رابطك الآن👇"
    await update.message.reply_text(text, reply_markup=reply_markup)

# الضغط على زر "ارسل"
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "send_link":
        await query.message.reply_text("✨ ارسل الرابط الآن 🔥")

# استقبال الرابط
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "tiktok.com" in url:
        countdown_msg = await update.message.reply_text("⏳ انتظر شوي جالس اجيبلك المقطع: 10")

        for i in range(9, -1, -1):
            await asyncio.sleep(1)
            try:
                await countdown_msg.edit_text(f"⏳ انتظر شوي جالس اجيبلك المقطع: {i}")
            except:
                pass

        # بعد العداد يجيب الفيديو
        try:
            api_url = "https://www.tikwm.com/api/"
            r = requests.post(api_url, data={"url": url}, timeout=15).json()

            if r.get("data") and "play" in r["data"]:
                video_url = r["data"]["play"]
                await update.message.reply_video(video_url, caption="✅ تفضل المقطع بدون علامة مائية 🎉")
            else:
                await update.message.reply_text("❌ ما قدرت اجيب الفيديو، جرب رابط ثاني 🙏")

        except Exception as e:
            await update.message.reply_text(f"⚠️ صار خطأ أثناء جلب الفيديو: {e}")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ البوت شغال ...")
    app.run_polling()

if __name__ == "__main__":
    main()
