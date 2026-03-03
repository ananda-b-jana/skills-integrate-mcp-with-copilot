"""
Database module for managing extracurricular activities and participation.
"""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

DB_PATH = Path(__file__).parent / "activities.db"


def init_db():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Activities table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            schedule TEXT NOT NULL,
            max_participants INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Participation table (tracks registrations with optional fees)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS participation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_id INTEGER NOT NULL,
            email TEXT NOT NULL,
            fee REAL DEFAULT 0,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (activity_id) REFERENCES activities(id),
            UNIQUE(activity_id, email)
        )
    """)
    
    conn.commit()
    conn.close()


def get_activities() -> Dict[str, Dict[str, Any]]:
    """Retrieve all activities from database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, description, schedule, max_participants FROM activities")
    activities = {}
    
    for activity_id, name, description, schedule, max_participants in cursor.fetchall():
        # Get participants for this activity
        cursor.execute("SELECT email FROM participation WHERE activity_id = ?", (activity_id,))
        participants = [row[0] for row in cursor.fetchall()]
        
        activities[name] = {
            "id": activity_id,
            "description": description,
            "schedule": schedule,
            "max_participants": max_participants,
            "participants": participants
        }
    
    conn.close()
    return activities


def add_activity(name: str, description: str, schedule: str, max_participants: int) -> bool:
    """Add a new activity to the database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activities (name, description, schedule, max_participants) VALUES (?, ?, ?, ?)",
            (name, description, schedule, max_participants)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def signup_participant(activity_name: str, email: str, fee: float = 0.0) -> tuple[bool, str]:
    """
    Sign up a participant for an activity.
    Returns (success: bool, message: str)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get activity ID
    cursor.execute("SELECT id, max_participants FROM activities WHERE name = ?", (activity_name,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False, "Activity not found"
    
    activity_id, max_participants = result
    
    # Check if already signed up
    cursor.execute("SELECT id FROM participation WHERE activity_id = ? AND email = ?", (activity_id, email))
    if cursor.fetchone():
        conn.close()
        return False, "Student is already signed up"
    
    # Check capacity
    cursor.execute("SELECT COUNT(*) FROM participation WHERE activity_id = ?", (activity_id,))
    current_count = cursor.fetchone()[0]
    
    if current_count >= max_participants:
        conn.close()
        return False, "Activity is at maximum capacity"
    
    # Add participation record
    try:
        cursor.execute(
            "INSERT INTO participation (activity_id, email, fee) VALUES (?, ?, ?)",
            (activity_id, email, fee)
        )
        conn.commit()
        conn.close()
        return True, f"Signed up {email} for {activity_name}"
    except Exception as e:
        conn.close()
        return False, f"Database error: {str(e)}"


def unregister_participant(activity_name: str, email: str) -> tuple[bool, str]:
    """
    Unregister a participant from an activity.
    Returns (success: bool, message: str)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get activity ID
    cursor.execute("SELECT id FROM activities WHERE name = ?", (activity_name,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False, "Activity not found"
    
    activity_id = result[0]
    
    # Check if signed up
    cursor.execute("SELECT id FROM participation WHERE activity_id = ? AND email = ?", (activity_id, email))
    if not cursor.fetchone():
        conn.close()
        return False, "Student is not signed up for this activity"
    
    # Remove participation record
    cursor.execute("DELETE FROM participation WHERE activity_id = ? AND email = ?", (activity_id, email))
    conn.commit()
    conn.close()
    return True, f"Unregistered {email} from {activity_name}"


def get_participation_details(activity_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get participation details for activities.
    If activity_name is provided, return only for that activity; otherwise return all.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if activity_name:
        cursor.execute(
            """
            SELECT a.name, p.email, p.fee, p.registered_at
            FROM participation p
            JOIN activities a ON p.activity_id = a.id
            WHERE a.name = ?
            ORDER BY p.registered_at
            """,
            (activity_name,)
        )
    else:
        cursor.execute(
            """
            SELECT a.name, p.email, p.fee, p.registered_at
            FROM participation p
            JOIN activities a ON p.activity_id = a.id
            ORDER BY a.name, p.registered_at
            """
        )
    
    details = []
    for activity, email, fee, registered_at in cursor.fetchall():
        details.append({
            "activity": activity,
            "email": email,
            "fee": fee,
            "registered_at": registered_at
        })
    
    conn.close()
    return details


def populate_default_activities():
    """Load default activities from the app's existing data."""
    default_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Soccer Team": {
            "description": "Join the school soccer team and compete in matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 22,
            "participants": ["liam@mergington.edu", "noah@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Practice and play basketball with the school team",
            "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": ["ava@mergington.edu", "mia@mergington.edu"]
        },
        "Art Club": {
            "description": "Explore your creativity through painting and drawing",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
        },
        "Drama Club": {
            "description": "Act, direct, and produce plays and performances",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 20,
            "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
        },
        "Math Club": {
            "description": "Solve challenging problems and participate in math competitions",
            "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
            "max_participants": 10,
            "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop public speaking and argumentation skills",
            "schedule": "Fridays, 4:00 PM - 5:30 PM",
            "max_participants": 12,
            "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
        }
    }
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for activity_name, activity_data in default_activities.items():
        # Check if activity already exists
        cursor.execute("SELECT id FROM activities WHERE name = ?", (activity_name,))
        if cursor.fetchone():
            continue
        
        # Insert activity
        cursor.execute(
            "INSERT INTO activities (name, description, schedule, max_participants) VALUES (?, ?, ?, ?)",
            (activity_name, activity_data["description"], activity_data["schedule"], activity_data["max_participants"])
        )
        activity_id = cursor.lastrowid
        
        # Insert participants
        for email in activity_data["participants"]:
            cursor.execute(
                "INSERT INTO participation (activity_id, email, fee) VALUES (?, ?, ?)",
                (activity_id, email, 0.0)
            )
    
    conn.commit()
    conn.close()
