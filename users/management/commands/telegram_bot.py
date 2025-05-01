import os
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from django.core.cache import cache
from users.models import User, Profile
from projects.models import Notification, Project
from asgiref.sync import sync_to_async
from dotenv import load_dotenv
from django.core.management.base import BaseCommand

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# --------- UTILS ---------
@sync_to_async
def get_user_profile(user):
    return user.profile

@sync_to_async
def get_user_by_id(user_id):
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return None



@sync_to_async
def get_user_by_chat_id(chat_id):
    try:
        return User.objects.filter(profile__telegram_chat_id=chat_id).first()
    except User.DoesNotExist:
        return None

@sync_to_async
def save_telegram_chat_id(user, chat_id):
    if hasattr(user, "profile"):
        user.profile.telegram_chat_id = chat_id
        user.profile.save()

# --------- COMMANDS ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        token = args[0]
        user_id = cache.get(f'tg_link_{token}')
        print(f"Trying to get user from token: tg_link_{token}, user_id: {user_id}")

        if user_id is not None:
            user = await get_user_by_id(user_id)
            if user is not None:
                await save_telegram_chat_id(user, update.message.chat_id)
                await update.message.reply_text("✅ Telegram успешно привязан к вашему аккаунту ScholarHub!")
            else:
                await update.message.reply_text("❌ Ошибка: пользователь не найден.")
        else:
            await update.message.reply_text("⚠️ Срок действия токена истек или токен недействителен.")
    else:
        await update.message.reply_text("👋 Привет! Для использования ScholarHub бота необходимо связать аккаунт через сайт.")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user_by_chat_id(update.message.chat_id)
    if not user:
        await update.message.reply_text("❌ Вы не привязали аккаунт ScholarHub.")
        return
    profile = await get_user_profile(user)

    await update.message.reply_text(
        f"👤 <b>Username:</b> {user.username}\n"
        f"📧 <b>Email:</b> {user.email}\n"
        f"🌍 <b>Country:</b> {profile.country or 'Not set'}",
        parse_mode='HTML'
    )

async def notifications(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user_by_chat_id(update.message.chat_id)
    if user:
        notes = await sync_to_async(list)(Notification.objects.filter(user=user).order_by('-created_at')[:5])
        if notes:
            text = "\n\n".join([f"🔔 {n.message}" for n in notes])
            await update.message.reply_text(text)
        else:
            await update.message.reply_text("🔔 Нет уведомлений.")
    else:
        await update.message.reply_text("❌ Профиль не найден.")

async def projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user_by_chat_id(update.message.chat_id)
    if user:
        projects = await sync_to_async(list)(Project.objects.filter(owner=user))
        if projects:
            text = "\n\n".join([f"📁 {p.title}" for p in projects])
            await update.message.reply_text(text)
        else:
            await update.message.reply_text("📂 У вас нет проектов.")
    else:
        await update.message.reply_text("❌ Профиль не найден.")

async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚙️ Изменить настройки можно на сайте:\n"
        "👉 https://scholarhub.kz/settings/"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 Список команд:\n"
        "/profile - Профиль\n"
        "/notifications - Последние уведомления\n"
        "/projects - Мои проекты\n"
        "/settings - Настройки\n"
        "/help - Помощь\n"
    )

# --------- SETUP MENU ---------
async def set_commands(application):
    await application.bot.set_my_commands([
        BotCommand("start", "Привязать аккаунт ScholarHub"),
        BotCommand("profile", "Показать профиль"),
        BotCommand("notifications", "Последние уведомления"),
        BotCommand("projects", "Мои проекты"),
        BotCommand("settings", "Изменить настройки"),
        BotCommand("help", "Помощь и команды"),
    ])

# --------- DJANGO COMMAND ---------
class Command(BaseCommand):
    help = "Запускает ScholarHub Telegram-бота"

    def handle(self, *args, **options):
        if not TELEGRAM_BOT_TOKEN:
            self.stdout.write(self.style.ERROR('TELEGRAM_BOT_TOKEN не найден в env!'))
            return

        app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("profile", profile))
        app.add_handler(CommandHandler("notifications", notifications))
        app.add_handler(CommandHandler("projects", projects))
        app.add_handler(CommandHandler("settings", settings))
        app.add_handler(CommandHandler("help", help_command))

        app.post_init = set_commands  # 👈 Добавляем меню после запуска

        self.stdout.write(self.style.SUCCESS("✅ Telegram бот успешно запущен."))
        app.run_polling()
