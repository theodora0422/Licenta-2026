async function analyzeCode() {
    const dashboardContainer = document.getElementById("results-dashboard");
    const explanationContainer = document.getElementById("explanation-view");
    const scenarioContainer = document.getElementById("scenario-visualizer");

    try {
        const requestBody = window.RequestBuilder.buildAnalysisRequest();

        if (dashboardContainer) {
            dashboardContainer.innerHTML = "<p>Running analysis...</p>";
        }

        if (explanationContainer) {
            explanationContainer.innerHTML = "";
        }

        if (scenarioContainer) {
            scenarioContainer.innerHTML = "";
        }

        const response = await fetch("/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }

        const data = await response.json();

        window.ResultsDashboard.renderResultsDashboard(data);
        window.ExplanationView.renderExplanationView(data);
        window.ScenarioVisualizer.renderScenarioVisualizer(data);
    } catch (error) {
        console.error("Analysis request failed:", error);

        if (dashboardContainer) {
            dashboardContainer.innerHTML = `<p>Request failed: ${error.message}</p>`;
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (window.CodeInputModule) {
        window.CodeInputModule.initializeCodeInput();
    }

    const analyzeButton = document.getElementById("analyze-btn");

    if (!analyzeButton) {
        console.error("Analyze button not found.");
        return;
    }

    analyzeButton.addEventListener("click", analyzeCode);
});