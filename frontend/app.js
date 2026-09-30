const API_BASE = "http://127.0.0.1:8000";


// ===============================
// Load all dashboard data
// ===============================

async function loadDashboard() {

    try {

        const [busResponse, bunchingResponse, controlResponse] =
            await Promise.all([
                fetch(`${API_BASE}/bus-status`),
                fetch(`${API_BASE}/detect-bunching`),
                fetch(`${API_BASE}/control-decisions`)
            ]);


        const busData = await busResponse.json();
        const bunchingData = await bunchingResponse.json();
        const controlData = await controlResponse.json();


        updateBusStatus(busData);
        updateBunchingAlerts(bunchingData);
        updateControlDecisions(controlData);

        updateSystemStatus(controlData);

        document.getElementById("last-update").textContent =
            new Date().toLocaleTimeString();

    }

    catch (error) {

        console.error("Backend connection error:", error);

        document.getElementById("system-status").textContent =
            "BACKEND OFFLINE";

        document.getElementById("system-status").className =
            "status warning";

    }
}



// ===============================
// Update bus table
// ===============================

function updateBusStatus(data) {

    const table = document.getElementById("bus-table");

    table.innerHTML = "";

    document.getElementById("total-buses").textContent =
        data.buses.length;


    data.buses.forEach(bus => {

        const row = document.createElement("tr");

        row.innerHTML = `
            <td><strong>${bus.bus_id}</strong></td>

            <td>
                ${Number(bus.position).toFixed(2)}
            </td>

            <td>
                ${Number(bus.speed).toFixed(2)}
            </td>

            <td>
                ${bus.passengers}
            </td>

            <td class="bus-normal">
                ACTIVE
            </td>
        `;

        table.appendChild(row);

    });

}



// ===============================
// Update bunching alerts
// ===============================

function updateBunchingAlerts(data) {

    const container =
        document.getElementById("alerts-container");

    container.innerHTML = "";


    document.getElementById("total-alerts").textContent =
        data.alerts.length;


    if (data.alerts.length === 0) {

        container.innerHTML =
            "<p>No bus bunching detected.</p>";

        return;
    }


    data.alerts.forEach(alert => {

        const element =
            document.createElement("div");

        element.className = "alert";


        element.innerHTML = `
            <strong>
                ${alert.status}
            </strong>

            <p>
                Bus <b>${alert.bus_id}</b>
                is close to
                Bus <b>${alert.following_bus}</b>.
            </p>

            <p>
                Headway:
                <b>${alert.headway}</b> stops
            </p>

            <p>
                Severity:
                <b>${alert.severity}</b>
            </p>

            <p>
                Recommendation:
                <b>${alert.recommendation}</b>
                for
                <b>${alert.hold_seconds} seconds</b>
            </p>
        `;

        container.appendChild(element);

    });

}



// ===============================
// Update control decisions
// ===============================

function updateControlDecisions(data) {

    const container =
        document.getElementById("decisions-container");

    container.innerHTML = "";


    document.getElementById("total-interventions").textContent =
        data.decisions.length;


    if (data.decisions.length === 0) {

        container.innerHTML =
            "<p>No control intervention required.</p>";

        return;
    }


    data.decisions.forEach(decision => {

        const element =
            document.createElement("div");

        element.className = "decision";


        element.innerHTML = `
            <p>
                <b>${decision.bus_id}</b>
                →
                ${decision.following_bus}
            </p>

            <p>
                Severity:
                <b>${decision.severity}</b>
            </p>

            <p class="hold">
                ACTION:
                ${decision.action}
                ${decision.hold_seconds} seconds
            </p>

            <p>
                ${decision.reason}
            </p>
        `;

        container.appendChild(element);

    });

}



// ===============================
// System status
// ===============================

function updateSystemStatus(data) {

    const status =
        document.getElementById("system-status");


    if (data.status === "NORMAL") {

        status.textContent =
            "SYSTEM NORMAL";

        status.className =
            "status normal";

    }

    else {

        status.textContent =
            "INTERVENTION REQUIRED";

        status.className =
            "status warning";

    }

}



// ===============================
// Auto refresh
// ===============================

loadDashboard();

setInterval(loadDashboard, 2000);