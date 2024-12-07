import os
from datetime import datetime

import requests

from logger_setup import setup_logger

logger = setup_logger('nasa_api_logger')


def fetch_nasa_apod(date=None):
    logger.info("Starting get data from API NASA.")

    api_key = os.getenv('NASA_API_KEY', 'DEMO_KEY')
    if not api_key:
        logger.error("NASA_API_KEY is not set. Please set the NASA_API_KEY environment variable.")
        raise ValueError("NASA_API_KEY is not set. Please set the NASA_API_KEY environment variable.")

    # Использовать текущую дату, если дата не предоставлена
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    url = f'https://api.nasa.gov/planetary/apod?api_key={api_key}&date={date}'
    logger.info(f"Sending request to NASA API for date: {date}")

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        explanation = data.get('explanation')
        image_url = data.get('url')
        hd_image_url = data.get('hdurl')
        media_type = data.get('media_type')
        title = data.get('title')
        date = data.get('date')

        logger.info(f"Successfully retrieved data for date: {date}")
        return explanation, image_url, hd_image_url, media_type, title, date

    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred while requesting data: {e}")
        return f"An error occurred: {e}"
