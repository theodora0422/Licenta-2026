function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function renderFindings(findings) {
    if (!findings || findings.length === 0) {
        return "<p>No findings available.</p>";
    }

    let html = "";
    let index = 0;

    while (index < findings.length) {
        const finding = findings[index];

        html += `
            <div class="finding-card">
                <p><strong>Type:</strong> ${escapeHtml(finding.type)}</p>
                <p><strong>Message:</strong> ${escapeHtml(finding.message)}</p>
                <p><strong>Location:</strong> ${escapeHtml(finding.location ?? "N/A")}</p>
            </div>
        `;

        index += 1;
    }

    return html;
}

function renderParsingSummary(parsing) {
    if (!parsing) {
        return "";
    }

    const diagnosticsCount = parsing.diagnostics ? parsing.diagnostics.length : 0;

    return `
        <div class="parsing-summary">
            <h4>Parsing Summary</h4>
            <p><strong>AST Root:</strong> ${escapeHtml(parsing.ast_root_type ?? "N/A")}</p>
            <p><strong>Syntax Errors:</strong> ${parsing.has_syntax_errors ? "Yes" : "No"}</p>
            <p><strong>Diagnostics:</strong> ${diagnosticsCount}</p>
        </div>
    `;
}

function renderResultsDashboard(data) {
    const container = document.getElementById("results-dashboard");

    if (!container) {
        console.error("Results dashboard container not found.");
        return;
    }

    const status = data.status ?? "unknown";
    const findings = data.findings ?? [];
    const parsing = data.parsing ?? null;

    container.innerHTML = `
        <div class="results-dashboard-block">
            <h3>Analysis Results</h3>
            <p><strong>Status:</strong> ${escapeHtml(status)}</p>
            ${renderParsingSummary(parsing)}
            <div class="findings-section">
                <h4>Findings</h4>
                ${renderFindings(findings)}
            </div>
        </div>
    `;
}

window.ResultsDashboard = {
    renderResultsDashboard
};