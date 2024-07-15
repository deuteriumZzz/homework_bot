import os
import sys
import time
import logging
import requests
from dotenv import load_dotenv
from telebot import TeleBot
from exceptions import APIRequestError, APIResponseError
from http import HTTPStatus

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    tokens = {
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID
    }
    missing_tokens = [name for name, value in tokens.items() if not value]
    if missing_tokens:
        logging.critical(
            'Отсутствуют обязательные переменные окружения: '
            f'{", ".join(missing_tokens)}'
        )
    return not missing_tokens


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.debug('Сообщение успешно отправлено в Telegram')
    except Exception as error:
        logging.error(f'Сбой при отправке сообщения в Telegram: {error}')


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса."""
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if response.status_code != HTTPStatus.OK:
            raise APIRequestError(
                f'Ошибка при запросе к API: {response.status_code}'
            )
        return response.json()
    except requests.RequestException as error:
        logging.error(f'Ошибка при запросе к API: {error}')
        raise APIRequestError(f'Ошибка при запросе к API: {error}')


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        raise TypeError('Ответ API не является словарём')
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError('В ответе API отсутствуют ожидаемые ключи')
    if not isinstance(response['homeworks'], list):
        raise TypeError(
            'Неверный формат данных в ответе API: ожидается список'
        )
    return response['homeworks']


def parse_status(homework):
    """Извлекает статус работы из информации о домашней работе."""
    if 'homework_name' not in homework or 'status' not in homework:
        raise APIResponseError('В ответе API отсутствуют ожидаемые ключи')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_VERDICTS:
        raise APIResponseError('Недокументированный статус домашней работы')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы программы."""
    if not check_tokens():
        logging.critical('Отсутствуют обязательные переменные окружения')
        sys.exit(1)

    logging.basicConfig(
        level=logging.DEBUG,
        format=(
            '%(asctime)s - %(levelname)s - %(message)s - '
            '%(funcName)s - %(lineno)d'
        ),
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if homeworks:
                for homework in homeworks:
                    message = parse_status(homework)
                    send_message(bot, message)
            else:
                logging.debug('Отсутствие в ответе новых статусов')
            timestamp = response.get('current_date', timestamp)
        except (APIRequestError, APIResponseError) as error:
            logging.error(f'Сбой в работе программы: {error}')
            send_message(bot, f'Сбой в работе программы: {error}')
        except Exception as error:
            logging.error(f'Неизвестная ошибка: {error}')
            send_message(bot, f'Неизвестная ошибка: {error}')
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
