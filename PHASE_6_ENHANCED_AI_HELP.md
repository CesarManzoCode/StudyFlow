# Phase 6: Enhanced AI Help Output - Feature Documentation

## Overview

Enhanced AI help provides step-level metadata (time estimates, difficulty, minimal first step) to help users overcome procrastination by showing exactly what they're signing up for.

**Psychology Insight**: "I can spend 5 minutes on step 1" is psychologically easier than "I need to write an essay" - concrete time commitment reduces activation friction.

## Features Implemented

### 1. **Step Time Estimation** ⏱️
Each step includes an estimated time in minutes (1-120).

**Heuristic Rules:**
- Keywords trigger time estimates:
  - "open", "click", "close", "view" → 1 minute (trivial effort)
  - "review", "check", "copy", "paste" → 3 minutes (easy)
  - "write", "edit", "create", "prepare" → 10 minutes (moderate)
  - "develop", "implement", "design", "solve" → 20 minutes (hard)
  
**Example:**
```
⚡ 1 min - Open the assignment document
✓ 3 min - Review the requirements
● 10 min - Write the introduction
● 15 min - Write the main body
● 5 min - Review and proofread
─────────────────────────────────
⏱️ Total: 34 minutes
```

### 2. **Difficulty Levels** 📊
Four difficulty tiers with visual indicators:

| Difficulty | Emoji | Time Budget | Use Case |
|-----------|-------|------------|----------|
| TRIVIAL   | ⚡    | < 1 min    | Pure mechanical steps (click, open) |
| EASY      | ✓     | 1-5 min    | Light thinking required |
| MODERATE  | ●     | 5-15 min   | Some analysis/writing needed |
| HARD      | ⚠     | 15+ min    | Deep thinking/complex work |

**Visual UI:**
- Color-coded badges next to each step
- Effort emoji provides quick scan-ability
- Time estimate in compact format

### 3. **"Minimal First Step" Highlight** ⭐
The first step is automatically marked as "START HERE" with special formatting.

**Why This Matters:**
- Overcomes "task paralysis" - users see the smallest possible commitment
- First 5 minutes = psychological win = momentum builder
- Usually the minimal step is trivial (open document, click link, etc.)

**Example Output:**
```
┌─────────────────────────────────────────┐
│ ⚡ START HERE                           │
│ 1 min - Open the assignment document    │
│                                         │  
│ Yellow highlight + bold text            │
└─────────────────────────────────────────┘
```

### 4. **Total Time Summary** 📌
Shows the overall time commitment at the top.

```
⏱️ Total estimated time: 34 minutes
```

Helps users decide: "Can I do this in my 30-minute study block?" → Yes/No

## Technical Implementation

### Domain Model (`app/domain/models/task_step.py`)

```python
class StepDifficulty(str, Enum):
    TRIVIAL = "trivial"    # ⚡
    EASY = "easy"          # ✓
    MODERATE = "moderate"  # ●
    HARD = "hard"          # ⚠
    
    @property
    def effort_indicator(self) -> str:
        """Returns visual emoji indicator"""
        
    @property
    def time_budget(self) -> str:
        """Returns time budget description"""

class TaskStep(BaseModel):
    description: str              # "Write introduction"
    estimated_minutes: int        # 1-120 range validated
    difficulty: StepDifficulty    # One of the 4 levels
    is_minimal_first_step: bool   # True only for first step
    
    @property
    def effort_indicator(self) -> str:
        """Returns emoji for this step's difficulty"""
        
    @property
    def formatted_time(self) -> str:
        """Returns "X min" format"""
```

### API Endpoint (`app/presentation/routes/ai_help.py`)

**Endpoint:** `POST /api/tasks/{task_id}/help/enhanced?user_question=optional`

**Response:**
```json
{
  "summary": "Task introduction",
  "deliverable": "Complete introduction section",
  "steps": [
    {
      "description": "Open document",
      "estimated_minutes": 1,
      "difficulty": "trivial",
      "is_minimal_first_step": true,
      "effort_indicator": "⚡",
      "formatted_time": "1 min"
    },
    {
      "description": "Write introduction",
      "estimated_minutes": 15,
      "difficulty": "moderate",
      "is_minimal_first_step": false,
      "effort_indicator": "●",
      "formatted_time": "15 min"
    }
  ],
  "warnings": [],
  "questions_to_clarify": [],
  "final_checklist": ["Intro complete"],
  "total_estimated_minutes": 16,
  "minimal_first_step": { /* first step object */ },
  "has_minimal_first_step": true
}
```

### Frontend JavaScript (`app/presentation/static/js/enhanced_help.js`)

**User Flow:**
1. User generates basic checklist with "Generate checklist" button
2. New "Load with estimates" button appears next to steps
3. Click button → calls `/api/tasks/{task_id}/help/enhanced`
4. JavaScript renders enriched steps with:
   - Color-coded difficulty badges
   - Time estimates in readable format
   - "START HERE" highlight for minimal first step
   - Total time banner at top

**Key Functions:**
- `loadEnhancedSteps()` - Async fetch with error handling
- `renderEnhancedSteps(data)` - DOM building with XSS-safe escaping
- `getTaskId()` - Extract ID from URL
- `escapeHtml(text)` - Prevent injection attacks

## How to Use

### As a User

1. **View a task** on the dashboard
2. **In "AI Help" section**, click "Generate checklist"
3. AI generates basic checklist
4. **Click "Load with estimates"** button
5. See enhanced steps with:
   - ⏱️ Total time commitment at top
   - Per-step difficulty (⚡✓●⚠)
   - Per-step time in minutes
   - "START HERE" badge on first step

### As a Developer

#### Add Enhanced Steps to Custom Code

```python
from app.domain.models.task_step import TaskStep, StepDifficulty

# Create a step
step = TaskStep(
    description="Write introduction paragraph",
    estimated_minutes=15,
    difficulty=StepDifficulty.MODERATE,
    is_minimal_first_step=False,
)

# Use properties
print(step.effort_indicator)  # "●"
print(step.formatted_time)    # "15 min"
```

#### Call the API Directly

```javascript
async function getEnhancedHelp(taskId) {
    const response = await fetch(
        `/api/tasks/${taskId}/help/enhanced`,
        { method: "POST" }
    );
    return await response.json();
}
```

## Testing

### Unit Tests (20 tests)
**File:** `tests/unit/test_task_step_model.py`

- StepDifficulty enum coverage (4 levels, properties)
- TaskStep validation (time range, required fields)
- Property generation (effort_indicator, formatted_time)
- JSON serialization

**Run:** `pytest tests/unit/test_task_step_model.py -v`

### Integration Tests (7 tests)
**File:** `tests/integration/test_ai_help_routes.py`

- Endpoint responds with correct format
- Step effort indicators are accurate
- Total time calculation correct
- Minimal first step identification works
- Empty steps handled gracefully

**Run:** `pytest tests/integration/test_ai_help_routes.py -v`

**Result:** 161 total tests passing ✅

## Design Decisions

### Why Heuristic Time Estimation?

We don't use LLM time estimation because:
1. **Faster** - No extra API calls, immediate feedback
2. **Consistent** - Rules are predictable across users
3. **Future-proof** - Easy to upgrade when LLM adds time metadata

### Why Keywords Instead of Machine Learning?

- **No ML dependency** - Keeps stack simple
- **Rule-based** - Transparent and debuggable
- **Customizable** - Easy to adjust time mappings
- **Scalable** - No training data needed

### Why Always Mark First Step as Minimal?

- **Psychological principle** - First step should always be easiest
- **By definition** - Minimal means "lowest resistance"
- **Positional rule** - Simple and predictable

## Limitations & Future Work

### Current Limitations

1. **Heuristic estimation** - Keyword-based, not LLM-aware
   - May overestimate complex steps
   - May underestimate simple steps with complex descriptions

2. **No step dependencies** - All steps shown in sequence
   - Future: Could show "can skip if..." notes

3. **No user feedback loop** - Time estimates don't improve over time
   - Future: Track actual vs. estimated time

4. **No caching** - Recalculate every time
   - Future: Cache enhanced responses per task

### Future Enhancements

1. **LLM Integration** - Update ChecklistPayload schema to receive time/difficulty from LLM
   - Results in more accurate, context-aware estimates

2. **User Feedback** - "Took longer/shorter than expected" → improve estimates

3. **Step Dependencies** - "Do this first", "can skip if...", prerequisite highlighting

4. **Alternative Orderings** - Suggest reordering steps for optimal cognitive pacing

5. **Batch Estimation** - Show time allocation across multiple tasks

## Psychological Impact

### Problem Solved
- **Procrastination Friction**: "I need to write a 10-page essay" feels impossible
- **Decision Paralysis**: Too many steps, don't know where to start
- **Time Anxiety**: "Will this take 10 minutes or 10 hours?"

### Solution Provided
- **Concrete First Step**: "Spend 5 minutes opening the document" is achievable
- **Clear Path**: Steps shown in order with purpose
- **Time Certainty**: "I can commit to this 30-minute block"

### Expected User Experience
```
Before: "Ugh, I need to do this essay → Procrastinate → Never start"
After:  "OK, 1 min to open file → 5 min to review → I can do this! → Momentum"
```

## Performance

- **API Response Time**: < 100ms (with mock data)
- **Frontend Rendering**: 50-100ms for 5-10 steps
- **JavaScript Bundle**: +146 lines (~5 KB)
- **No Database Queries**: All heuristics are in-memory
- **No LLM Overhead**: Uses cached ChecklistResponse

## Files Modified in Phase 6

```
Created:
├── app/domain/models/task_step.py (119 lines)
├── app/presentation/routes/ai_help.py (161 lines)
├── app/presentation/static/js/enhanced_help.js (146 lines)
├── tests/unit/test_task_step_model.py (112 lines)
├── tests/integration/test_ai_help_routes.py (172 lines)

Updated:
├── app/presentation/templates/partials/ai_panel.html (+12 lines)
├── app/presentation/templates/base.html (+5 lines)
└── app/presentation/routes/__init__.py (+2 lines for router registration)
```

## Conclusion

Phase 6 delivers a complete enhanced AI help system that:
- ✅ Estimates reasonable time per step using heuristics
- ✅ Classifies difficulty with visual indicators
- ✅ Highlights the crucial "minimal first step"
- ✅ Shows total time commitment
- ✅ Provides smooth async UI experience
- ✅ Includes comprehensive test coverage (27 new tests)
- ✅ Maintains backwards compatibility
- ✅ Ready for LLM integration in Phase 7

**Next Steps**: Wire LLM to output structured step metadata instead of plain text, enabling AI-aware time/difficulty estimates.
