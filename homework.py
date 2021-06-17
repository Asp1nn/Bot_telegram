import os
import time
import logging

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()


PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
PRAKTIKUM_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
STATUS_VERDICTS = {'rejected': 'К сожалению в работе нашлись ошибки.',
                   'reviewing': 'Ревьюер взял работу на проверку.',
                   'approved': 'Ревьюеру всё понравилось, '
                               'можно приступать к следующему уроку.'}
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
UNKNOWN_STATUS = 'Неизвестный статус проекта - {key}'
STATUS_PROJECT = 'У вас проверили работу "{name}"!\n\n{verdict}'
LOGGING_INFO = 'Сообщение отправлено:\n«{message}»'
LOGGING_ERROR = 'Бот столкнулся с ошибкой: {error}'
NETWORK_FAILURE = ('Произошел сбой сети в {key}, '
                   'параметры запроса {params}, '
                   'запрос по урлу: {url}, '
                   'заголовок: {headers}')
ERROR_MESSAGE_TEMPLATE = ('Ошибка сервера {key}: {error}, '
                          'параметры запроса {params}, '
                          'запрос по урлу: {url}, '
                          'заголовок: {headers}')


def parse_homework_status(homework):
    status = homework['status']
    if status not in STATUS_VERDICTS:
        raise ValueError(UNKNOWN_STATUS.format(key=status))
    return STATUS_PROJECT.format(
        name=homework['homework_name'],
        verdict=STATUS_VERDICTS[status]
    )


def get_homework_statuses(current_timestamp):
    date = {'from_date': current_timestamp}
    try:
        response = requests.get(
            PRAKTIKUM_URL,
            headers=HEADERS,
            params=date
        )
    except requests.RequestException as error:
        raise ConnectionError(NETWORK_FAILURE.format(
            key=error,
            url=PRAKTIKUM_URL,
            headers=HEADERS,
            params=date
        ))
    response_json = response.json()
    for key in ('error', 'code'):
        if key in response_json:
            raise RuntimeError(ERROR_MESSAGE_TEMPLATE.format(
                key=key,
                error=response_json[key],
                params=date,
                url=PRAKTIKUM_URL,
                headers=HEADERS
            ))
    return response_json


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
                logging.info(LOGGING_INFO.format(message=message))
            current_timestamp = new_homework.get(
                'current_date',
                current_timestamp
            )
            time.sleep(1200)

        except Exception as error:
            logging.error(LOGGING_ERROR.format(error=error), exc_info=True)
            time.sleep(1200)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.DEBUG,
        filemode='w',
        filename=__file__ + '.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )
    main()
