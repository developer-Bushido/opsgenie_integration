# app.py

import os
from flask import Flask, render_template, request, jsonify, json
from datetime import datetime, timezone
from opsgenie_module import get_on_call_schedule
from holidays_module import get_holidays
import calendar
import colorsys
from dateutil import parser
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
API_KEY = os.getenv('API_KEY')
SCHEDULE_ID = os.getenv('SCHEDULE_ID')
COUNTRY_CODE = os.getenv('COUNTRY_CODE', 'CY')  # Default to 'CY' (Cyprus)

if not API_KEY or not SCHEDULE_ID:
    raise ValueError("API_KEY and SCHEDULE_ID must be set in the environment variables.")

def parse_iso_datetime(s):
    return parser.isoparse(s)

def get_on_call_report(year, month):
    schedule = get_on_call_schedule(API_KEY, SCHEDULE_ID, year, month)
    holidays = get_holidays(year, month, COUNTRY_CODE)

    report = {}
    shift_periods = []

    for period in schedule:
        start = parse_iso_datetime(period['startDate'])
        end = parse_iso_datetime(period['endDate'])
        user = period['recipient']['name']
        shift_periods.append({'start': start, 'end': end, 'user': user})

    shift_periods.sort(key=lambda x: x['start'])
    num_days = calendar.monthrange(year, month)[1]

    for day in range(1, num_days + 1):
        day_time = datetime(year, month, day, 12, 0, 0, tzinfo=timezone.utc)
        assigned_user = None

        for shift in shift_periods:
            if shift['start'] <= day_time < shift['end']:
                assigned_user = shift['user']
                break

        if assigned_user:
            if assigned_user not in report:
                report[assigned_user] = {
                    'workdays_count': 0,
                    'holidays_weekends_count': 0,
                    'days': []
                }

            current_date_str = day_time.strftime("%d %B %Y")
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

    for user in report:
        report[user]['days'].sort(key=lambda x: datetime.strptime(x['date'], "%d %B %Y"))

    # Sort the report by user name
    sorted_report = dict(sorted(report.items()))

    return sorted_report

@app.route('/')
def index():
    year = request.args.get('year', type=int) or datetime.now().year
    month = request.args.get('month', type=int) or datetime.now().month

    report = get_on_call_report(year, month)
    users = list(report.keys())
    colors = generate_user_colors(users)
    month_name = calendar.month_name[month]

    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    return render_template(
        'index.html',
        users=users,
        user_stats=report,
        colors=colors,
        month=month,
        year=year,
        month_name=month_name,
        prev_month=prev_month,
        prev_year=prev_year,
        next_month=next_month,
        next_year=next_year
    )

@app.route("/get_events")
def get_events():
    year = request.args.get("year", type=int)
    month = request.args.get("month", type=int)
    if not year or not month:
        return jsonify({"error": "Year and month are required"}), 400

    try:
        events_data = get_on_call_report(year, month)
        users = list(events_data.keys())
        colors = generate_user_colors(users)
        holidays = get_holidays(year, month, COUNTRY_CODE)

        # Create on-call events
        events = [
            {
                "title": user.split('@')[0],
                "start": datetime.strptime(entry['date'], "%d %B %Y").date().isoformat(),
                "color": colors[user],
                "allDay": True
            }
            for user, user_data in events_data.items()
            for entry in user_data['days']
        ]

        # Add holiday events
        for holiday_date, holiday_name in holidays.items():
            if holiday_date.month == month:
                events.append({
                    "title": holiday_name,
                    "start": holiday_date.isoformat(),
                    "allDay": True,
                    "display": 'background',
                    "color": "#ffeaa7",
                    "className": "holiday"
                })

        # Create day_types for cell coloring
        day_types = {}
        num_days = calendar.monthrange(year, month)[1]
        for day in range(1, num_days + 1):
            date_obj = datetime(year, month, day).date()
            date_str = date_obj.isoformat()
            if date_obj in holidays:
                day_types[date_str] = holidays[date_obj]
            elif date_obj.weekday() >= 5:
                day_types[date_str] = 'Weekend'
            else:
                day_types[date_str] = 'Weekday'

        # Prepare summary data and sort by user name
        summary_data = sorted(
            [
                {
                    "user": user.split('@')[0],
                    "workdays_count": data['workdays_count'],
                    "holidays_weekends_count": data['holidays_weekends_count']
                }
                for user, data in events_data.items()
            ],
            key=lambda x: x["user"]
        )

        return app.response_class(
            response=json.dumps({
                "events": events,
                "summary": summary_data,
                "day_types": day_types
            }, ensure_ascii=False),
            mimetype='application/json'
        )
    except Exception as e:
        print(f"Error retrieving on-call data: {e}")
        return jsonify({"error": str(e)}), 500

def generate_user_colors(users):
    num_users = len(users)
    colors = []
    for i in range(num_users):
        hue = i / num_users
        lightness = 0.5  # More saturated colors
        saturation = 0.7  # Brighter colors
        rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
        color = '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        colors.append(color)
    return dict(zip(users, colors))

if __name__ == '__main__':
    app.run(debug=True)