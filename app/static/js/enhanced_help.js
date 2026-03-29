/**
 * Enhanced AI help - load steps with time estimates and difficulty levels
 */

/**
 * Extract task ID from the current URL
 */
function getTaskId() {
    const match = window.location.pathname.match(/\/tasks\/([^/]+)/);
    return match ? match[1] : null;
}

/**
 * Load enhanced steps with time and difficulty information
 */
async function loadEnhancedSteps() {
    const taskId = getTaskId();
    if (!taskId) {
        console.error("Could not determine task ID");
        return;
    }

    try {
        const button = event.target;
        button.disabled = true;
        button.textContent = "Loading...";

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
        alert("Failed to load enhanced step information");
        event.target.disabled = false;
        event.target.textContent = "Load with estimates";
    }
}

/**
 * Render enhanced steps with time and difficulty information
 */
function renderEnhancedSteps(data) {
    const container = document.getElementById("steps-container");

    let html = "";

    // Show total estimated time
    if (data.total_estimated_minutes) {
        html += `
            <div style="background: #f0f4f8; border-left: 4px solid #3b82f6; padding: 1rem; margin-bottom: 1rem; border-radius: 4px;">
                <p style="margin: 0; font-weight: 600; color: #1e40af;">
                    ⏱️ Total estimated time: ${data.total_estimated_minutes} minutes
                </p>
            </div>
        `;
    }

    // Render each step
    if (data.steps && data.steps.length > 0) {
        html += '<div style="space-y: 0.5rem;">';

        data.steps.forEach((step, index) => {
            const isMinimal = step.is_minimal_first_step;
            const minimalBadge = isMinimal
                ? '<span style="background: #fbbf24; color: #78350f; padding: 0.25rem 0.75rem; border-radius: 4px; font-size: 0.875rem; margin-left: 0.5rem; font-weight: 600;">START HERE</span>'
                : "";

            const difficultyColors = {
                trivial: { bg: "#d1fae5", text: "#065f46", emoji: "⚡" },
                easy: { bg: "#dcfce7", text: "#166534", emoji: "✓" },
                moderate: { bg: "#fef3c7", text: "#92400e", emoji: "●" },
                hard: { bg: "#fee2e2", text: "#991b1b", emoji: "⚠" },
            };

            const difficulty = step.difficulty.toLowerCase();
            const colors = difficultyColors[difficulty] || difficultyColors.moderate;

            html += `
                <div style="
                    border: 1px solid #e5e7eb;
                    border-radius: 8px;
                    padding: 1rem;
                    margin-bottom: 0.75rem;
                    ${isMinimal ? "background: #fffbeb; border-left: 4px solid #f59e0b;" : ""}
                ">
                    <div style="display: flex; align-items: flex-start; gap: 1rem; margin-bottom: 0.75rem;">
                        <div style="
                            font-size: 1.5rem;
                            line-height: 1;
                            flex-shrink: 0;
                        ">
                            ${step.effort_indicator}
                        </div>
                        <div style="flex: 1; min-width: 0;">
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                                <span style="font-weight: 600; color: #1f2937;">
                                    Step ${index + 1}
                                </span>
                                ${minimalBadge}
                            </div>
                            <p style="margin: 0; color: #374151; line-height: 1.5;">
                                ${escapeHtml(step.description)}
                            </p>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                        <div style="
                            background: ${colors.bg};
                            color: ${colors.text};
                            padding: 0.5rem 0.75rem;
                            border-radius: 4px;
                            font-size: 0.875rem;
                            font-weight: 500;
                        ">
                            ${step.difficulty.charAt(0).toUpperCase() + step.difficulty.slice(1)}
                        </div>
                        <div style="
                            background: #f3f4f6;
                            color: #374151;
                            padding: 0.5rem 0.75rem;
                            border-radius: 4px;
                            font-size: 0.875rem;
                            font-weight: 500;
                        ">
                            ${step.formatted_time}
                        </div>
                    </div>
                </div>
            `;
        });

        html += "</div>";
    } else {
        html += '<p class="helper-text">No steps available.</p>';
    }

    container.innerHTML = html;
}

/**
 * Escape HTML special characters to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}
