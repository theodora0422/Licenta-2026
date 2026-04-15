function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function renderLegacyExplanation(data) {
    const explanation = data.explanation ?? "No explanation available.";
    return `
        <div class="explanation-block">
            <h3>Explanation</h3>
            <p>${escapeHtml(explanation)}</p>
        </div>
    `;
}

function renderStructuredExplanation(structuredExplanation) {
    const title = structuredExplanation?.title ?? "Explanation";
    const summary = structuredExplanation?.summary ?? "";
    const detailedSteps = structuredExplanation?.detailed_steps ?? [];
    const sourceReferences = structuredExplanation?.source_references ?? [];

    const stepsHtml = detailedSteps.length
        ? `
            <div class="explanation-steps">
                <h4>Detailed Steps</h4>
                <ol class="explanation-step-list">
                    ${detailedSteps.map(step => `
                        <li>${escapeHtml(step)}</li>
                    `).join("")}
                </ol>
            </div>
        `
        : "";

    const referencesHtml = sourceReferences.length
        ? `
            <div class="source-references">
                <h4>Source References</h4>
                <ul class="source-reference-list">
                    ${sourceReferences.map(reference => `
                        <li>
                            <strong>Line ${reference.line}</strong>
                            ${reference.thread ? ` | <strong>Thread:</strong> ${escapeHtml(reference.thread)}` : ""}
                            ${reference.action ? ` | <strong>Action:</strong> ${escapeHtml(reference.action)}` : ""}
                            ${reference.resource ? ` | <strong>Resource:</strong> ${escapeHtml(reference.resource)}` : ""}
                            ${reference.code_snippet ? `
                                <pre class="source-code-snippet"><code>${escapeHtml(reference.code_snippet)}</code></pre>
                            ` : ""}
                        </li>
                    `).join("")}
                </ul>
            </div>
        `
        : "";

    return `
        <div class="explanation-block">
            <h3>${escapeHtml(title)}</h3>
            <p>${escapeHtml(summary)}</p>
            ${stepsHtml}
            ${referencesHtml}
        </div>
    `;
}

function renderExplanationView(data) {
    const container = document.getElementById("explanation-view");

    if (!container) {
        console.error("Explanation view container not found.");
        return;
    }

    const structuredExplanation = data.structured_explanation;

    if (structuredExplanation) {
        container.innerHTML = renderStructuredExplanation(structuredExplanation);
        return;
    }

    container.innerHTML = renderLegacyExplanation(data);
}

window.ExplanationView = {
    renderExplanationView
};