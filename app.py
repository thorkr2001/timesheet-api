from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from pypdf import PdfReader, PdfWriter
import tempfile
import os
import calendar
from functools import lru_cache

app = FastAPI(title="Timesheet Filler API")

# Default day-to-suffix mapping (fallback if template parsing fails)
DEFAULT_DAY_SUFFIXES = {
    1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT", 6: "SUN", 7: "MON",
    8: "TUE_2", 9: "WED_2", 10: "THU_2", 11: "FRI_2", 12: "SAT_2", 13: "SUN_2", 14: "MON_2",
    15: "TUE_3", 16: "WED_3", 17: "THU_3", 18: "FRI_3", 19: "SAT_3", 20: "SUN_3", 21: "MON_3",
    22: "TUE_4", 23: "WED_4", 24: "THU_4", 25: "FRI_4", 26: "SAT_4", 27: "SUN_4", 28: "MON_4",
    29: "TUE_5", 30: "WED_5", 31: "THU_5"
}

MONTH_ABBR_TO_INDEX = {
    "JAN": 0, "FEB": 1, "MAR": 2, "APR": 3, "MAY": 4, "JUN": 5,
    "JUL": 6, "AUG": 7, "SEP": 8, "OCT": 9, "NOV": 10, "DEC": 11
}


def parse_month_year(month_str: Optional[str]) -> Optional[tuple]:
    if not month_str:
        return None
    parts = month_str.strip().upper().split()
    if len(parts) != 2:
        return None
    mon_abbr, year_str = parts
    if mon_abbr not in MONTH_ABBR_TO_INDEX:
        return None
    try:
        year = int(year_str)
    except ValueError:
        return None
    return (year, MONTH_ABBR_TO_INDEX[mon_abbr])


WEEKDAY_ABBR_TITLE = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
WEEKDAY_ABBR_UPPER = {0: "MON", 1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT", 6: "SUN"}


@lru_cache(maxsize=32)
def build_day_suffixes_from_template(template_path: str) -> dict:
    """
    Build a day->suffix mapping by reading the template's existing Day dropdown values.

    The PDF time fields are named like:
      TIME ON 1THU, TIME ON 1THU_2, ...
    The template's Day 01..Day 31 dropdown values tell us which weekday that row
    was originally aligned to, which we can convert into the suffix names.
    """
    reader = PdfReader(template_path)
    fields = reader.get_fields() or {}

    weekday_counts = {abbr: 0 for abbr in WEEKDAY_ABBR_UPPER.values()}
    mapping: dict[int, str] = {}

    for day in range(1, 32):
        day_key = f"Day {str(day).zfill(2)}"
        field = fields.get(day_key)
        raw_val = None
        if field:
            raw_val = field.get("/V") or field.get("/DV")

        val = str(raw_val).strip() if raw_val is not None else ""
        if val == "...":
            mapping[day] = DEFAULT_DAY_SUFFIXES.get(day, "TUE")
            continue

        abbr = val[:3].upper()
        if abbr not in weekday_counts:
            mapping[day] = DEFAULT_DAY_SUFFIXES.get(day, "TUE")
            continue

        weekday_counts[abbr] += 1
        mapping[day] = abbr if weekday_counts[abbr] == 1 else f"{abbr}_{weekday_counts[abbr]}"

    # Ensure we have a mapping for all possible days
    for day in range(1, 32):
        mapping.setdefault(day, DEFAULT_DAY_SUFFIXES.get(day, "TUE"))

    return mapping


def fill_day_dropdowns(field_values: dict, month_str: Optional[str]) -> None:
    """
    Fill Day 01..Day 31 dropdowns with the correct weekday for the requested month/year.
    Allowed values in the template are: Mon/Tue/Wed/Thu/Fri/Sat/Sun and '...'.
    """
    parsed = parse_month_year(month_str)
    if not parsed:
        return

    year, month_index = parsed
    _, days_in_month = calendar.monthrange(year, month_index + 1)

    for day in range(1, 32):
        key = f"Day {str(day).zfill(2)}"
        if day > days_in_month:
            field_values[key] = "..."
            continue
        weekday = calendar.weekday(year, month_index + 1, day)  # 0=Mon..6=Sun
        field_values[key] = WEEKDAY_ABBR_TITLE[weekday]


def resolve_template_path(month_str: Optional[str]) -> str:
    """Select a template based on month string if available."""
    parsed = parse_month_year(month_str)
    if parsed:
        year, month_index = parsed
        month_abbr = list(MONTH_ABBR_TO_INDEX.keys())[month_index]
        candidate = f"Leader_Timesheets_{month_abbr}_{year}.pdf"
        if os.path.exists(candidate):
            return candidate
    return os.environ.get("TEMPLATE_PATH", "Leader_Timesheets_JAN_2026.pdf")


class Shift(BaseModel):
    day: int  # 1-31
    time_on_1: Optional[str] = None
    time_off_1: Optional[str] = None
    time_on_2: Optional[str] = None
    time_off_2: Optional[str] = None
    time_on_3: Optional[str] = None
    time_off_3: Optional[str] = None
    basic_hours: Optional[str] = None
    night_duty_hours: Optional[str] = None
    sunday_hours: Optional[str] = None
    pub_hol_hours: Optional[str] = None
    disturbed: Optional[bool] = False
    undisturbed: Optional[bool] = False
    expenses: Optional[str] = None


class TimesheetData(BaseModel):
    # Header fields
    employee_name: str
    employee_number: str
    employee_payroll: Optional[str] = None
    leader: Optional[str] = None
    leader_code: Optional[str] = None
    month: Optional[str] = "JAN 2026"
    sheets: Optional[str] = None
    comments: Optional[str] = None
    
    # Shifts data
    shifts: List[Shift]
    
    # Optional totals
    basic_total: Optional[str] = None
    night_duty_total: Optional[str] = None
    sun_total: Optional[str] = None
    pub_hol_total: Optional[str] = None
    disturbed_total: Optional[str] = None
    undisturbed_total: Optional[str] = None
    hours_used_total: Optional[str] = None


def get_field_names_for_day(day: int, day_suffixes: dict) -> dict:
    """Get all field names for a specific day."""
    suffix = day_suffixes.get(day)
    if not suffix:
        raise ValueError(f"Invalid day: {day}")
    
    day_str = str(day).zfill(2)
    
    return {
        "day_dropdown": f"Day {day_str}",
        "time_on_1": f"TIME ON 1{suffix}",
        "time_off_1": f"TIME OFF 1{suffix}",
        "time_on_2": f"TIME ON 2{suffix}",
        "time_off_2": f"T ME OFF 2{suffix}",
        "time_on_3": f"T ME ON 3{suffix}",
        "time_off_3": f"TIME OFF 3{suffix}",
        "basic_hours": f"BASIC 08002000 MonSat{suffix}",
        "night_duty_hours": f"NIGHT DUTY after 2000 before 0800 MonSat{suffix}",
        "sunday_hours": f"SUN{suffix}",
        "pub_hol_hours": f"PUB HOL{suffix}",
        "disturbed": f"disturbed-{day}",
        "undisturbed": f"undisturbed-{day}",
        "expenses": f"EXPENSES RECEIPTS{suffix}"
    }


@app.post("/fill-timesheet")
async def fill_timesheet(data: TimesheetData):
    """Fill the timesheet PDF with provided data and return the filled PDF."""
    template_path = resolve_template_path(data.month)
    
    if not os.path.exists(template_path):
        raise HTTPException(status_code=500, detail=f"Template PDF not found at {template_path}")
    
    try:
        reader = PdfReader(template_path)
        writer = PdfWriter()
        writer.append(reader)
        
        field_values = {}

        # Always set weekday dropdowns based on requested month (prevents manual edits)
        fill_day_dropdowns(field_values, data.month)

        # Determine which suffix corresponds to each date row in THIS template file
        day_suffixes = build_day_suffixes_from_template(template_path)
        
        # Header fields
        field_values["employee-name"] = data.employee_name
        field_values["employee-number"] = data.employee_number
        
        if data.employee_payroll:
            field_values["employee-payroll"] = data.employee_payroll
        if data.leader:
            field_values["leader"] = data.leader
        if data.leader_code:
            field_values["leader-code"] = data.leader_code
        if data.month:
            field_values["2026"] = data.month
        if data.sheets:
            field_values["Sheets"] = data.sheets
        if data.comments:
            field_values["Comments"] = data.comments
        
        # Process each shift
        for shift in data.shifts:
            fields = get_field_names_for_day(shift.day, day_suffixes)
            
            if shift.time_on_1:
                field_values[fields["time_on_1"]] = shift.time_on_1
            if shift.time_off_1:
                field_values[fields["time_off_1"]] = shift.time_off_1
            if shift.time_on_2:
                field_values[fields["time_on_2"]] = shift.time_on_2
            if shift.time_off_2:
                field_values[fields["time_off_2"]] = shift.time_off_2
            if shift.time_on_3:
                field_values[fields["time_on_3"]] = shift.time_on_3
            if shift.time_off_3:
                field_values[fields["time_off_3"]] = shift.time_off_3
            if shift.basic_hours:
                field_values[fields["basic_hours"]] = shift.basic_hours
            if shift.night_duty_hours:
                field_values[fields["night_duty_hours"]] = shift.night_duty_hours
            if shift.sunday_hours:
                field_values[fields["sunday_hours"]] = shift.sunday_hours
            if shift.pub_hol_hours:
                field_values[fields["pub_hol_hours"]] = shift.pub_hol_hours
            if shift.expenses:
                field_values[fields["expenses"]] = shift.expenses
            
            field_values[fields["disturbed"]] = "/Yes" if shift.disturbed else "/Off"
            field_values[fields["undisturbed"]] = "/Yes" if shift.undisturbed else "/Off"
        
        # Totals
        if data.basic_total:
            field_values["BASIC-TOTAL"] = data.basic_total
        if data.night_duty_total:
            field_values["NIGHT-DUTY-TOTAL"] = data.night_duty_total
        if data.sun_total:
            field_values["SUN-TOTAL"] = data.sun_total
        if data.pub_hol_total:
            field_values["PUB-HOL-TOTAL"] = data.pub_hol_total
        if data.disturbed_total:
            field_values["DIS-TOTAL"] = data.disturbed_total
        if data.undisturbed_total:
            field_values["UNDIS-TOTAL"] = data.undisturbed_total
        if data.hours_used_total:
            field_values["HOURS-USED-TOTAL"] = data.hours_used_total
        
        writer.update_page_form_field_values(writer.pages[0], field_values)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            writer.write(tmp)
            tmp_path = tmp.name
        
        return FileResponse(
            tmp_path,
            media_type="application/pdf",
            filename=f"timesheet_{data.employee_name.replace(' ', '_')}.pdf"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/")
async def root():
    return {"message": "Timesheet Filler API is running", "docs": "/docs"}


@app.get("/fields")
async def list_fields():
    return {
        "header_fields": [
            "employee-name", "employee-number", "employee-payroll",
            "leader", "leader-code", "2026", "Sheets", "Comments"
        ],
        "total_fields": [
            "BASIC-TOTAL", "NIGHT-DUTY-TOTAL", "SUN-TOTAL",
            "PUB-HOL-TOTAL", "DIS-TOTAL", "UNDIS-TOTAL", "HOURS-USED-TOTAL"
        ],
        "day_suffixes": DEFAULT_DAY_SUFFIXES,
        "example_day_1_fields": get_field_names_for_day(1, DEFAULT_DAY_SUFFIXES)
    }
