
import json
import os

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters
)

# =========================
# BOT SOZLAMALARI
# =========================

TOKEN = "9073217554:AAEa8-GRm0CJ8_t1S5sNVM7C6F_6BJWG2rQ"

# BU YERGA O'Z TELEGRAM ID INGIZNI YOZING
ADMIN_IDS = {9245977814}

DB_FILE = "kinolar.json"

TITLE, PHOTO, VIDEO = range(3)


# =========================
# MA'LUMOTLAR
# =========================

def load_movies():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
    return []


movies = load_movies()


def save_movies():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(movies, f, ensure_ascii=False, indent=4)


def is_admin(update):
    return update.effective_user.id in ADMIN_IDS


# =========================
# MENYU
# =========================

def user_menu():
    return ReplyKeyboardMarkup(
        [
            ["🎬 Barcha kinolar"],
            ["🔍 Kino qidirish", "📸 Rasmlar"],
            ["ℹ️ Bot haqida"]
        ],
        resize_keyboard=True
    )


def admin_menu():
    return ReplyKeyboardMarkup(
        [
            ["➕ Kino qo'shish"],
            ["📚 Kinolar ro'yxati", "🗑 Kino o'chirish"],
            ["🎬 Barcha kinolar"],
            ["🔙 Asosiy menyu"]
        ],
        resize_keyboard=True
    )


# =========================
# START VA ID
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 KINO OLAMIGA XUSH KELIBSIZ!\n\n"
        "Bu yerda kinolar, rasmlar va videolar mavjud.\n\n"
        "Menyudan kerakli bo'limni tanlang.",
        reply_markup=admin_menu() if is_admin(update) else user_menu()
    )


async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🆔 Sizning Telegram ID'ingiz:\n\n"
        f"`{update.effective_user.id}`",
        parse_mode="Markdown"
    )


# =========================
# ADMIN PANEL
# =========================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    await update.message.reply_text(
        "👑 ADMIN PANEL\n\n"
        "Bu yerda botni boshqarishingiz mumkin.",
        reply_markup=admin_menu()
    )


# =========================
# KINO QO'SHISH
# =========================

async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return ConversationHandler.END

    await update.message.reply_text("🎬 Kino nomini yuboring:")
    return TITLE


async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text.strip()

    await update.message.reply_text(
        "📸 Endi kino rasmini yoki posterini yuboring:"
    )
    return PHOTO


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("Iltimos, rasm yuboring!")
        return PHOTO

    context.user_data["photo"] = update.message.photo[-1].file_id

    await update.message.reply_text(
        "🎥 Endi kino videosini yuboring:"
    )
    return VIDEO


async def get_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    video = update.message.video

    if not video and update.message.document:
        document = update.message.document
        if document.mime_type and document.mime_type.startswith("video/"):
            video = document

    if not video:
        await update.message.reply_text(
            "Iltimos, video yuboring yoki video faylni hujjat sifatida jo'nating!"
        )
        return VIDEO

    movie = {
        "title": context.user_data["title"],
        "photo": context.user_data["photo"],
        "video": video.file_id
    }

    movies.append(movie)
    save_movies()

    context.user_data.clear()

    await update.message.reply_text(
        "✅ KINO MUVAFFAQIYATLI QO'SHILDI!\n\n"
        f"🎬 {movie['title']}",
        reply_markup=admin_menu()
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "❌ Amal bekor qilindi.",
        reply_markup=admin_menu() if is_admin(update) else user_menu()
    )

    return ConversationHandler.END


# =========================
# KINOLAR RO'YXATI
# =========================

async def show_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not movies:
        await update.message.reply_text("Hozircha kinolar mavjud emas.")
        return

    keyboard = []

    for i, movie in enumerate(movies):
        keyboard.append([
            InlineKeyboardButton(
                "🎬 " + movie["title"],
                callback_data=f"movie_{i}"
            )
        ])

    await update.message.reply_text(
        "🎥 KINOLAR RO'YXATI:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================
# KINO OCHISH
# =========================

async def open_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        index = int(query.data.split("_")[1])
        movie = movies[index]
    except (ValueError, IndexError):
        await query.message.reply_text("❌ Kino topilmadi.")
        return

    await query.message.reply_photo(
        photo=movie["photo"],
        caption=f"🎬 {movie['title']}"
    )

    await query.message.reply_video(
        video=movie["video"],
        caption=f"▶️ {movie['title']}"
    )


# =========================
# KINO O'CHIRISH
# =========================

async def delete_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update):
        await update.message.reply_text("⛔ Siz admin emassiz!")
        return

    if not movies:
        await update.message.reply_text("O'chirish uchun kino yo'q.")
        return

    keyboard = []

    for i, movie in enumerate(movies):
        keyboard.append([
            InlineKeyboardButton(
                "🗑 " + movie["title"],
                callback_data=f"delete_{i}"
            )
        ])

    await update.message.reply_text(
        "Qaysi kinoni o'chirmoqchisiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def delete_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id not in ADMIN_IDS:
        await query.message.reply_text("⛔ Sizda ruxsat yo'q!")
        return

    try:
        index = int(query.data.split("_")[1])
        movie = movies.pop(index)
    except (ValueError, IndexError):
        await query.message.reply_text("Kino topilmadi.")
        return

    save_movies()

    await query.edit_message_text(
        f"✅ {movie['title']} o'chirildi!"
    )


# =========================
# RASMLAR
# =========================

async def show_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not movies:
        await update.message.reply_text("Rasmlar mavjud emas.")
        return

    for movie in movies:
        await update.message.reply_photo(
            photo=movie["photo"],
            caption=f"📸 {movie['title']}"
        )


# =========================
# QIDIRUV
# =========================

async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["searching"] = True
    await update.message.reply_text("🔍 Kino nomini yozing:")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "➕ Kino qo'shish":
        if is_admin(update):
            await update.message.reply_text("Kino qo'shish uchun /add yuboring.")
        else:
            await update.message.reply_text("⛔ Ruxsat yo'q!")
        return

    if text == "📚 Kinolar ro'yxati":
        if is_admin(update):
            await show_movies(update, context)
        else:
            await update.message.reply_text("⛔ Ruxsat yo'q!")
        return

    if text == "🗑 Kino o'chirish":
        await delete_menu(update, context)
        return

    if text == "🎬 Barcha kinolar":
        await show_movies(update, context)
        return

    if text == "🔍 Kino qidirish":
        await search_start(update, context)
        return

    if text == "📸 Rasmlar":
        await show_photos(update, context)
        return

    if text == "ℹ️ Bot haqida":
        await update.message.reply_text(
            "🎬 KINO BOT\n\n"
            "Kinolar, posterlar va videolar jamlangan."
        )
        return

    if text == "🔙 Asosiy menyu":
        await update.message.reply_text(
            "Asosiy menyu:",
            reply_markup=admin_menu() if is_admin(update) else user_menu()
        )
        return

    if context.user_data.get("searching"):
        context.user_data["searching"] = False

        results = [
            (i, m) for i, m in enumerate(movies)
            if text.lower() in m["title"].lower()
        ]

        if not results:
            await update.message.reply_text("❌ Kino topilmadi.")
            return

        keyboard = [
            [InlineKeyboardButton(
                "🎬 " + movie["title"],
                callback_data=f"movie_{i}"
            )]
            for i, movie in results
        ]

        await update.message.reply_text(
            "🔎 Qidiruv natijalari:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    await update.message.reply_text(
        "Kerakli bo'limni tanlang:",
        reply_markup=admin_menu() if is_admin(update) else user_menu()
    )


# =========================
# BOTNI ISHGA TUSHIRISH
# =========================

def main():
    app = Application.builder().token(TOKEN).build()

    conversation = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)
            ],
            PHOTO: [
                MessageHandler(filters.PHOTO, get_photo)
            ],
            VIDEO: [
                MessageHandler(
                    filters.VIDEO | filters.Document.VIDEO,
                    get_video
                )
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(conversation)
    app.add_handler(CommandHandler("cancel", cancel))

    app.add_handler(
        CallbackQueryHandler(delete_movie, pattern=r"^delete_\d+$")
    )
    app.add_handler(
        CallbackQueryHandler(open_movie, pattern=r"^movie_\d+$")
    )

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    print("KINO BOT ISHGA TUSHDI!")
    app.run_polling()


if __name__ == "__main__":
    main()
