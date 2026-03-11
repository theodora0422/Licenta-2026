function buildGraphElementsFromScenario(scenario) {
    const elements = [];
    const addedNodes = new Set();
    const addedEdges = new Set();

    function addNode(id, label, nodeType) {
        if (addedNodes.has(id)) {
            return;
        }

        addedNodes.add(id);

        elements.push({
            data: {
                id: id,
                label: label,
                nodeType: nodeType
            }
        });
    }

    function addEdge(id, source, target, label, edgeType) {
        if (addedEdges.has(id)) {
            return;
        }

        addedEdges.add(id);

        elements.push({
            data: {
                id: id,
                source: source,
                target: target,
                label: label,
                edgeType: edgeType
            }
        });
    }

    scenario.forEach((step, index) => {
        const threadId = `thread-${step.thread}`;
        addNode(threadId, step.thread, "thread");

        if (step.resource) {
            const resourceId = `resource-${step.resource}`;
            addNode(resourceId, step.resource, "resource");

            const action = step.action || "generic";

            addEdge(
                `edge-${index}-${threadId}-${resourceId}-${action}`,
                threadId,
                resourceId,
                action,
                action
            );
        }
    });

    return elements;
}

function renderScenarioSteps(scenario) {
    if (!scenario || scenario.length === 0) {
        return "<p>No scenario steps available.</p>";
    }

    return `
        <div class="scenario-steps-block">
            <h4>Scenario Steps</h4>
            <ol class="scenario-step-list">
                ${scenario.map(step => `
                    <li>
                        <strong>Thread:</strong> ${step.thread},
                        <strong>Action:</strong> ${step.action},
                        <strong>Resource:</strong> ${step.resource ?? "N/A"}
                    </li>
                `).join("")}
            </ol>
        </div>
    `;
}

function drawScenarioGraph(scenario) {
    const graphContainer = document.getElementById("scenario-graph");

    if (!graphContainer) {
        console.error("Scenario graph container not found.");
        return;
    }

    if (typeof window.cytoscape === "undefined") {
        console.error("Cytoscape is not available.");
        return;
    }

    const elements = buildGraphElementsFromScenario(scenario);

    window.cytoscape({
        container: graphContainer,
        elements: elements,
        style: [
            {
                selector: "node",
                style: {
                    "label": "data(label)",
                    "text-valign": "center",
                    "text-halign": "center",
                    "font-size": 12,
                    "width": 54,
                    "height": 54
                }
            },
            {
                selector: 'node[nodeType="thread"]',
                style: {
                    "shape": "roundrectangle",
                    "background-color": "#2563eb",
                    "color": "#ffffff"
                }
            },
            {
                selector: 'node[nodeType="resource"]',
                style: {
                    "shape": "ellipse",
                    "background-color": "#7c3aed",
                    "color": "#ffffff"
                }
            },
            {
                selector: "edge",
                style: {
                    "curve-style": "bezier",
                    "target-arrow-shape": "triangle",
                    "label": "data(label)",
                    "font-size": 10,
                    "text-background-opacity": 1,
                    "text-background-color": "#ffffff",
                    "text-background-padding": 2,
                    "text-rotation": "autorotate",
                    "width": 2,
                    "line-color": "#94a3b8",
                    "target-arrow-color": "#94a3b8"
                }
            },
            {
                selector: 'edge[edgeType="acquire"]',
                style: {
                    "line-color": "#16a34a",
                    "target-arrow-color": "#16a34a"
                }
            },
            {
                selector: 'edge[edgeType="wait"]',
                style: {
                    "line-style": "dashed",
                    "line-color": "#dc2626",
                    "target-arrow-color": "#dc2626"
                }
            },
            {
                selector: 'edge[edgeType="release"]',
                style: {
                    "line-color": "#ea580c",
                    "target-arrow-color": "#ea580c"
                }
            }
        ],
        layout: {
            name: "cose",
            animate: false,
            fit: true,
            padding: 30
        }
    });
}

function renderScenarioVisualizer(data) {
    const container = document.getElementById("scenario-visualizer");

    if (!container) {
        console.error("Scenario visualizer container not found.");
        return;
    }

    const scenario = data.scenario ?? [];

    container.innerHTML = `
        <div class="scenario-visualizer-block">
            <h3>Scenario Visualization</h3>
            <div id="scenario-graph"></div>
            ${renderScenarioSteps(scenario)}
        </div>
    `;

    if (!scenario.length) {
        return;
    }

    drawScenarioGraph(scenario);
}

window.ScenarioVisualizer = {
    renderScenarioVisualizer
};