/**
 * Enhanced AI help - load steps with time estimates and difficulty levels
 */

function getTaskId() {
    const match = window.location.pathname.match(/\/tasks\/([^/]+)/);
    return match ? match[1] : null;
}

async function loadEnhancedSteps() {
    const taskId = getTaskId();
    if (!taskId) {
        console.error("Could not determine task ID");
        return;
    }

    try {
        const button = event.target;
        button.disabled = true;
        button.innerHTML = "<span style='animation: pulse 1.5s infinite'>Initializing cognitive scan...</span>";

        const response = await fetch(`/api/tasks/${taskId}/help/enhanced`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        const data = await response.json();
        renderEnhancedSteps(data);

        button.style.display = "none";
    } catch (error) {
        console.error("Error loading enhanced steps:", error);
        alert("System failure: Could not load cognitive scan. Retrying or contacting admin is advised.");
        event.target.disabled = false;
        event.target.textContent = "Initiate Override Scan";
    }
}

function renderEnhancedSteps(data) {
    const container = document.getElementById("steps-container");

    let html = "";

    // Show total estimated time
    if (data.total_estimated_minutes) {
        html += `
            <div class="ai-estimate-summary">
                <span style="font-size: 1.5rem">⏱️</span>
                <p>COGNITIVE OVERHEAD ESTIMATE: ${data.total_estimated_minutes} MIN</p>
            </div>
        `;
    }

    // Render each step
    if (data.steps && data.steps.length > 0) {
        html += '<div class="ai-steps-grid">';

        data.steps.forEach((step, index) => {
            const isMinimal = step.is_minimal_first_step;
            const minimalClass = isMinimal ? "ai-step-card--minimal" : "";
            const minimalBadge = isMinimal 
                ? '<span class="ai-badge ai-badge--minimal">START HERE</span>' 
                : "";

            const difficulty = step.difficulty.toLowerCase();
            let diffClass = "ai-badge--moderate";
            if (difficulty === "trivial" || difficulty === "easy") diffClass = "ai-badge--easy";
            if (difficulty === "hard") diffClass = "ai-badge--hard";

            html += `
                <div class="ai-step-card ${minimalClass}">
                    <div class="ai-step-header">
                        <div class="ai-step-icon">
                            ${step.effort_indicator}
                        </div>
                        <div class="ai-step-content">
                            <div class="ai-step-title-row">
                                <span class="ai-step-number">STEP_0${index + 1}</span>
                                ${minimalBadge}
                            </div>
                            <p class="ai-step-description">${escapeHtml(step.description)}</p>
                            
                            <div class="ai-step-meta">
                                <span class="ai-badge ${diffClass}">
                                    ${step.difficulty.toUpperCase()}
                                </span>
                                <span class="ai-badge ai-badge--time">
                                    [T] ${step.formatted_time}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        html += "</div>";
    } else {
        html += '<div class="empty-state"><p class="empty-state__description">No executable steps synthesized.</p></div>';
    }

    // Small fade-in effect when elements appear
    container.style.opacity = 0;
    container.innerHTML = html;
    
    // Trigger reflow and fade in
    void container.offsetWidth;
    container.style.transition = "opacity 0.6s ease-in-out";
    container.style.opacity = 1;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
