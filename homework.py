import os
import time
import logging
from json import JSONDecodeError

import requests
from dotenv import load_dotenv
from requests.exceptions import Timeout, SSLError, ConnectionError
from requests.exceptions import RequestException
from telegram import Bot

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
STATUS_DATA = {'rejected': 'К сожалению в работе нашлись ошибки.',
               'reviewing': 'Ревьюер взял работу на проверку.',
               'approved': ('Ревьюеру всё понравилось, ' 
                            'можно приступать к следующему уроку.')}
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    status = homework['status']
    if status not in STATUS_DATA:
        raise ValueError(f'Несуществующий статус проекта - {status}')
    verdict = STATUS_DATA[status]
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    date = {'from_date': current_timestamp}
    try:
        response = requests.get(
            PRAKTIKUM_URL,
            headers=HEADERS,
            params=date
        )
    except (Timeout, SSLError, ConnectionError, OSError,
            RequestException, JSONDecodeError):
        raise
    return response.json()


def send_message(message, bot_client):
    return bot_client.send_message(CHAT_ID, message)


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                message = parse_homework_status(
                    new_homework.get('homeworks')[0]
                )
                send_message(message, bot)
                logging.info(f'Сообщение отправлено:\n«{message}»')
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(1200)

        except Exception as error:
            logging.error(f'Бот столкнулся с ошибкой: {error}', exc_info=True)
            time.sleep(1200)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filemode='w',
        filename=__file__ + '.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    main()
