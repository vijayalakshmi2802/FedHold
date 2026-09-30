import sqlite3
from datetime import datetime
from pathlib import Path
import os


# ==========================================
# Database location
# ==========================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE = DATABASE_DIR / "fedhold.db"


# ==========================================
# Experiment configuration
# ==========================================

CURRENT_RUN_ID = os.getenv("FEDHOLD_RUN_ID", "RUN-001")
CONTROL_MODE = os.getenv("FEDHOLD_CONTROL_MODE", "RULE_BASED")


# ==========================================
# Connection
# ==========================================

def get_connection():
    return sqlite3.connect(str(DATABASE))


# ==========================================
# Initialize database
# ==========================================

def initialize_database():

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------
    # Bus telemetry
    # --------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bus_observations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            bus_id TEXT NOT NULL,
            position REAL NOT NULL,
            speed REAL NOT NULL,
            passengers INTEGER NOT NULL
        )
    """)

    # --------------------------------------
    # Bunching events
    # --------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bunching_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            bus_id TEXT NOT NULL,
            following_bus TEXT NOT NULL,
            headway REAL NOT NULL,
            severity TEXT NOT NULL,
            hold_seconds INTEGER NOT NULL,
            intervention_applied INTEGER NOT NULL DEFAULT 0
        )
    """)

    # --------------------------------------
    # Experiment runs
    # --------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiment_runs (
            run_id TEXT PRIMARY KEY,
            experiment_name TEXT NOT NULL,
            control_mode TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            status TEXT NOT NULL
        )
    """)

    # --------------------------------------
    # Safe migration for existing database
    # --------------------------------------

    cursor.execute("PRAGMA table_info(bunching_events)")
    columns = [row[1] for row in cursor.fetchall()]

    if "intervention_applied" not in columns:
        cursor.execute("""
            ALTER TABLE bunching_events
            ADD COLUMN intervention_applied INTEGER NOT NULL DEFAULT 0
        """)

    connection.commit()
    connection.close()


# ==========================================
# Create experiment run
# ==========================================

def create_run(run_id, experiment_name, control_mode):

    connection = get_connection()
    cursor = connection.cursor()

    # Do not recreate an existing run.
    cursor.execute("""
        SELECT run_id
        FROM experiment_runs
        WHERE run_id = ?
    """, (run_id,))

    existing = cursor.fetchone()

    if existing:
        connection.close()
        return

    cursor.execute("""
        INSERT INTO experiment_runs
        (
            run_id,
            experiment_name,
            control_mode,
            started_at,
            ended_at,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        experiment_name,
        control_mode,
        datetime.now().isoformat(),
        None,
        "RUNNING"
    ))

    connection.commit()
    connection.close()


# ==========================================
# End experiment run
# ==========================================

def end_run(run_id):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE experiment_runs
        SET
            ended_at = ?,
            status = ?
        WHERE run_id = ?
    """, (
        datetime.now().isoformat(),
        "COMPLETED",
        run_id
    ))

    connection.commit()
    connection.close()


# ==========================================
# Save bus observation
# ==========================================

def save_bus_observation(bus):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO bus_observations
        (
            run_id,
            timestamp,
            bus_id,
            position,
            speed,
            passengers
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        CURRENT_RUN_ID,
        datetime.now().isoformat(),
        bus["bus_id"],
        bus["position"],
        bus["speed"],
        bus["passengers"]
    ))

    connection.commit()
    connection.close()


# ==========================================
# Save bunching event
# ==========================================

def save_bunching_event(alert):

    connection = get_connection()
    cursor = connection.cursor()

    # In NO_CONTROL mode, bunching may be detected
    # and HOLD may be recommended, but no intervention
    # is actually applied.

    intervention_applied = (
        1 if CONTROL_MODE == "RULE_BASED" else 0
    )

    cursor.execute("""
        INSERT INTO bunching_events
        (
            run_id,
            timestamp,
            bus_id,
            following_bus,
            headway,
            severity,
            hold_seconds,
            intervention_applied
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        CURRENT_RUN_ID,
        datetime.now().isoformat(),
        alert["bus_id"],
        alert["following_bus"],
        alert["headway"],
        alert["severity"],
        alert["hold_seconds"],
        intervention_applied
    ))

    connection.commit()
    connection.close()


# ==========================================
# Get experiment metrics
# ==========================================

def get_metrics():

    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------
    # Total observations
    # --------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM bus_observations
        WHERE run_id = ?
    """, (CURRENT_RUN_ID,))

    total_observations = cursor.fetchone()[0]

    # --------------------------------------
    # Average passengers
    # --------------------------------------

    cursor.execute("""
        SELECT AVG(passengers)
        FROM bus_observations
        WHERE run_id = ?
    """, (CURRENT_RUN_ID,))

    average_passengers = cursor.fetchone()[0]

    # --------------------------------------
    # Bunching events
    # --------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM bunching_events
        WHERE run_id = ?
    """, (CURRENT_RUN_ID,))

    total_bunching_events = cursor.fetchone()[0]

    # --------------------------------------
    # Average bunching headway
    # --------------------------------------

    cursor.execute("""
        SELECT AVG(headway)
        FROM bunching_events
        WHERE run_id = ?
    """, (CURRENT_RUN_ID,))

    average_headway = cursor.fetchone()[0]

    # --------------------------------------
    # Actual interventions
    # --------------------------------------

    cursor.execute("""
        SELECT COUNT(*)
        FROM bunching_events
        WHERE run_id = ?
        AND intervention_applied = 1
    """, (CURRENT_RUN_ID,))

    total_interventions = cursor.fetchone()[0]

    connection.close()

    return {
        "run_id": CURRENT_RUN_ID,
        "control_mode": CONTROL_MODE,
        "total_observations": total_observations,
        "average_passengers": round(
            average_passengers or 0,
            2
        ),
        "total_bunching_events": total_bunching_events,
        "average_bunching_headway": round(
            average_headway or 0,
            2
        ),
        "total_interventions": total_interventions
    }