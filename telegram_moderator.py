import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from toxiguard_engine import analyze_and_log

# ==========================================================
# PASTE YOUR @BotFather TOKEN BELOW
# ==========================================================
BOT_TOKEN = "PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE"

logging.basicConfig(level=logging.INFO)


async def moderate_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text
    sender = update.message.from_user.first_name or "Member"
    chat_title = update.effective_chat.title or "Telegram Group"

    result = analyze_and_log(
        text=text,
        platform=f"Telegram ({chat_title})",
        author=sender,
    )

    if result["is_toxic"]:
        try:
            # Automatically deletes/hides the toxic comment for ALL group members
            await update.message.delete()

            flagged_str = ", ".join(c.replace("_", " ").title() for c in result["flagged_categories"])
            scores_str = " | ".join(
                f"{c}: {result['scores'][c]*100:.0f}%" for c in result["flagged_categories"]
            )

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=(
                    f"🛡️ *ToxiGuard Auto-Moderation*\n"
                    f"👤 *User:* {sender}\n"
                    f"🚫 *Detected:* `{flagged_str}` ({scores_str})\n"
                    f"_Comment was automatically hidden from all group members._"
                ),
                parse_mode="Markdown",
            )
            print(f"🚫 [HIDDEN] {sender}: '{text}' -> {result['flagged_categories']}")
        except Exception as e:
            print(f"[ERROR] Could not delete message. Make sure bot is Admin with 'Delete Messages' enabled! ({e})")
    else:
        print(f"✅ [ALLOWED] {sender}: '{text}'")


if __name__ == "__main__":
    if BOT_TOKEN == "PASTE_YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("❌ Paste your @BotFather token into telegram_moderator.py first!")
        exit(1)

    print("🚀 ToxiGuard Telegram Live Moderator is running...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), moderate_group_message))
    app.run_polling()