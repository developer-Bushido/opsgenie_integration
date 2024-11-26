# holidays_module.py

import holidays
from datetime import timedelta

def get_holidays(year, month, country_code):
    """
    Returns a dictionary of holidays for the specified month and year in the given country.

    Parameters:
        year (int): The year for which to retrieve holidays.
        month (int): The month (1-12) for which to retrieve holidays.
        country_code (str): The country code as per the 'holidays' library (e.g., 'CY' for Cyprus).

    Returns:
        dict: A dictionary where keys are dates (datetime.date) and values are holiday names.

    Raises:
        ValueError: If the country code is not supported.
    """
    try:
        country_holidays = holidays.country_holidays(country_code, years=year)
    except NotImplementedError:
        raise ValueError(f"Holidays not available for country code '{country_code}'.")

    month_holidays = {}

    for day, name in country_holidays.items():
        if day.month == month:
            month_holidays[day] = name
        # For countries with Easter Monday, add Easter Tuesday if applicable
        if name == "Easter Monday":
            easter_tuesday = day + timedelta(days=1)
            if easter_tuesday.month == month:
                month_holidays[easter_tuesday] = "Easter Tuesday (Bank Holiday)"

    return month_holidays