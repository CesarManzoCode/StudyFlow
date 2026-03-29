/**
 * Generate and display day plan
 */
async function generateDayPlan(triggerButton) {
  const container = document.getElementById('day-plan-container');
  const loading = document.getElementById('day-plan-loading');
  const error = document.getElementById('day-plan-error');
  const errorMsg = document.getElementById('day-plan-error-message');
  const result = document.getElementById('day-plan-result');
  const noTasks = document.getElementById('no-tasks-message');
  const plannedTasks = document.getElementById('planned-tasks');
  const button = triggerButton || document.querySelector('[data-day-plan-trigger]');

  if (!container || !loading || !error || !errorMsg || !result || !noTasks || !plannedTasks) {
    return;
  }

  setHidden(loading, false);
  setHidden(error, true);
  setHidden(result, true);
  setHidden(noTasks, true);

  if (button) {
    button.disabled = true;
    button.dataset.originalLabel = button.dataset.originalLabel || button.textContent.trim();
    button.textContent = 'Calculando plan...';
  }

  try {
    const response = await fetch('/api/plan/my-day');

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const plan = await response.json();

    plannedTasks.innerHTML = '';

    document.getElementById('plan-total-hours').textContent =
      plan.total_hours > 0 ? `${plan.total_hours}h` : '0h';
    document.getElementById('plan-task-count').textContent =
      plan.planned_tasks.length;
    document.getElementById('plan-feasible').textContent =
      plan.is_feasible ? 'Yes' : 'No';
    document.getElementById('plan-balance').textContent =
      plan.cognitive_balance || 'balanced';

    if (plan.planned_tasks.length === 0) {
      setHidden(noTasks, false);
    } else {
      plan.planned_tasks.forEach((task) => {
        const taskEl = createTaskElement(task);
        plannedTasks.appendChild(taskEl);
      });
    }

    setHidden(loading, true);
    setHidden(result, false);
  } catch (err) {
    console.error('Error generating day plan:', err);
    errorMsg.textContent = `No fue posible generar el plan: ${err.message}`;
    setHidden(loading, true);
    setHidden(error, false);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = button.dataset.originalLabel || 'Generar plan del dia';
    }
  }
}

/**
 * Create a task element for the plan
 */
function createTaskElement(task) {
  const div = document.createElement('div');
  div.className = 'planned-task';

  const difficultyClass = `task-badge--difficulty-${task.difficulty}`;
  const loadClass = `task-badge--load-${task.cognitive_load}`;

  div.innerHTML = `
    <div class="planned-task__sequence">${escapeHtml(String(task.sequence_position))}</div>
    <div class="planned-task__content">
      <div class="planned-task__header">
        <p class="planned-task__title">${escapeHtml(task.title)}</p>
        <span class="planned-task__time">${escapeHtml(task.formatted_time_block)}</span>
      </div>
      <p class="planned-task__course">${escapeHtml(task.course_name)}</p>
      <div class="planned-task__meta">
        <span class="task-badge task-badge--time">⏱ ${escapeHtml(task.formatted_time_block)}</span>
        <span class="task-badge ${difficultyClass}">
          Difficulty: ${escapeHtml(task.difficulty)}
        </span>
        <span class="task-badge ${loadClass}">
          Load: ${escapeHtml(task.cognitive_load)}
        </span>
      </div>
    </div>
  `;

  return div;
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
  const safeText = String(text ?? '');
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return safeText.replace(/[&<>"']/g, m => map[m]);
}

function setHidden(element, hidden) {
  if (element) {
    element.hidden = hidden;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const trigger = document.querySelector('[data-day-plan-trigger]');

  if (!trigger) {
    return;
  }

  trigger.addEventListener('click', () => {
    generateDayPlan(trigger);
  });
});

window.generateDayPlan = generateDayPlan;
