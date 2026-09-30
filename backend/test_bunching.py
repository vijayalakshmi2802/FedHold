from bunching_detector import detect_bunching


buses = [
    {
        "bus_id": "BUS-101",
        "position": 2.0
    },
    {
        "bus_id": "BUS-102",
        "position": 3.0
    },
    {
        "bus_id": "BUS-103",
        "position": 7.0
    },
    {
        "bus_id": "BUS-104",
        "position": 8.0
    }
]


alerts = detect_bunching(buses)


print("\nFEDHOLD BUNCHING DETECTION")
print("=" * 50)

for alert in alerts:
    print(alert)