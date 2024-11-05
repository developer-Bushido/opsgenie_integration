# opsgenie_module.py

import os
import requests
import calendar
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv('API_KEY')
SCHEDULE_ID = os.getenv('SCHEDULE_ID')

if not API_KEY or not SCHEDULE_ID:
    raise ValueError("Environment variables API_KEY and SCHEDULE_ID must be set.")

BASE_URL = 'https://api.opsgenie.com/v2/schedules'

def get_on_call_schedule(year, month):
    try:
        month_start = datetime(year, month, 1)
        _, num_days = calendar.monthrange(year, month)
        month_end = datetime(year, month, num_days, 23, 59, 59, 999999)

        start_date = month_start - timedelta(days=7)
        total_days = (month_end - start_date).days + 1
        interval = total_days
        interval_unit = 'days'

        params = {
            'date': start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
            'interval': interval,
            'intervalUnit': interval_unit
        }
        headers = {
            'Authorization': f'GenieKey {API_KEY}'
        }
        url = f'{BASE_URL}/{SCHEDULE_ID}/timeline'

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 422:
            raise ValueError(f"Некорректный временной диапазон. Дата должна быть не ранее 1 года назад и не позднее 2 лет в будущем. Запрошено для {year}-{month}.")
        elif response.status_code != 200:
            raise Exception(f"Error fetching data: {response.status_code} - {response.text}")

        data = response.json()
        rotations = data.get('data', {}).get('finalTimeline', {}).get('rotations', [])
        if not rotations:
            return []

        periods = rotations[0].get('periods', [])
        if not periods:
            return []

        filtered_periods = [
            period for period in periods
            if datetime.fromisoformat(period['endDate'][:-1]) >= month_start and datetime.fromisoformat(period['startDate'][:-1]) <= month_end
        ]

        return filtered_periods

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Ошибка сети или сервера: {e}")
    except Exception as e:
        raise RuntimeError(f"Непредвиденная ошибка: {e}")