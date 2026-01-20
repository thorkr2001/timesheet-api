"""
Parser to convert payroll shift format to timesheet format.

Input format: Continuous work periods with start/end dates
Output format: Detailed daily shifts with time breakdowns
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import calendar


def parse_payroll_shifts(payroll_data: dict, month: str = "MAR 2026", year: int = 2026, month_num: int = 3) -> List[Dict]:
    """
    Convert payroll shift data into timesheet format.

    Args:
        payroll_data: Dict with 'timesheets' array containing work periods
        month: Month string like "MAR 2026"
        year: Year (default 2026)
        month_num: Month number 1-12 (default 3 for March)

    Returns:
        List of timesheet data dicts, one per employee
    """
    timesheets_by_employee = {}

    # Group timesheets by employee
    for timesheet_entry in payroll_data.get('timesheets', []):
        employee = timesheet_entry['employee']

        if employee not in timesheets_by_employee:
            timesheets_by_employee[employee] = {
                "employee_name": employee,
                "employee_number": "",
                "employee_payroll": "",
                "leader": "",
                "leader_code": "",
                "month": month,
                "sheets": "1",
                "comments": "",
                "shifts": [],
                "basic_total": "0",
                "night_duty_total": "0",
                "sun_total": "0",
                "pub_hol_total": "0",
                "disturbed_total": "0",
                "undisturbed_total": "0",
                "hours_used_total": "0"
            }

        # Convert this work period into shifts
        shifts = convert_work_period_to_shifts(
            timesheet_entry['start_date'],
            timesheet_entry['end_date'],
            timesheet_entry['start_time'],
            timesheet_entry['end_time'],
            year,
            month_num
        )

        timesheets_by_employee[employee]['shifts'].extend(shifts)

    # Calculate totals for each employee
    for employee_data in timesheets_by_employee.values():
        calculate_totals(employee_data)

    return list(timesheets_by_employee.values())


def convert_work_period_to_shifts(start_date: int, end_date: int, start_time: str, end_time: str, year: int, month: int) -> List[Dict]:
    """
    Convert a continuous work period into daily shift records.

    Pattern for residential care shifts:
    - 48-hour shift (20:00 to 20:00, 2 days later):
      * Day 1: 20:00-00:00 (4 hours - night/sunday)
      * Day 2: 08:00-00:00 (10.5 basic + 4 night, or 14.5 sunday if Sunday)
      * Day 3: 08:00-20:00 (11 hours - basic or sunday)

    - 24-hour shift (20:00 to 20:00, next day):
      * Day 1: 20:00-00:00 (4 hours - night/sunday)
      * Day 2: 08:00-20:00 (11 hours - basic or sunday)

    Standard shift pattern with breaks:
    - 08:00-11:00, 12:00-15:30, 16:00-20:00/00:00
    """
    shifts = []
    total_days = end_date - start_date  # 1 for 24hr, 2 for 48hr

    # Get day of week for each date
    weekdays = {}
    for day in range(start_date, end_date + 1):
        try:
            wd = calendar.weekday(year, month, day)
            weekdays[day] = wd  # 0=Mon, 6=Sun
        except:
            weekdays[day] = None

    # First day - evening shift (20:00-00:00)
    if start_time == "20:00":
        first_shift = {
            "day": start_date,
            "time_on_1": "20:00",
            "time_off_1": "00:00",
            "time_on_2": None,
            "time_off_2": None,
            "time_on_3": None,
            "time_off_3": None,
            "basic_hours": None,
            "night_duty_hours": None,
            "sunday_hours": None,
            "pub_hol_hours": None,
            "disturbed": True,
            "undisturbed": False,
            "expenses": None
        }

        # Check if first day is Sunday
        if weekdays.get(start_date) == 6:  # Sunday
            first_shift["sunday_hours"] = "4"
        else:
            first_shift["night_duty_hours"] = "4"

        shifts.append(first_shift)

    # Process remaining days
    for day_offset in range(1, total_days + 1):
        day = start_date + day_offset
        is_last_day = (day == end_date)
        is_middle_day = not is_last_day and total_days > 1
        is_sunday = weekdays.get(day) == 6

        # Determine shift pattern for this day
        if is_last_day and end_time == "20:00":
            # Last day ending at 20:00 (08:00-20:00)
            day_end_time = "20:00"
            night_hours = None
            basic_hours = "11"
            disturbed = False
        elif is_middle_day or (is_last_day and end_time == "00:00"):
            # Middle day OR last day ending at midnight (08:00-00:00)
            day_end_time = "00:00"
            night_hours = "4"
            basic_hours = "10.5"
            disturbed = True
        else:
            # Default to 20:00 end
            day_end_time = "20:00"
            night_hours = None
            basic_hours = "11"
            disturbed = False

        shift = {
            "day": day,
            "time_on_1": "08:00",
            "time_off_1": "11:00",
            "time_on_2": "12:00",
            "time_off_2": "15:30",
            "time_on_3": "16:00",
            "time_off_3": day_end_time,
            "basic_hours": None,
            "night_duty_hours": night_hours,
            "sunday_hours": None,
            "pub_hol_hours": None,
            "disturbed": disturbed,
            "undisturbed": False,
            "expenses": None
        }

        # Allocate hours to appropriate category
        if is_sunday:
            # All hours on Sunday go to sunday_hours
            if day_end_time == "00:00":
                shift["sunday_hours"] = "14.5"  # 08:00-00:00 with breaks
                shift["night_duty_hours"] = None  # Don't double-count
            else:
                shift["sunday_hours"] = basic_hours
        else:
            shift["basic_hours"] = basic_hours

        shifts.append(shift)

    return shifts


def calculate_totals(employee_data: Dict) -> None:
    """Calculate total hours for an employee's timesheet."""
    basic_total = 0.0
    night_duty_total = 0.0
    sun_total = 0.0
    pub_hol_total = 0.0
    disturbed_count = 0
    undisturbed_count = 0

    for shift in employee_data['shifts']:
        if shift.get('basic_hours'):
            basic_total += float(shift['basic_hours'])
        if shift.get('night_duty_hours'):
            night_duty_total += float(shift['night_duty_hours'])
        if shift.get('sunday_hours'):
            sun_total += float(shift['sunday_hours'])
        if shift.get('pub_hol_hours'):
            pub_hol_total += float(shift['pub_hol_hours'])
        if shift.get('disturbed'):
            disturbed_count += 1
        if shift.get('undisturbed'):
            undisturbed_count += 1

    hours_used_total = basic_total + night_duty_total + sun_total + pub_hol_total

    employee_data['basic_total'] = str(basic_total) if basic_total > 0 else "0"
    employee_data['night_duty_total'] = str(int(night_duty_total)) if night_duty_total > 0 else "0"
    employee_data['sun_total'] = str(int(sun_total)) if sun_total > 0 else "0"
    employee_data['pub_hol_total'] = str(int(pub_hol_total)) if pub_hol_total > 0 else "0"
    employee_data['disturbed_total'] = str(disturbed_count)
    employee_data['undisturbed_total'] = str(undisturbed_count)
    employee_data['hours_used_total'] = str(hours_used_total) if hours_used_total > 0 else "0"


# Example usage
if __name__ == "__main__":
    import json

    sample_data = {
        "timesheets": [
            {
                "employee": "Judy",
                "start_date": 1,
                "start_day": "Sunday",
                "start_time": "20:00",
                "end_date": 3,
                "end_day": "Tuesday",
                "end_time": "20:00",
                "total_hours": 48,
                "comments": ""
            }
        ]
    }

    result = parse_payroll_shifts(sample_data, month="MAR 2026", year=2026, month_num=3)
    print(json.dumps(result, indent=2))
