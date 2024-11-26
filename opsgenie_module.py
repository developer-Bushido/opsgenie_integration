# opsgenie_module.py

import requests
import calendar
from datetime import datetime, timedelta
from dateutil import parser

BASE_URL = 'https://api.opsgenie.com/v2/schedules'

def get_on_call_schedule(api_key, schedule_id, year, month):
    """
    Retrieves the on-call schedule for a given month from Opsgenie.

    Parameters:
        api_key (str): The Opsgenie API key for authentication.
        schedule_id (str): The ID of the Opsgenie schedule.
        year (int): The year for the schedule.
        month (int): The month for the schedule.

    Returns:
        list: A list of periods with on-call information within the specified month.

    Raises:
        ValueError: If the date range is incorrect.
        ConnectionError: If there is a network or server error.
        RuntimeError: For any other unexpected errors.
    """
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
            'Authorization': f'GenieKey {api_key}'
        }
        url = f'{BASE_URL}/{schedule_id}/timeline'

        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 422:
            raise ValueError(f"Incorrect time range. Date must be no earlier than 1 year ago and no later than 2 years in the future. Requested for {year}-{month}.")
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
            if parser.isoparse(period['endDate'][:-1]) >= month_start and parser.isoparse(period['startDate'][:-1]) <= month_end
        ]

        return filtered_periods

    except requests.exceptions.RequestException as e:
        raise ConnectionError(f"Network or server error: {e}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {e}")