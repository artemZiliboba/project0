import logging
import os

import telebot

from logger_setup import setup_logger
from nasa.gigachat import post_get_token, count_tokens, ask_chat
from nasa.nasa_api import fetch_nasa_apod

logger = setup_logger(__name__, log_level=logging.INFO)

TOKEN = os.getenv('TOKEN')

if not TOKEN:
    logger.error("TOKEN is not set. Please set the TOKEN environment variable.")
    raise ValueError("TOKEN is not set.")

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['version'])
def send_version(message):
    bot.reply_to(message, 'created by WIPEOFFS')
    logger.info(f"User {message.from_user.username} ({message.from_user.id}) sent: {message.text}")


@bot.message_handler(commands=['apod'])
def send_apod(message):
    logger.info(f"Received /apod command from {message.from_user.username} ({message.from_user.id})")

    # Пример: Получаем текущую дату
    date = message.text.split('/apod ')[-1] if len(message.text.split()) > 1 else None

    # Получаем данные с API NASA
    explanation, url, hdurl = fetch_nasa_apod(date)
    access_token, expires_at = post_get_token()
    content = ask_chat(access_token, "Переведи на русский - " + explanation)

    # Отправляем сообщение пользователю
    response = f"`{content}`\n\n[URL]({url})\n[HD URL]({hdurl})"
    bot.reply_to(message, response, parse_mode='Markdown')


@bot.message_handler(commands=['test'])
def send_version(message):
    access_token, expires_at = post_get_token()
    tokens_count, characters = count_tokens(access_token, "My some text")
    content = ask_chat(access_token, "Привет, как дела?")

    bot.reply_to(message, f'Token is: {access_token}, expire at: {expires_at}')
    bot.reply_to(message, f'Tokens count: {tokens_count}\nCharacters count: {characters}')
    bot.reply_to(message, f'Answer gigachat - {content}')
    logger.info(f"User {message.from_user.username} ({message.from_user.id}) sent: {message.text}")


@bot.message_handler(func=lambda message: True)
def log_message(message):
    logger.info(f"Received message from {message.from_user.username} ({message.from_user.id}): {message.text}")


if __name__ == '__main__':
    logger.info("Bot is starting...")
    bot.polling(none_stop=True)
