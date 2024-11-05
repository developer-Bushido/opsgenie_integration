# app.py

from flask import Flask, render_template, request, jsonify, json
from datetime import datetime, timezone, timedelta
from opsgenie_module import get_on_call_schedule
from holidays_module import get_cyprus_holidays
import calendar
import colorsys

app = Flask(__name__)

def parse_iso_datetime(s):
    if s.endswith('Z'):
        return datetime.fromisoformat(s[:-1]).replace(tzinfo=timezone.utc)
    else:
        return datetime.fromisoformat(s)

def get_on_call_report(year, month):
    schedule = get_on_call_schedule(year, month)
    holidays = get_cyprus_holidays(year, month)

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

    # Сортируем report по ключу (имени пользователя) в алфавитном порядке
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
        holidays = get_cyprus_holidays(year, month)

        # Создаем события дежурств
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

        # Добавляем события праздников
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

        # Создаем day_types для раскрашивания ячеек дней
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

        # Создаем summary_data и сортируем по имени пользователя
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
        print(f"Ошибка при получении данных дежурств: {e}")
        return jsonify({"error": str(e)}), 500

def generate_user_colors(users):
    num_users = len(users)
    colors = []
    for i in range(num_users):
        hue = i / num_users
        lightness = 0.5  # Более насыщенные цвета
        saturation = 0.7  # Более яркие цвета
        rgb = colorsys.hls_to_rgb(hue, lightness, saturation)
        color = '#%02x%02x%02x' % tuple(int(c * 255) for c in rgb)
        colors.append(color)
    return dict(zip(users, colors))

if __name__ == '__main__':
    app.run(debug=True)