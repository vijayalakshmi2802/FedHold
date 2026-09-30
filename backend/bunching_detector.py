BUNCHING_THRESHOLD = 2.0


def detect_bunching(buses):

    alerts = []

    sorted_buses = sorted(
        buses,
        key=lambda x: x["position"]
    )

    for i in range(len(sorted_buses) - 1):

        current_bus = sorted_buses[i]
        next_bus = sorted_buses[i + 1]

        headway = (
            next_bus["position"]
            - current_bus["position"]
        )

        if headway < 0:
            continue

        if headway <= BUNCHING_THRESHOLD:

            if headway <= 0.5:
                severity = "CRITICAL"
                hold_seconds = 60

            elif headway <= 1.0:
                severity = "HIGH"
                hold_seconds = 45

            elif headway <= 1.5:
                severity = "MEDIUM"
                hold_seconds = 30

            else:
                severity = "LOW"
                hold_seconds = 15

            alerts.append({

                "bus_id": current_bus["bus_id"],

                "following_bus":
                    next_bus["bus_id"],

                "headway":
                    round(headway, 2),

                "severity":
                    severity,

                "status":
                    "BUNCHING DETECTED",

                "recommendation":
                    "HOLD",

                "hold_seconds":
                    hold_seconds
            })

    return alerts