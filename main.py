import calendar
from datetime import datetime, timezone
from opsgenie_module import get_on_call_schedule
from holidays_module import get_cyprus_holidays
import yaml

def parse_iso_datetime(s):
    # Parse ISO datetime strings with 'Z' suffix as UTC
    if s.endswith('Z'):
        return datetime.fromisoformat(s[:-1]).replace(tzinfo=timezone.utc)
    else:
        return datetime.fromisoformat(s)

def get_on_call_report(year, month):
    """
    Generates an on-call report for the specified month and year.
    """
    schedule = get_on_call_schedule(year, month)
    holidays = get_cyprus_holidays(year, month)

    report = {}

    # Collect shift periods
    shift_periods = []
    for period in schedule:
        start = parse_iso_datetime(period['startDate'])
        end = parse_iso_datetime(period['endDate'])
        user = period['recipient']['name']
        shift_periods.append({'start': start, 'end': end, 'user': user})

    # Sort shift periods by start time
    shift_periods.sort(key=lambda x: x['start'])

    # For each day in the month
    num_days = calendar.monthrange(year, month)[1]

    for day in range(1, num_days + 1):
        # Set the time to 12:00 UTC on that day
        day_time = datetime(year, month, day, 12, 0, 0, tzinfo=timezone.utc)
        assigned_user = None

        # Find the shift that covers 'day_time'
        for shift in shift_periods:
            shift_start = shift['start']
            shift_end = shift['end']
            user = shift['user']

            if shift_start <= day_time < shift_end:
                assigned_user = user
                break  # Found the user for this day

        if assigned_user:
            if assigned_user not in report:
                report[assigned_user] = {
                    'workdays_count': 0,
                    'holidays_weekends_count': 0,
                    'days': []
                }

            current_date_str = day_time.strftime("%d %B %Y")
            # Prevent duplicate date entries
            if not any(d['date'] == current_date_str for d in report[assigned_user]['days']):
                current_date = day_time.date()
                day_type = holidays.get(current_date) or ("Weekend" if current_date.weekday() >= 5 else "Weekday")
                report[assigned_user]['days'].append({
                    'date': current_date_str,
                    'day_type': f"{calendar.day_name[current_date.weekday()]} - {day_type}"
                })
                if day_type == "Weekday":
                    report[assigned_user]['workdays_count'] += 1
                else:
                    report[assigned_user]['holidays_weekends_count'] += 1

    # Sort the days for each user
    for user in report:
        report[user]['days'].sort(key=lambda x: datetime.strptime(x['date'], "%d %B %Y"))

    # Format the report
    formatted_report = {}
    for user, data in report.items():
        formatted_report[user] = {
            f"{data['workdays_count']} weekdays, {data['holidays_weekends_count']} holidays+weekends": [
                f"{day['date']} - {day['day_type']}" for day in data['days']
            ]
        }

    return formatted_report

if __name__ == "__main__":
    year = 2024  # Replace with the desired year
    month = 7   # Replace with the desired month

    report = get_on_call_report(year, month)
    print(yaml.dump(report, allow_unicode=True, default_flow_style=False))