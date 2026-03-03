"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import os
from pathlib import Path
from database import (
    init_db,
    get_activities,
    populate_default_activities,
    signup_participant,
    unregister_participant,
    get_participation_details,
)

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Initialize database
init_db()
populate_default_activities()

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def list_activities():
    """Get all activities from the database."""
    return get_activities()


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, fee: float = 0.0):
    """Sign up a student for an activity"""
    success, message = signup_participant(activity_name, email, fee)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(activity_name: str, email: str):
    """Unregister a student from an activity"""
    success, message = unregister_participant(activity_name, email)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}


@app.get("/admin/participation")
def view_all_participation():
    """Get participation details for all activities (admin endpoint)."""
    return {"participation": get_participation_details()}


@app.get("/admin/participation/{activity_name}")
def view_activity_participation(activity_name: str):
    """Get participation details for a specific activity (admin endpoint)."""
    details = get_participation_details(activity_name)
    if not details:
        raise HTTPException(status_code=404, detail=f"No participation data or activity '{activity_name}' not found")
    return {"activity": activity_name, "participation": details}
