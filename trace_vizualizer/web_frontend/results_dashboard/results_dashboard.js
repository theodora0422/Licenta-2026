function renderResultsDashboard(data) {
    const container = document.getElementById("results-dashboard");

    if (!container) {
        console.error("Results dashboard container not found.");
        return;
    }

    const findingsHtml = data.findings && data.findings.length > 0
        ? `
            <ul>
                ${data.findings.map(finding => `
                    <li>
                        <strong>Type:</strong> ${finding.type}<br>
                        <strong>Message:</strong> ${finding.message}<br>
                        <strong>Location:</strong> ${finding.location ?? "N/A"}
                    </li>
                `).join("")}
            </ul>
        `
        : "<p>No findings reported.</p>";

    container.innerHTML = `
        <div class="results-dashboard-block">
            <h3>Status</h3>
            <p>${data.status}</p>

            <h3>Findings</h3>
            ${findingsHtml}
        </div>
    `;
}

window.ResultsDashboard = {
    renderResultsDashboard
};