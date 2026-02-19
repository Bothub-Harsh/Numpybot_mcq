import json
import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)
from config import TOKEN

user_sessions = {}

# ----------------------------
# Load Questions
# ----------------------------
def load_questions(set_number):
    with open(f"questions/set{set_number}.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    random.shuffle(questions)
    return questions


# ----------------------------
# Save Score
# ----------------------------
def save_score(user_id, set_number, score):
    try:
        with open("database/user_data.json", "r") as f:
            data = json.load(f)
    except:
        data = {}

    if str(user_id) not in data:
        data[str(user_id)] = {}

    data[str(user_id)][f"set{set_number}"] = score

    with open("database/user_data.json", "w") as f:
        json.dump(data, f, indent=4)


# ----------------------------
# /start Command
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Set 1", callback_data="set_1")],
        [InlineKeyboardButton("Set 2", callback_data="set_2")],
        [InlineKeyboardButton("Set 3", callback_data="set_3")],
        [InlineKeyboardButton("Set 4", callback_data="set_4")],
        [InlineKeyboardButton("Set 5", callback_data="set_5")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📚 Choose a NumPy Practice Set:",
        reply_markup=reply_markup
    )


# ----------------------------
# Handle Set Selection
# ----------------------------
async def handle_set(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    set_number = int(query.data.split("_")[1])

    questions = load_questions(set_number)

    user_sessions[user_id] = {
        "set": set_number,
        "questions": questions[:10],  # only 10 questions per quiz
        "current": 0,
        "score": 0
    }

    await send_question(query)


# ----------------------------
# Send Question
# ----------------------------
async def send_question(query):
    user_id = query.from_user.id
    session = user_sessions[user_id]

    q = session["questions"][session["current"]]

    keyboard = []
    for i, option in enumerate(q["options"]):
        keyboard.append(
            [InlineKeyboardButton(option, callback_data=f"ans_{i}")]
        )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Q{session['current'] + 1}: {q['question']}",
        reply_markup=reply_markup
    )


# ----------------------------
# Handle Answer
# ----------------------------
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    session = user_sessions[user_id]

    selected = int(query.data.split("_")[1])
    correct = session["questions"][session["current"]]["answer"]

    if selected == correct:
        session["score"] += 1

    session["current"] += 1

    if session["current"] >= 10:
        score = session["score"]
        set_number = session["set"]

        save_score(user_id, set_number, score)

        await query.edit_message_text(
            f"✅ Quiz Finished!\n\n"
            f"📊 Your Score: {score}/10\n\n"
            f"Use /start to try another set."
        )
    else:
        await send_question(query)


# ----------------------------
# MAIN APP
# ----------------------------
PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_set, pattern="^set_"))
    app.add_handler(CallbackQueryHandler(handle_answer, pattern="^ans_"))

    print("Bot running on Render...")

    app.run_polling()

