import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
from telegram.constants import ParseMode

# ================= CONFIG =================

TOKEN = os.environ.get("TOKEN")
GROUP_ID = int(os.environ.get("GROUP_ID"))

START_DATE = datetime(2026, 5, 1)
EXAM_DATE = datetime(2027, 1, 20)

DATA_FILE = "data.json"

# Replace with real Telegram IDs
USER_NAMES = {
    "PIYUSH_ID": "Piyush",
    "YOG_ID": "Yog"
}

# ================= STATES =================

MATH, PHYSICS, CHEMISTRY, HOURS, QUESTIONS = range(5)

# ================= DATA =================

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# ================= CORE =================

def calc_score(hours, questions):
    try:
        return int(float(hours) * 10 + int(questions) * 0.5)
    except:
        return 0

def get_name(user_id):
    return USER_NAMES.get(str(user_id), f"User {user_id}")

def update_user(user_id, score):
    data = load_data()
    user_id = str(user_id)
    today = str(datetime.now().date())

    if user_id not in data:
        data[user_id] = {
            "streak": 1,
            "last": today,
            "score": score,
            "total_days": 1
        }
    else:
        if data[user_id]["last"] != today:
            data[user_id]["streak"] += 1
            data[user_id]["total_days"] += 1
            data[user_id]["last"] = today

        data[user_id]["score"] = score

    save_data(data)
    return data[user_id]

# ================= BOT FLOW =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("What did you do in Mathematics today?")
    return MATH

async def maths(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["math"] = update.message.text
    await update.message.reply_text("What did you do in Physics today?")
    return PHYSICS

async def physics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["physics"] = update.message.text
    await update.message.reply_text("What did you do in Chemistry today?")
    return CHEMISTRY

async def chemistry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["chemistry"] = update.message.text
    await update.message.reply_text("Hours studied?")
    return HOURS

async def hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["hours"] = update.message.text
    await update.message.reply_text("Questions solved?")
    return QUESTIONS

async def questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    hours = context.user_data["hours"]
    questions = update.message.text

    score = calc_score(hours, questions)
    stats = update_user(user_id, score)

    today = datetime.now()
    day_number = (today - START_DATE).days + 1
    days_remaining = (EXAM_DATE - today).days

    msg = f"""**DAILY REPORT**

**Date:** {today.strftime('%d %B %Y')}

**User:** {get_name(user_id)}

**Day:** {day_number}
**Days Remaining:** {days_remaining}

**Mathematics:** {context.user_data['math']}
**Physics:** {context.user_data['physics']}
**Chemistry:** {context.user_data['chemistry']}

**Hours:** {hours}
**Questions:** {questions}

**Score:** {stats['score']}
**Streak:** {stats['streak']}
"""

    await context.bot.send_message(
        chat_id=GROUP_ID,
        text=msg,
        parse_mode=ParseMode.MARKDOWN
    )

    await update.message.reply_text("Posted successfully")
    return ConversationHandler.END

# ================= LEADERBOARD =================

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()

    board = []
    for uid, stats in data.items():
        board.append((stats["score"], stats["streak"], uid))

    board.sort(reverse=True)

    msg = "**LEADERBOARD**\n\n"

    for i, (score, streak, uid) in enumerate(board, start=1):
        msg += f"**{i}. {get_name(uid)}**\n"
        msg += f"Score: {score}\n"
        msg += f"Streak: {streak}\n\n"

    await update.message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)

# ================= INACTIVITY =================

async def inactivity_check(app):
    data = load_data()
    today = str(datetime.now().date())

    msg = "**INACTIVITY REPORT**\n\n"
    found = False

    for uid, stats in data.items():
        if stats.get("last") != today:
            found = True
            msg += f"**{get_name(uid)} missed today's update**\n"

    if found:
        await app.bot.send_message(GROUP_ID, msg, parse_mode=ParseMode.MARKDOWN)

# ================= DAILY WINNER =================

async def daily_winner(app):
    data = load_data()

    if not data:
        return

    winner = max(data.items(), key=lambda x: x[1]["score"])
    uid, stats = winner

    msg = f"""**DAILY WINNER**

**{get_name(uid)}**
Score: {stats['score']}

Consistency matters. Competitive system active.
"""

    await app.bot.send_message(GROUP_ID, msg, parse_mode=ParseMode.MARKDOWN)

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MATH: [MessageHandler(filters.TEXT, maths)],
            PHYSICS: [MessageHandler(filters.TEXT, physics)],
            CHEMISTRY: [MessageHandler(filters.TEXT, chemistry)],
            HOURS: [MessageHandler(filters.TEXT, hours)],
            QUESTIONS: [MessageHandler(filters.TEXT, questions)],
        },
        fallbacks=[],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("leaderboard", leaderboard))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
