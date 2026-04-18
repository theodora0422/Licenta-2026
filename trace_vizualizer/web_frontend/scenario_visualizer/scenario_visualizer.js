function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function buildLegacyGraphElementsFromScenario(scenario) {
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
                nodeType: nodeType,
                highlighted: false
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
                edgeType: edgeType,
                highlighted: false
            }
        });
    }

    let index = 0;
    while (index < scenario.length) {
        const step = scenario[index];
        const threadId = "thread-" + step.thread;
        addNode(threadId, step.thread, "thread");

        if (step.resource) {
            const resourceId = "resource-" + step.resource;
            addNode(resourceId, step.resource, "resource");

            const action = step.action || "generic";

            addEdge(
                "edge-" + index + "-" + threadId + "-" + resourceId + "-" + action,
                threadId,
                resourceId,
                action,
                action
            );
        }

        index += 1;
    }

    return elements;
}

function buildGraphElementsFromVisualization(visualization) {
    const elements = [];
    const graphNodes = visualization?.graph_nodes ?? [];
    const graphEdges = visualization?.graph_edges ?? [];

    let index = 0;
    while (index < graphNodes.length) {
        const node = graphNodes[index];
        elements.push({
            data: {
                id: node.id,
                label: node.label,
                nodeType: node.node_type,
                highlighted: !!node.highlighted
            }
        });
        index += 1;
    }

    index = 0;
    while (index < graphEdges.length) {
        const edge = graphEdges[index];
        elements.push({
            data: {
                id: edge.id,
                source: edge.source,
                target: edge.target,
                label: edge.label,
                edgeType: edge.edge_type,
                highlighted: !!edge.highlighted
            }
        });
        index += 1;
    }

    return elements;
}

function renderScenarioStepsFromLegacyScenario(scenario) {
    if (!scenario || scenario.length === 0) {
        return "<p>No scenario steps available.</p>";
    }

    let itemsHtml = "";
    let index = 0;

    while (index < scenario.length) {
        const step = scenario[index];
        itemsHtml += `
            <li>
                <strong>Thread:</strong> ${escapeHtml(step.thread)},
                <strong>Action:</strong> ${escapeHtml(step.action)},
                <strong>Resource:</strong> ${escapeHtml(step.resource ?? "N/A")}
            </li>
        `;
        index += 1;
    }

    return `
        <div class="scenario-steps-block">
            <h4>Scenario Steps</h4>
            <ol class="scenario-step-list">
                ${itemsHtml}
            </ol>
        </div>
    `;
}

function renderTimelineFromVisualization(visualization) {
    const timeline = visualization?.timeline ?? [];

    if (!timeline.length) {
        return "<p>No timeline items available.</p>";
    }

    const highlightIds = new Set();
    const markers = visualization?.highlights ?? [];

    let markerIndex = 0;
    while (markerIndex < markers.length) {
        const marker = markers[markerIndex];
        if (marker.target_type === "timeline") {
            highlightIds.add(marker.target_id);
        }
        markerIndex += 1;
    }

    let itemsHtml = "";
    let index = 0;

    while (index < timeline.length) {
        const item = timeline[index];
        const itemId = "timeline-step:" + item.step_index;
        const highlightedClass = highlightIds.has(itemId) ? "timeline-step-highlighted" : "";
        const derivedBadge = item.derived ? `<span class="derived-badge">derived</span>` : "";

        itemsHtml += `
            <li class="${highlightedClass}">
                <strong>Step ${item.step_index}:</strong>
                <strong>Thread:</strong> ${escapeHtml(item.thread_id)},
                <strong>Action:</strong> ${escapeHtml(item.action)},
                <strong>Resource:</strong> ${escapeHtml(item.resource ?? "N/A")}
                ${item.line ? `, <strong>Line:</strong> ${item.line}` : ""}
                ${derivedBadge}
            </li>
        `;

        index += 1;
    }

    return `
        <div class="scenario-steps-block">
            <h4>Scenario Timeline</h4>
            <ol class="scenario-step-list">
                ${itemsHtml}
            </ol>
        </div>
    `;
}

function drawScenarioGraph(elements) {
    const graphContainer = document.getElementById("scenario-graph");

    if (!graphContainer) {
        console.error("Scenario graph container not found.");
        return;
    }

    if (typeof window.cytoscape === "undefined") {
        console.error("Cytoscape is not available.");
        return;
    }

    window.cytoscape({
        container: graphContainer,
        elements: elements,
        style: [
            {
                selector: "node",
                style: {
                    label: "data(label)",
                    "text-valign": "center",
                    "text-halign": "center",
                    "font-size": 12,
                    width: 54,
                    height: 54
                }
            },
            {
                selector: 'node[nodeType="thread"]',
                style: {
                    shape: "roundrectangle",
                    "background-color": "#2563eb",
                    color: "#ffffff"
                }
            },
            {
                selector: 'node[nodeType="resource"]',
                style: {
                    shape: "ellipse",
                    "background-color": "#7c3aed",
                    color: "#ffffff"
                }
            },
            {
                selector: "node[highlighted = true]",
                style: {
                    "border-width": 4,
                    "border-color": "#f59e0b"
                }
            },
            {
                selector: "edge",
                style: {
                    "curve-style": "bezier",
                    "target-arrow-shape": "triangle",
                    label: "data(label)",
                    "font-size": 10,
                    "text-background-opacity": 1,
                    "text-background-color": "#ffffff",
                    "text-background-padding": 2,
                    "text-rotation": "autorotate",
                    width: 2,
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
            },
            {
                selector: "edge[highlighted = true]",
                style: {
                    width: 4,
                    "line-color": "#f59e0b",
                    "target-arrow-color": "#f59e0b"
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

    const visualization = data.visualization;
    const legacyScenario = data.scenario ?? [];

    if (visualization) {
        const elements = buildGraphElementsFromVisualization(visualization);

        container.innerHTML = `
            <div class="scenario-visualizer-block">
                <h3>Scenario Visualization</h3>
                <div id="scenario-graph"></div>
                ${renderTimelineFromVisualization(visualization)}
            </div>
        `;

        drawScenarioGraph(elements);
        return;
    }

    const elements = buildLegacyGraphElementsFromScenario(legacyScenario);

    container.innerHTML = `
        <div class="scenario-visualizer-block">
            <h3>Scenario Visualization</h3>
            <div id="scenario-graph"></div>
            ${renderScenarioStepsFromLegacyScenario(legacyScenario)}
        </div>
    `;

    if (!legacyScenario.length) {
        return;
    }

    drawScenarioGraph(elements);
}

window.ScenarioVisualizer = {
    renderScenarioVisualizer
};