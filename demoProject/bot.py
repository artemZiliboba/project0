import logging
import os

import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

from logger_setup import setup_logger
from nasa.gigachat import post_get_token, count_tokens, ask_chat
from nasa.nasa_api import fetch_nasa_apod

EMPTY_NEWS = "Новость не найдена!"

logger = setup_logger(__name__, log_level=logging.INFO)

TOKEN = os.getenv('TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

if not TOKEN:
    logger.error("TOKEN is not set. Please set the TOKEN environment variable.")
    raise ValueError("TOKEN is not set.")

bot = telebot.TeleBot(TOKEN)
storage = {}


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

    # Получаем данные из GigaChat
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


# Example: /publish 2022-02-28
@bot.message_handler(commands=['publish'])
def publish_to_channel(message):
    try:
        date = message.text.split('/publish ')[-1] if len(message.text.split()) > 1 else None
        explanation, url, hdurl, media_type, title, date = fetch_nasa_apod(date)

        # Переводим в GigaChat
        access_token, expires_at = post_get_token()
        content = ask_chat(access_token, "Переведи на русский - " + explanation)

        response = f"*📷 {date} - {title}*\n\n{content}\n\n[URL]({url})\n[HD URL]({hdurl})"

        # Сохраняем все данные в хранилище
        storage[message.chat.id] = {
            "response": response,
            "photo_url": url,
        }

        # Создаем инлайн-кнопку
        markup = InlineKeyboardMarkup()
        publish_button = InlineKeyboardButton("✅ Опубликовать", callback_data="publish_news")
        decline_button = InlineKeyboardButton("❌ Удалить", callback_data="decline_news")
        markup.add(publish_button, decline_button)

        bot.send_photo(message.chat.id, url, caption=response, parse_mode='Markdown', reply_markup=markup)
    except Exception as e:
        bot.reply_to(message, "Failed to publish message to channel.")
        logger.error(f"Failed to publish message to channel {CHANNEL_ID}: {e}")


# Обработчик нажатий на инлайн-кнопки
@bot.callback_query_handler(func=lambda call: call.data == "publish_news")
def handle_publish_news(call):
    try:
        # Получаем сохраненные данные из хранилища
        data = storage.pop(call.message.chat.id, None)

        if data:
            # Публикуем фото с описанием в канал
            bot.send_photo(
                CHANNEL_ID,
                data["photo_url"],
                caption=data["response"],
                parse_mode='Markdown'
            )
            bot.answer_callback_query(call.id, "Новость опубликована в канал!")
            logger.info(f"Новость опубликована в канал {CHANNEL_ID} кнопкой 'Опубликовать'.")
        else:
            bot.answer_callback_query(call.id, "Новость не найдена!")
            logger.warning(f"Нет данных для публикации для чата {call.message.chat.id}.")

    except Exception as e:
        bot.answer_callback_query(call.id, "Произошла ошибка при публикации.")
        logger.error(f"Failed to publish news to channel {CHANNEL_ID}: {e}")


# Обработчик нажатия на кнопку "Не публиковать"
@bot.callback_query_handler(func=lambda call: call.data == "decline_news")
def handle_decline_news(call):
    try:
        # Удаляем новость из хранилища (если нужно)
        storage.pop(call.message.chat.id, None)

        # Отвечаем пользователю
        bot.answer_callback_query(call.id, "Новость не опубликована.")
        bot.send_message(call.message.chat.id, "Новость была отклонена и не опубликована.")
        logger.info(f"News declined by {call.from_user.username} ({call.from_user.id})")

    except Exception as e:
        bot.answer_callback_query(call.id, "Произошла ошибка при отклонении новости.")
        logger.error(f"Failed to decline news: {e}")


@bot.message_handler(func=lambda message: True)
def log_message(message):
    logger.info(f"Received message from {message.from_user.username} ({message.from_user.id}): {message.text}")


if __name__ == '__main__':
    logger.info("Bot is starting...")
    bot.polling(none_stop=True)
