import time
import random
import requests


# ============================================================
# Experiment configuration
# ============================================================

CONTROL_MODE = "RULE_BASED"

# Available modes:
#
# NO_CONTROL
# RULE_BASED
#
# Later:
# RL


# ============================================================
# Backend URLs
# ============================================================

import os

API_HOST = os.getenv("FEDHOLD_API_HOST", "127.0.0.1")

API_URL = f"http://{API_HOST}:8000/update-buses"
CONTROL_URL = f"http://{API_HOST}:8000/control-decisions"


# ============================================================
# Route
# ============================================================

STOPS = [
    "Central",
    "Market",
    "Hospital",
    "College",
    "Railway",
    "Airport",
    "Tech Park",
    "University",
    "Bus Stand",
    "Industrial Area"
]


# ============================================================
# Initial bus state
# ============================================================

buses = [
    {
        "bus_id": "BUS-101",
        "position": 0.0,
        "speed": 1.0,
        "passengers": 35
    },
    {
        "bus_id": "BUS-102",
        "position": 2.0,
        "speed": 1.0,
        "passengers": 42
    },
    {
        "bus_id": "BUS-103",
        "position": 4.0,
        "speed": 1.0,
        "passengers": 28
    },
    {
        "bus_id": "BUS-104",
        "position": 6.0,
        "speed": 1.0,
        "passengers": 50
    },
    {
        "bus_id": "BUS-105",
        "position": 8.0,
        "speed": 1.0,
        "passengers": 31
    }
]


# ============================================================
# HOLD state
# ============================================================

hold_until = {}


# ============================================================
# Get control decisions
# ============================================================

def get_control_decisions():

    if CONTROL_MODE == "NO_CONTROL":
        return {
            "status": "NO_CONTROL",
            "decisions": []
        }

    try:

        response = requests.get(
            CONTROL_URL,
            timeout=2
        )

        if response.status_code == 200:
            return response.json()

    except requests.exceptions.RequestException:
        pass

    return {
        "status": "NORMAL",
        "decisions": []
    }


# ============================================================
# Startup information
# ============================================================

print("=" * 60)
print("FEDHOLD LIVE BUS SIMULATOR")
print("=" * 60)

print(f"Control Mode: {CONTROL_MODE}")


if CONTROL_MODE == "NO_CONTROL":

    print("Control feedback disabled")
    print("Buses will continue moving without HOLD intervention")

elif CONTROL_MODE == "RULE_BASED":

    print("Rule-based control feedback enabled")
    print("Simulator will apply HOLD decisions from backend")

print()


# ============================================================
# Main simulation loop
# ============================================================

while True:

    current_time = time.time()


    # --------------------------------------------------------
    # Get control decisions
    # --------------------------------------------------------

    control_data = get_control_decisions()

    decisions = control_data.get(
        "decisions",
        []
    )


    # --------------------------------------------------------
    # Apply HOLD decisions
    # --------------------------------------------------------

    if CONTROL_MODE == "RULE_BASED":

        for decision in decisions:

            bus_id = decision["bus_id"]

            # Only start a new hold if the bus
            # is currently not being held.

            if bus_id not in hold_until:

                hold_seconds = decision["hold_seconds"]

                hold_until[bus_id] = (
                    current_time + hold_seconds
                )

                print(
                    f"[CONTROL] {bus_id} "
                    f"HOLD for {hold_seconds} seconds"
                )


    # --------------------------------------------------------
    # Update each bus
    # --------------------------------------------------------

    for bus in buses:

        bus_id = bus["bus_id"]


        # ====================================================
        # RULE-BASED CONTROL
        # ====================================================

        if CONTROL_MODE == "RULE_BASED":

            if bus_id in hold_until:

                if current_time < hold_until[bus_id]:

                    # Bus remains stopped
                    bus["speed"] = 0.0

                else:

                    # Hold completed
                    del hold_until[bus_id]

                    bus["speed"] = round(
                        random.uniform(0.6, 1.0),
                        2
                    )

                    print(
                        f"[CONTROL] {bus_id} "
                        f"HOLD completed"
                    )


        # ====================================================
        # MOVE BUS
        # ====================================================

        if bus_id not in hold_until:

            bus["speed"] = round(
                random.uniform(0.6, 1.0),
                2
            )

            bus["position"] += bus["speed"]


        # ====================================================
        # Route loop
        # ====================================================

        if bus["position"] >= len(STOPS):

            bus["position"] = 0.0


        # ====================================================
        # Passenger variation
        # ====================================================

        bus["passengers"] = max(
            0,
            bus["passengers"]
            + random.randint(-3, 3)
        )


    # ========================================================
    # Send live state to backend
    # ========================================================

    try:

        response = requests.post(
            API_URL,
            json={
                "buses": buses
            },
            timeout=2
        )

        if response.status_code != 200:

            print(
                "Backend update failed:",
                response.status_code
            )

    except requests.exceptions.RequestException as error:

        print(
            "Backend connection error:",
            error
        )


    # ========================================================
    # Display current state
    # ========================================================

    print("\nLIVE BUS STATUS")
    print("-" * 60)

    for bus in buses:

        if bus["speed"] == 0:

            status = "HOLDING"

        else:

            status = "MOVING"


        stop_index = int(
            bus["position"]
        ) % len(STOPS)


        print(
            f"{bus['bus_id']} | "
            f"Position: {bus['position']:.2f} | "
            f"Stop: {STOPS[stop_index]} | "
            f"Speed: {bus['speed']:.2f} | "
            f"Passengers: {bus['passengers']} | "
            f"{status}"
        )


    time.sleep(2)