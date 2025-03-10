import requests
from bs4 import BeautifulSoup
import logging
import django
import os
import urllib3

# Отключаем предупреждения о небезопасных HTTPS-запросах (НЕ для продакшена!)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Настройка Django окружения
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "user_management.settings")
django.setup()

from sduNews.models import Journal

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_journals(url: str):
    try:
        response = requests.get(url, verify=False, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Ошибка запроса: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    journals_list = []

    journals_div = soup.find('div', class_='journals')
    if not journals_div:
        logger.error("Не удалось найти раздел с журналами.")
        return []

    for item in journals_div.find_all('li'):
        body_div = item.find('div', class_='body')
        if not body_div:
            continue

        title_tag = body_div.find('h3')
        title = title_tag.get_text(strip=True) if title_tag else ""

        a_tag = title_tag.find('a') if title_tag else None
        journal_url = a_tag.get('href', '') if a_tag else ""

        description_div = body_div.find('div', class_='description')
        description = description_div.get_text(strip=True) if description_div else ""

        thumb_div = item.find('div', class_='thumb')
        image_url = thumb_div.find('img')['src'] if thumb_div and thumb_div.find('img') else ""

        links_div = body_div.find('ul', class_='links')
        view_link = ""
        current_issue_link = ""

        if links_div:
            for li in links_div.find_all('li'):
                a_link = li.find('a')
                if a_link:
                    link_text = a_link.get_text(strip=True).lower()
                    if "view" in link_text:
                        view_link = a_link.get('href', '')
                    elif "current" in link_text:
                        current_issue_link = a_link.get('href', '')

        journals_list.append({
            'title': title,
            'journal_url': journal_url,
            'description': description,
            'image_url': image_url,
            'view_link': view_link,
            'current_issue_link': current_issue_link,
        })

    return journals_list

def save_to_db(journals):
    for journal in journals:
        obj, created = Journal.objects.update_or_create(
            journal_url=journal['journal_url'],  # Проверяем по URL, чтобы избежать дублирования
            defaults={
                'title': journal['title'],
                'description': journal['description'],
                'image_url': journal['image_url'],
                'view_link': journal['view_link'],
                'current_issue_link': journal['current_issue_link'],
            }
        )
        if created:
            logger.info(f"Добавлен новый журнал: {journal['title']}")
        else:
            logger.info(f"Обновлен журнал: {journal['title']}")

if __name__ == "__main__":
    url = "https://journals.sdu.edu.kz/"
    journals = parse_journals(url)
    if journals:
        save_to_db(journals)