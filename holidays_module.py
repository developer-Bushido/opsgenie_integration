# holiday_module.py

import holidays
from datetime import timedelta

def get_cyprus_holidays(year, month):
    """
    Возвращает словарь праздников на Кипре для указанного месяца и года.
    """
    cyprus_holidays = holidays.CY(years=year)
    month_holidays = {}

    for day, name in cyprus_holidays.items():
        if day.month == month:
            month_holidays[day] = name
        if name == "Easter Monday":
            easter_tuesday = day + timedelta(days=1)
            if easter_tuesday.month == month:
                month_holidays[easter_tuesday] = "Easter Tuesday (Bank Holiday)"

    return month_holidays