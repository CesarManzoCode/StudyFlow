# StudyFlow

StudyFlow is a local web app that helps you turn Moodle assignments into a clear, manageable work plan.

Instead of jumping between Moodle, due dates, task descriptions, and AI chat tools, StudyFlow puts everything into one simple flow:

1. sync your pending tasks from Moodle
2. open a task
3. ask for AI help
4. get a structured checklist you can actually follow

This project is meant for end users who want less friction when organizing academic work, not for teams managing enterprise LMS integrations.

## What Problem It Solves

Moodle is useful, but in day-to-day use it often creates a very specific problem:

- tasks are scattered across courses
- deadlines are easy to miss
- assignment descriptions are often long or unclear
- you still have to manually translate "what Moodle says" into "what I should do next"
- if you use AI separately, you have to copy and paste context every time

StudyFlow solves that by connecting directly to Moodle, listing your pending tasks, and generating task-specific help from the assignment itself.

## Why Use StudyFlow

StudyFlow is useful if you want:

- one place to see pending tasks
- a faster way to understand what each assignment is asking for
- a practical checklist instead of a vague AI answer
- a local-first workflow where your configuration stays on your machine
- a lightweight tool focused on student execution, not project management overhead

## What You Can Do With It

- load your pending Moodle assignments
- review each task in a cleaner detail view
- ask the AI for help on a specific assignment
- get a response with:
  - summary
  - deliverable
  - steps
  - warnings
  - questions to clarify
  - final checklist
- save your Moodle and AI provider settings from the browser

## Who It Is For

StudyFlow is designed for:

- students who actively use Moodle
- people who struggle with turning assignment text into an action plan
- users who want AI help without manually re-explaining the task every time

It is especially useful when you have multiple pending assignments and want a more guided workflow than checking Moodle directly.

## Who It Is Not For

StudyFlow is probably not the right fit if:

- you do not use Moodle
- you want collaborative team features
- you want calendar sync, reminders, or mobile notifications
- you need a cloud dashboard shared across multiple users
- you want AI to complete work for you instead of helping you understand and execute it

## Main Idea

StudyFlow does not try to replace Moodle.

It solves the gap between:

- "the assignment exists in Moodle"
- and
- "I know exactly what to do next"

That is the core value of the program.

## How It Works

StudyFlow follows a simple user flow:

### 1. Open the app

Run:

```bash
python scripts/run.py
```

Then open:

```text
http://127.0.0.1:8000
```

### 2. Configure your account

Open the **Settings** page and fill in:

- Moodle base URL
- Moodle username
- Moodle password
- AI provider
- model
- API key or base URL, depending on the provider

When you save settings, the app reloads its internal configuration automatically.

### 3. Sync your tasks

On the dashboard, click **Refresh tasks**.

StudyFlow will log into Moodle and load pending assignments into the dashboard.

### 4. Open a task

Click any task card to open the detail page.

You will see:

- course name
- task status
- due date
- task description

### 5. Ask for AI help

Inside the task page, optionally write a custom question like:

- "give me a short plan"
- "explain what I need to deliver"
- "break this into small steps"
- "what should I clarify with the teacher?"

Then click **Generate checklist**.

### 6. Use the checklist to work

The AI output is structured so you can move from confusion to execution quickly.

## Supported AI Providers

StudyFlow supports:

- OpenAI
- Groq
- Ollama
- Anthropic

The exact model and credentials depend on the provider you choose.

## Why This Is Better Than Using Moodle Alone

Moodle tells you what exists.

StudyFlow helps you act on it.

The difference matters when:

- you are overloaded
- several assignments are pending at once
- task instructions are ambiguous
- you want fast interpretation, not just storage

## Why This Is Better Than Using a Generic AI Chat Separately

With a normal AI chat, you usually have to:

- open Moodle
- copy the assignment text
- paste it into an AI tool
- explain the context
- repeat that process for every task

StudyFlow reduces that friction because the task context already comes from Moodle.

## Tradeoffs

StudyFlow is intentionally simple, and that simplicity comes with tradeoffs.

### Benefits of this approach

- focused workflow
- local configuration
- very little setup inside the UI
- works around a real student pain point
- AI help is tied to a specific task, not a generic blank chat

### Limitations of this approach

- it depends on Moodle page structure
- if Moodle changes its HTML, syncing may need adjustments
- it is single-user and local-first
- it does not replace your judgment about assignment requirements
- AI responses can help interpret a task, but they can still be incomplete or wrong

## Important Expectations

StudyFlow helps you understand and organize your work.

It does not guarantee that:

- Moodle task text is complete
- the AI fully understands hidden teacher expectations
- a generated checklist is enough without reading the original assignment

The best way to use it is:

1. sync tasks
2. read the task
3. use the AI checklist to organize your approach
4. verify important details in Moodle before submitting

## Privacy and Local Use

StudyFlow is designed as a local-first tool.

- your settings are stored locally on your machine
- you access the app through your own browser
- Moodle credentials are used so the app can log in and fetch your assignments

If you use a cloud AI provider like OpenAI, Groq, or Anthropic, task content sent for AI help may leave your machine and be processed by that provider.

If you want a more local workflow, use Ollama with a local model.

## Best Use Cases

StudyFlow works especially well for:

- weekly assignment review
- planning before starting homework
- clarifying deliverables
- breaking large assignments into smaller actions
- deciding what to do first when several tasks are pending

## Example Daily Workflow

1. Open StudyFlow.
2. Click **Refresh tasks**.
3. Review the pending list.
4. Open the most urgent task.
5. Ask: "Give me a practical step-by-step plan."
6. Follow the generated checklist while completing the assignment.

## If Something Does Not Work

The most common issues are:

- Moodle login credentials are incorrect
- Playwright browsers are not installed
- the selected AI provider is missing credentials
- Moodle changed its page structure

If syncing works but AI help fails, the problem is usually provider configuration.

If the dashboard loads but tasks do not appear after refresh, the problem is usually Moodle access or scraping.

## Final Summary

StudyFlow is not a general productivity suite.

It is a focused tool for one specific problem:

turning Moodle assignments into an actionable plan with as little friction as possible.

If your real problem is not "I need a place to store tasks," but "I need help understanding what to do next," that is exactly where StudyFlow is useful.
