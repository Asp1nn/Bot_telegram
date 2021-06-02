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


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    if homework['status'] == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework['status'] == 'reviewing':
        verdict = 'Ревьюер взял работу на проверку.'
    else:
        verdict = 'Ревьюеру всё понравилось, можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    date = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            PRAKTIKUM_URL,
            headers=headers,
            params=date
        )
        return homework_statuses.json()
    except requests.RequestException as e:
        logging.error(e, exc_info=True)


def send_message(message, bot_client):
    return bot_client.send_message(CHAT_ID, message)


def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    logging.basicConfig(
        level=logging.DEBUG,
        filemode='w',
        filename='bot.log',
        format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    )

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                message = parse_homework_status(new_homework.get('homeworks')[0])
                send_message(message, bot)
                send_message(parse_homework_status(new_homework.get('homeworks')[0]), bot)
                logging.info(f'Сообщение отправлено:\n«{message}»')
            current_timestamp = new_homework.get('current_date', current_timestamp)
            time.sleep(1200)

        except Exception as e:
            message = f'Бот столкнулся с ошибкой: {e}'
            logging.error(message, exc_info=True)
            time.sleep(1200)


if __name__ == '__main__':
    main()
