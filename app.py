from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from pypdf import PdfReader, PdfWriter
import tempfile
import os

app = FastAPI(title="Timesheet Filler API")

# Day-to-suffix mapping for field names
DAY_SUFFIXES = {
    1: "TUE", 2: "WED", 3: "THU", 4: "FRI", 5: "SAT", 6: "SUN", 7: "MON",
    8: "TUE_2", 9: "WED_2", 10: "THU_2", 11: "FRI_2", 12: "SAT_2", 13: "SUN_2", 14: "MON_2",
    15: "TUE_3", 16: "WED_3", 17: "THU_3", 18: "FRI_3", 19: "SAT_3", 20: "SUN_3", 21: "MON_3",
    22: "TUE_4", 23: "WED_4", 24: "THU_4", 25: "FRI_4", 26: "SAT_4", 27: "SUN_4", 28: "MON_4",
    29: "TUE_5", 30: "WED_5", 31: "THU_5"
}


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


def get_field_names_for_day(day: int) -> dict:
    """Get all field names for a specific day."""
    suffix = DAY_SUFFIXES.get(day)
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
    template_path = os.environ.get("TEMPLATE_PATH", "Leader_Timesheets_JAN_2026.pdf")
    
    if not os.path.exists(template_path):
        raise HTTPException(status_code=500, detail=f"Template PDF not found at {template_path}")
    
    try:
        reader = PdfReader(template_path)
        writer = PdfWriter()
        writer.append(reader)
        
        field_values = {}
        
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
            fields = get_field_names_for_day(shift.day)
            
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
        "day_suffixes": DAY_SUFFIXES,
        "example_day_1_fields": get_field_names_for_day(1)
    }
