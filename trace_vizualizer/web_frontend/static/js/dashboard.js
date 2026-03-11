function renderAnalysisResults(data) {
    const resultsContainer = document.getElementById("results");

    const findingsHtml = data.findings.length
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

    const scenarioHtml = data.scenario.length
        ? `
            <ol>
                ${data.scenario.map(step => `
                    <li>
                        <strong>Thread:</strong> ${step.thread},
                        <strong>Action:</strong> ${step.action},
                        <strong>Resource:</strong> ${step.resource ?? "N/A"}
                    </li>
                `).join("")}
            </ol>
        `
        : "<p>No scenario steps available.</p>";

    resultsContainer.innerHTML = `
        <div>
            <h3>Status</h3>
            <p>${data.status}</p>

            <h3>Explanation</h3>
            <p>${data.explanation}</p>

            <h3>Findings</h3>
            ${findingsHtml}

            <h3>Scenario</h3>
            ${scenarioHtml}
        </div>
    `;
}

window.renderAnalysisResults = renderAnalysisResults;