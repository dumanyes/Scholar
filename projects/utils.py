from projects.models import Notification
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import os
import requests

def send_telegram_message(chat_id, text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

def send_notification(user, message, link=None):
    profile = getattr(user, 'profile', None)
    if not profile:
        return
    Notification.objects.create(
        user=user,
        message=message,
        link=link or "",
    )
    if profile.email_notifications:
        subject = "🚀 ScholarHub | You've Got a New Update!"

        text_content = f"""
Hello {user.get_full_name() or user.username},

🔔 You have a new update on ScholarHub!

{message}

👉 View it here: {link or 'Login to ScholarHub'}

---

Сәлем, {user.get_full_name() or user.username},

🔔 ScholarHub платформасында сізге жаңа жаңарту бар!

{message}

👉 Мұнда көре аласыз: {link or 'ScholarHub жүйесіне кіріңіз'}

---

Здравствуйте, {user.get_full_name() or user.username},

🔔 У вас новое обновление на платформе ScholarHub!

{message}

👉 Посмотреть можно здесь: {link or 'Войдите в ScholarHub'}

Thank you for being with us!
        """

        html_content = render_to_string('emails/notification_email.html', {
            'user': user,
            'message': message,
            'link': link or 'https://scholarhub.kz/',
        })

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=True)
    if profile.telegram_chat_id:
        full_message = f"🔔 {message}\n\n👉 <a href='https://scholarhub.kz{link}'>View</a>" if link else f"🔔 {message}"
        send_telegram_message(profile.telegram_chat_id, full_message)
