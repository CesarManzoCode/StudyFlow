/**
 * Enhanced AI help - load steps with time estimates and difficulty levels
 */

function getTaskId() {
  const match = window.location.pathname.match(/\/tasks\/([^/]+)/);
  return match ? match[1] : null;
}

async function loadEnhancedSteps(triggerButton) {
  const taskId = getTaskId();
  const container = document.getElementById('steps-container');
  const button = triggerButton || document.querySelector('[data-enhanced-steps-trigger]');

  if (!taskId || !container || !button) {
    console.error('Could not initialize enhanced step loader');
    return;
  }

  try {
    button.disabled = true;
    button.dataset.originalLabel = button.dataset.originalLabel || button.textContent.trim();
    button.textContent = 'Escaneando...';

    container.innerHTML = `
      <div class="panel-message panel-message--loading">
        <span class="panel-message__spinner"></span>
        <div>
          <p class="panel-message__title">Ejecutando cognitive scan</p>
          <p class="panel-message__text">Calculando dificultad, tiempo y primer paso minimo.</p>
        </div>
      </div>
    `;

    const response = await fetch(`/api/tasks/${taskId}/help/enhanced`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    renderEnhancedSteps(data);

    button.hidden = true;
  } catch (error) {
    console.error('Error loading enhanced steps:', error);
    container.innerHTML = `
      <div class="alert alert--error">
        <p class="alert__eyebrow">Enhanced Scan Error</p>
        <p class="alert__message">No fue posible cargar el escaneo avanzado: ${escapeHtml(error.message)}</p>
      </div>
    `;

    button.disabled = false;
    button.textContent = button.dataset.originalLabel || 'Escanear tiempos y dificultad';
  }
}

function renderEnhancedSteps(data) {
  const container = document.getElementById('steps-container');

  if (!container) {
    return;
  }

  let html = '';

  if (data.total_estimated_minutes) {
    html += `
      <div class="ai-estimate-summary">
        <span aria-hidden="true">[T]</span>
        <p>COGNITIVE OVERHEAD ESTIMATE: ${escapeHtml(String(data.total_estimated_minutes))} MIN</p>
      </div>
    `;
  }

  if (data.steps && data.steps.length > 0) {
    html += '<div class="ai-steps-grid">';

    data.steps.forEach((step, index) => {
      const isMinimal = step.is_minimal_first_step;
      const minimalClass = isMinimal ? 'ai-step-card--minimal' : '';
      const minimalBadge = isMinimal
        ? '<span class="ai-badge ai-badge--minimal">Start Here</span>'
        : '';

      const difficulty = String(step.difficulty || '').toLowerCase();
      const difficultyLabel = step.difficulty ? String(step.difficulty).toUpperCase() : 'UNKNOWN';
      let diffClass = 'ai-badge--moderate';

      if (difficulty === 'trivial' || difficulty === 'easy') {
        diffClass = 'ai-badge--easy';
      }

      if (difficulty === 'hard') {
        diffClass = 'ai-badge--hard';
      }

      html += `
        <div class="ai-step-card ${minimalClass}">
          <div class="ai-step-header">
            <div class="ai-step-icon">
              ${escapeHtml(step.effort_indicator || '>')}
            </div>
            <div class="ai-step-content">
              <div class="ai-step-title-row">
                <span class="ai-step-number">STEP_${String(index + 1).padStart(2, '0')}</span>
                ${minimalBadge}
              </div>
              <p class="ai-step-description">${escapeHtml(step.description)}</p>
              <div class="ai-step-meta">
                <span class="ai-badge ${diffClass}">
                  ${escapeHtml(difficultyLabel)}
                </span>
                <span class="ai-badge ai-badge--time">
                  [T] ${escapeHtml(step.formatted_time)}
                </span>
              </div>
            </div>
          </div>
        </div>
      `;
    });

    html += '</div>';
  } else {
    html += `
      <div class="empty-state empty-state--compact">
        <h3 class="empty-state__title">Sin pasos ejecutables</h3>
        <p class="empty-state__description">No se sintetizaron pasos accionables en el escaneo avanzado.</p>
      </div>
    `;
  }

  container.innerHTML = html;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = String(text ?? '');
  return div.innerHTML;
}

document.addEventListener('DOMContentLoaded', () => {
  const button = document.querySelector('[data-enhanced-steps-trigger]');

  if (!button) {
    return;
  }

  button.addEventListener('click', () => {
    loadEnhancedSteps(button);
  });
});

window.loadEnhancedSteps = loadEnhancedSteps;
