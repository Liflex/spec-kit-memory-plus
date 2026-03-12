---
description: Quick feature generation for small fixes and improvements (< 4 hours). Creates minimal spec, plan, and tasks.
handoffs:
  - label: Implement Feature
    agent: speckit.implement
    prompt: Implement the quick feature based on the generated spec, plan, and tasks.
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Overview

The text the user typed after `/speckit.features` in the triggering message **is** the feature description. This command creates a quick feature workflow for small tasks that can be completed in under 4 hours.

**When to use `/speckit.features`:**
- Bug fixes that are well-understood
- Small UI improvements
- Configuration changes
- Documentation updates
- Tasks estimated < 4 hours
- Quick implementations without extensive research

**When to use `/speckit.specify` instead:**
- Complex features requiring research
- API changes that affect multiple systems
- Features with external dependencies
- Tasks estimated > 4 hours
- Projects requiring architecture decisions

## Quick Feature Workflow

### Step 0: Check for Existing Feature Plan

**BEFORE anything else**, check if a feature plan already exists in the current project.

**Check for these files in order:**
1. `.speckit/FEATURE_PLAN.md` - Current feature plan
2. `.spec-kit/FEATURE_PLAN.md` - Legacy location
3. `specs/*/FEATURE_PLAN.md` - In any spec directory

**If a feature plan EXISTS:**
- Read the plan file
- Inform the user: "Found existing feature plan. Executing based on the plan."
- Skip feature creation, proceed directly to **Step 3: Implement**
- After successful implementation, **delete** the plan file

**If no plan exists AND `$ARGUMENTS` is empty:**
- Tell the user: "No feature plan found and no description provided. Please either provide a feature description (`/speckit.features <description>`) or I'll help you create one."
- Ask: "Would you like to create a feature plan now?"
  - If yes: Proceed to **Step 1**
  - If no: **STOP**

**If no plan exists AND `$ARGUMENTS` is provided:**
- Continue to **Step 0.1** below

### Step 0.1: Load Project Context

**Read project context files if they exist:**

1. **`.speckit/DESCRIPTION.md`** or **`README.md`** - Understand:
   - Tech stack (language, framework, database)
   - Project architecture
   - Coding conventions

2. **`.claude/memory/`** directory — check if exists. If missing — create it with stub files using Auto-Create Rule (see CLAUDE.md), then skip reading. If exists — read:
   - **`lessons.md`** - Learn from past bugs, solutions that worked
   - **`patterns.md`** - Proven implementation patterns
   - **`architecture.md`** - Key technical decisions
   - If Ollama is configured and vector memory has entries — run semantic search for similar past solutions. If not configured — skip entirely, do not check or ask.

3. **`CLAUDE.md`** (if exists) - Check:
   - Project-specific rules
   - Development guidelines
   - Testing requirements

**How to apply context:**
- Treat project-specific rules as **overrides** to general practices
- When project rules conflict with general rules, **project rules win**
- Apply both: general best practices + project-specific rules
- **CRITICAL:** Context rules apply to ALL outputs including specs, plans, and code

### Step 1: Quick Feature Planning

For quick features, create a minimal plan focusing on:

**Key Questions to Answer:**
1. **What** is being changed/added/removed?
2. **Why** is this change needed?
3. **Where** in the codebase will changes happen?
4. **How** will the change be implemented (high-level)?
5. **What** could break (risks)?

**Quick Research (if needed):**

Use targeted code exploration:

```bash
# Find relevant files
Glob("**/*<related-keyword>*")

# Search for similar patterns
Grep("pattern", "<file-extension>")
```

**Create Feature Plan:**

Create `.speckit/FEATURE_PLAN.md` with:

```markdown
# Feature Plan: {Brief Title}

**Type:** Bug Fix | Small Feature | Refactor | Config | Docs
**Estimated:** {X} hours (< 4 hours for quick features)
**Created:** {YYYY-MM-DD HH:mm}

## Overview

{What is being done and why}

## Changes Required

**Files to modify:**
- `path/to/file.ext` - {what to change}
- `path/to/another.ext` - {what to change}

## Implementation Approach

1. {Step 1 - what to do}
2. {Step 2 - what to do}
3. {Step 3 - verification}

## Risks & Considerations

- {Potential side effect}
- {What to check after}
- {Edge cases to watch}

## Acceptance Criteria

1. {First criterion}
2. {Second criterion}
3. No regressions in existing functionality

## Notes

{Any additional context or constraints}
```

**After creating the plan:**

```
## Feature Plan Created ✅

Plan saved to `.speckit/FEATURE_PLAN.md`.

To implement immediately, run: /speckit.features
To review/modify first, edit the plan file
```

**STOP here if user wants to review.**

### Step 2: Ask User for Mode

If no plan existed and user provided `$ARGUMENTS`, ask:

```
How would you like to proceed with this feature?

1. Plan first - Create a plan for review, then implement
2. Implement now - Proceed directly with implementation
```

**If user chooses "Plan first":**
- Create feature plan as described in Step 1
- **STOP** and wait for user to execute again

**If user chooses "Implement now":**
- Skip plan creation, proceed to **Step 3**

### Step 3: Implement

When implementing (either from plan or directly):

**Before making changes:**
1. Read the feature plan if it exists
2. Use plan as your guide
3. Follow each step sequentially

**Implementation approach:**

1. **Make targeted changes only**
   - Fix/implement exactly what's needed
   - Don't refactor unrelated code
   - Don't add "extra" improvements

2. **Add logging for verification**
   ```typescript
   // ✅ REQUIRED: Add logging
   console.log('[FEATURE] {feature-name} processing', { relevant_data });

   try {
     const result = await implementation();
     console.log('[FEATURE] {feature-name} success', { result });
     return result;
   } catch (error) {
     console.error('[FEATURE] {feature-name} error', {
       error: error.message,
       stack: error.stack
     });
     throw error;
   }
   ```

3. **Follow project conventions**
   - Match existing code style
   - Use existing patterns
   - Respect project structure

4. **Test as you go**
   - Verify each change works
   - Check for regressions
   - Test edge cases

### Step 4: Verification

After implementation:

1. **Check compilation/build**
   - Code compiles without errors
   - No type errors
   - Dependencies are satisfied

2. **Verify functionality**
   - Feature works as expected
   - Edge cases handled
   - Error cases handled

3. **Check for regressions**
   - Existing features still work
   - No unintended side effects

### Step 5: Suggest Test Coverage

**ALWAYS suggest adding tests:**

```
## Feature Implemented ✅

**What was done:** {brief description}
**Files modified:** {list of files}

### Recommended: Add Tests

This feature should have test coverage:

\`\`\`{language}
describe('{feature-name}', () => {
  it('should {expected behavior}', () => {
    // Arrange
    const input = { test input };

    // Act
    const result = {function}(input);

    // Assert
    expect(result).{expected outcome};
  });
});
\`\`\`

Would you like me to create the test?
- [ ] Yes, create the test
- [ ] No, skip for now
```

### Step 6: Create Learning Artifact (inline, as discovered)

**Save insights immediately when recognized** — do not wait for task completion. The session may end at any moment.

Only save if the insight is non-trivial and reusable. Memory directory and stub files should already exist (created during Memory Context step). If not — create them now.

**If this was a bug fix or revealed a non-obvious lesson:** Immediately append to `.claude/memory/lessons.md`

```markdown
## {Bug/Issue Title}

**Date:** {YYYY-MM-DD}
**Type:** Bug Fix | Quick Feature

**Problem:**
{What was wrong or needed}

**Solution:**
{How it was fixed - key insight}

**Tags:** {#tag1} {#tag2}
```

**If this revealed a reusable pattern:** Append to `.claude/memory/patterns.md`

```markdown
## {Pattern Name}

**When to use:**
{Situation where this pattern applies}

**How to implement:**
{Code or approach}
```

**If this involved an architecture decision:** Append to `.claude/memory/architecture.md`

```markdown
## {Decision Title}

**Date:** {YYYY-MM-DD}
**Context:** {Why this decision was needed}
**Decision:** {What was chosen}
**Rationale:** {Why this over alternatives}
```

**Vector memory:** For high-importance insights (cross-project relevance, major pattern or architecture decision) — also store in vector memory via `vector_memory.py`. If Ollama is not configured — skip silently.

### Step 7: Cleanup

After successful implementation:

1. **Delete feature plan** if it exists:
   ```bash
   rm .speckit/FEATURE_PLAN.md
   ```

2. **Offer to free context:**
   ```
   Feature complete! Context is heavy from implementation.

   Would you like to:
   1. /clear - Full reset (recommended)
   2. /compact - Compress history
   3. Continue as is
   ```

## Important Rules

1. **Check FEATURE_PLAN.md first** - Always check for existing plan
2. **Quick = focused** - Small changes only, don't expand scope
3. **Load context** - Read project files before making changes
4. **Add logging** - Always add logging for verification
5. **Suggest tests** - Help prevent regressions
6. **Create artifacts** - Learn from each feature/fix
7. **Clean up** - Delete plan after successful implementation
8. **Minimal changes** - Don't refactor unrelated code
9. **Follow conventions** - Match existing code style
10. **Verify** - Check for regressions before done

## Examples

### Example 1: Quick Bug Fix

**User:** `/speckit.features Fix button not responding on first click`

**Actions:**
1. Find button component
2. Identify event handler issue
3. Add fix with logging
4. Test and verify
5. Suggest test case

### Example 2: Small UI Improvement

**User:** `/speckit.features Add loading spinner to API calls`

**Actions:**
1. Find API call locations
2. Add loading state
3. Add spinner component
4. Test with slow network
5. Document usage

### Example 3: Configuration Change

**User:** `/speckit.features Update timeout to 30 seconds`

**Actions:**
1. Find timeout configuration
2. Update value
3. Check all affected code
4. Verify no breaking changes
5. Update documentation

## DO NOT

- ❌ Use for complex features requiring research
- ❌ Skip loading project context
- ❌ Make extensive refactoring
- ❌ Add unrelated improvements
- ❌ Skip logging
- ❌ Skip verification
- ❌ Skip test suggestions
- ❌ Leave FEATURE_PLAN.md after implementation
