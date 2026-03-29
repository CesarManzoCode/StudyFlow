/**
 * Generate and display day plan
 */
async function generateDayPlan() {
  const container = document.getElementById('day-plan-container');
  const loading = document.getElementById('day-plan-loading');
  const error = document.getElementById('day-plan-error');
  const errorMsg = document.getElementById('day-plan-error-message');
  const result = document.getElementById('day-plan-result');
  const noTasks = document.getElementById('no-tasks-message');
  const plannedTasks = document.getElementById('planned-tasks');

  // Show loading state
  loading.style.display = 'block';
  error.style.display = 'none';
  result.style.display = 'none';

  try {
    // Call the API
    const response = await fetch('/api/plan/my-day');

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const plan = await response.json();

    // Clear previous results
    plannedTasks.innerHTML = '';

    // Update summary stats
    document.getElementById('plan-total-hours').textContent = 
      plan.total_hours > 0 ? `${plan.total_hours}h` : '0h';
    document.getElementById('plan-task-count').textContent = 
      plan.planned_tasks.length;
    document.getElementById('plan-feasible').textContent = 
      plan.is_feasible ? '✓ Yes' : '✗ No';
    document.getElementById('plan-balance').textContent = 
      plan.cognitive_balance || 'balanced';

    // Render tasks or empty state
    if (plan.planned_tasks.length === 0) {
      noTasks.style.display = 'block';
    } else {
      noTasks.style.display = 'none';

      // Render each task
      plan.planned_tasks.forEach((task) => {
        const taskEl = createTaskElement(task);
        plannedTasks.appendChild(taskEl);
      });
    }

    // Show results
    loading.style.display = 'none';
    result.style.display = 'block';

  } catch (err) {
    console.error('Error generating day plan:', err);
    errorMsg.textContent = `Failed to generate plan: ${err.message}`;
    loading.style.display = 'none';
    error.style.display = 'block';
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
    <div class="task-sequence">${task.sequence_position}</div>
    <div class="task-content">
      <p class="task-title">${escapeHtml(task.title)}</p>
      <p class="task-course">${escapeHtml(task.course_name)}</p>
      <div class="task-meta">
        <span class="task-badge task-badge--time">⏱ ${task.formatted_time_block}</span>
        <span class="task-badge ${difficultyClass}">
          Difficulty: ${task.difficulty}
        </span>
        <span class="task-badge ${loadClass}">
          Load: ${task.cognitive_load}
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
  const map = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#039;'
  };
  return text.replace(/[&<>"']/g, m => map[m]);
}

// Export for use in HTML
window.generateDayPlan = generateDayPlan;
