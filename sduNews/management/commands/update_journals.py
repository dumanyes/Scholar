from django.core.management.base import BaseCommand
from sduNews.models import Journal
from save_to_db import parse_journals, save_to_db  # Импортируем функции напрямую
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = "Ежедневное обновление журналов: удаляет старые записи и парсит новые данные"

    def handle(self, *args, **kwargs):
        # Очистка таблицы Journal
        Journal.objects.all().delete()
        logger.info("Удалены все старые записи Journal.")

        # URL для парсинга
        url = "https://journals.sdu.edu.kz/"
        journals = parse_journals(url)

        if journals:
            save_to_db(journals)
            logger.info("Журналы успешно обновлены.")
        else:
            logger.error("Не удалось получить данные с сайта.")
