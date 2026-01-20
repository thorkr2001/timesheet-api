#!/usr/bin/env python3
"""Test the payroll parser with full dataset"""
import json
from payroll_parser import parse_payroll_shifts

# Full test data from user
test_data = {
    "shifts": [
        {"date": 1, "day": "Sunday", "time": "20:00", "on_shift": "Judy", "comments": ""},
        {"date": 2, "day": "Monday", "time": "", "on_shift": "Judy", "comments": ""},
        {"date": 3, "day": "Tuesday", "time": "20:00", "on_shift": "Eunice", "comments": ""},
        {"date": 4, "day": "Wednesday", "time": "20:00", "on_shift": "Rosana", "comments": ""},
        {"date": 5, "day": "Thursday", "time": "", "on_shift": "Rosana", "comments": ""},
        {"date": 6, "day": "Friday", "time": "20:00", "on_shift": "Laura", "comments": ""},
        {"date": 7, "day": "Saturday", "time": "", "on_shift": "Laura", "comments": ""},
        {"date": 8, "day": "Sunday", "time": "20:00", "on_shift": "Eunice", "comments": ""},
        {"date": 9, "day": "Monday", "time": "20:00", "on_shift": "Judy", "comments": ""},
        {"date": 10, "day": "Tuesday", "time": "20:00", "on_shift": "Jane", "comments": ""},
        {"date": 11, "day": "Wednesday", "time": "20:00", "on_shift": "Brenda", "comments": ""},
        {"date": 12, "day": "Thursday", "time": "", "on_shift": "Brenda", "comments": ""},
        {"date": 13, "day": "Friday", "time": "20:00", "on_shift": "Laura", "comments": ""},
        {"date": 14, "day": "Saturday", "time": "20:00", "on_shift": "Rosana", "comments": ""},
        {"date": 15, "day": "Sunday", "time": "", "on_shift": "Rosana", "comments": ""},
        {"date": 16, "day": "Monday", "time": "20:00", "on_shift": "Eunice", "comments": ""},
        {"date": 17, "day": "Tuesday", "time": "20:00", "on_shift": "Jane", "comments": ""},
        {"date": 18, "day": "Wednesday", "time": "20:00", "on_shift": "Brenda", "comments": ""},
        {"date": 19, "day": "Thursday", "time": "", "on_shift": "Brenda", "comments": ""},
        {"date": 20, "day": "Friday", "time": "20:00", "on_shift": "Laura", "comments": ""},
        {"date": 21, "day": "Saturday", "time": "20:00", "on_shift": "Rosana", "comments": ""},
        {"date": 22, "day": "Sunday", "time": "", "on_shift": "Rosana", "comments": ""},
        {"date": 23, "day": "Monday", "time": "20:00", "on_shift": "Eunice", "comments": ""},
        {"date": 24, "day": "Tuesday", "time": "", "on_shift": "Eunice", "comments": ""},
        {"date": 25, "day": "Wednesday", "time": "20:00", "on_shift": "Brenda", "comments": ""},
        {"date": 26, "day": "Thursday", "time": "", "on_shift": "Brenda", "comments": ""},
        {"date": 27, "day": "Friday", "time": "20:00", "on_shift": "Grainne", "comments": ""},
        {"date": 28, "day": "Saturday", "time": "", "on_shift": "Grainne", "comments": ""},
        {"date": 29, "day": "Sunday", "time": "20:00", "on_shift": "Eunice", "comments": ""},
        {"date": 30, "day": "Monday", "time": "20:00", "on_shift": "Jane", "comments": ""},
        {"date": 31, "day": "Tuesday", "time": "", "on_shift": "", "comments": ""}
    ],
    "timesheets": [
        {"employee": "Judy", "start_date": 1, "start_day": "Sunday", "start_time": "20:00", "end_date": 3, "end_day": "Tuesday", "end_time": "20:00", "total_hours": 48, "comments": ""},
        {"employee": "Eunice", "start_date": 3, "start_day": "Tuesday", "start_time": "20:00", "end_date": 4, "end_day": "Wednesday", "end_time": "20:00", "total_hours": 24, "comments": ""},
        {"employee": "Rosana", "start_date": 4, "start_day": "Wednesday", "start_time": "20:00", "end_date": 6, "end_day": "Friday", "end_time": "20:00", "total_hours": 48, "comments": ""},
        {"employee": "Laura", "start_date": 6, "start_day": "Friday", "start_time": "20:00", "end_date": 8, "end_day": "Sunday", "end_time": "20:00", "total_hours": 48, "comments": ""},
        {"employee": "Eunice", "start_date": 8, "start_day": "Sunday", "start_time": "20:00", "end_date": 9, "end_day": "Monday", "end_time": "20:00", "total_hours": 24, "comments": ""},
        {"employee": "Judy", "start_date": 9, "start_day": "Monday", "start_time": "20:00", "end_date": 10, "end_day": "Tuesday", "end_time": "20:00", "total_hours": 24, "comments": ""},
        {"employee": "Jane", "start_date": 10, "start_day": "Tuesday", "start_time": "20:00", "end_date": 11, "end_day": "Wednesday", "end_time": "20:00", "total_hours": 24, "comments": ""},
        {"employee": "Brenda", "start_date": 11, "start_day": "Wednesday", "start_time": "20:00", "end_date": 13, "end_day": "Friday", "end_time": "20:00", "total_hours": 48, "comments": ""},
        {"employee": "Laura", "start_date": 13, "start_day": "Friday", "start_time": "20:00", "end_date": 14, "end_day": "Saturday", "end_time": "20:00", "total_hours": 24, "comments": ""},
        {"employee": "Rosana", "start_date": 14, "start_day": "Saturday", "start_time": "20:00", "end_date": 16, "end_day": "Monday", "end_time": "20:00", "total_hours": 48, "comments": ""},
        {"employee": "Eunice", "start_date": 16, "start_day": "Monday", "start_time": "20:00", "end_date": 17, "end_day": "Tuesday", "end_time": "20:00", "total_hours": 24, "comments": ""},
        {"employee": "Jane", "start_date": 17, "start_day": "Tuesday", "start_time": "20:00", "end_date": 18, "end_day": "Wednesday", "end_time": "20:00", "total_hours": 24, "comments": ""},
        {"employee": "Brenda", "start_date": 18, "start_day": "Wednesday", "start_time": "20:00", "end_date": 20, "end_day": "Friday", "end_time": "20:00", "total_hours": 48, "comments": ""},
        {"employee": "Laura", "start_date": 20, "start_day": "Friday", "start_time": "20:00", "end_date": 21, "end_day": "Saturday", "end_time": "20:00", "total_hours": 24, "comments": ""},
        {"employee": "Rosana", "start_date": 21, "start_day": "Saturday", "start_time": "20:00", "end_date": 23, "end_day": "Monday", "end_time": "20:00", "total_hours": 48, "comments": ""},
        {"employee": "Eunice", "start_date": 23, "start_day": "Monday", "start_time": "20:00", "end_date": 25, "end_day": "Wednesday", "end_time": "20:00", "total_hours": 48, "comments": ""},
        {"employee": "Brenda", "start_date": 25, "start_day": "Wednesday", "start_time": "20:00", "end_date": 27, "end_day": "Friday", "end_time": "20:00", "total_hours": 48, "comments": ""},
        {"employee": "Grainne", "start_date": 27, "start_day": "Friday", "start_time": "20:00", "end_date": 29, "end_day": "Sunday", "end_time": "20:00", "total_hours": 48, "comments": ""},
        {"employee": "Eunice", "start_date": 29, "start_day": "Sunday", "start_time": "20:00", "end_date": 30, "end_day": "Monday", "end_time": "20:00", "total_hours": 24, "comments": ""}
    ],
    "summary": "...",
    "totalEntries": 19
}

# Parse and print results
results = parse_payroll_shifts(test_data, month="MAR 2026", year=2026, month_num=3)

print(f"Generated {len(results)} employee timesheets:\n")

for ts in results:
    print(f"Employee: {ts['employee_name']}")
    print(f"  Shifts: {len(ts['shifts'])} days")
    print(f"  Basic hours: {ts['basic_total']}")
    print(f"  Night duty: {ts['night_duty_total']}")
    print(f"  Sunday: {ts['sun_total']}")
    print(f"  Disturbed: {ts['disturbed_total']}")
    print(f"  Total hours: {ts['hours_used_total']}")
    print()

# Show detailed breakdown for first employee
print("Detailed breakdown for Judy:")
judy = next((ts for ts in results if ts['employee_name'] == 'Judy'), None)
if judy:
    for shift in judy['shifts']:
        print(f"  Day {shift['day']}: on={shift['time_on_1']}, off={shift['time_off_3']}, "
              f"basic={shift['basic_hours']}, night={shift['night_duty_hours']}, "
              f"sun={shift['sunday_hours']}, disturbed={shift['disturbed']}")
