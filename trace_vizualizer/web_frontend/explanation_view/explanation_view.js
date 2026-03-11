function renderExplanationView(data) {
    const container = document.getElementById("explanation-view");

    if (!container) {
        console.error("Explanation view container not found.");
        return;
    }

    const explanationText = data.explanation
        ? data.explanation
        : "No explanation available.";

    container.innerHTML = `
        <div class="explanation-view-block">
            <h3>Explanation</h3>
            <p>${explanationText}</p>
        </div>
    `;
}

window.ExplanationView = {
    renderExplanationView
};