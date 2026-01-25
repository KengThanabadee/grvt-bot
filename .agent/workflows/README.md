# Antigravity Workflows

This folder contains Antigravity skills/workflows for the GRVT Trading Bot.

## Available Workflows

### 1. Trading Strategy Builder
**File:** [trading-strategy-builder.md](trading-strategy-builder.md)

**Purpose:** Guided workflow to build custom trading strategies with proper structure and validation.

**Use when:** You want to create a new trading strategy from scratch or convert existing strategy logic into code.

**Workflow phases:**
- Phase 0: Check existing strategy
- Phase 1: Strategy discovery (style, indicators, risk)
- Phase 2: Logic definition (entry/exit conditions)
- Phase 3: Code generation (Python strategy class)
- Phase 4: Validation & testing
- Phase 5: Deployment guide

**Usage:**
```
Just ask Antigravity:
"Help me build a trading strategy using the strategy builder workflow"

or

"I want to create a new trading strategy"
```

## How to Use Workflows

1. **Mention the workflow name** in your conversation with Antigravity
2. **Follow the guided steps** - AI will ask questions phase by phase  
3. **Provide detailed answers** - The more specific, the better the output
4. **Review generated code** - Always validate before using

## Adding New Workflows

To add a new workflow:

1. Create `workflowname.md` in this folder
2. Use YAML frontmatter:
   ```markdown
   ---
   name: Workflow Name
   description: Brief description
   ---
   ```
3. Document the workflow steps clearly
4. Include templates and examples
5. Update this README

## Workflow Best Practices

- **Be specific** - Define exact conditions and criteria
- **Use examples** - Show what you mean with concrete examples
- **Test incrementally** - Validate each phase before proceeding
- **Document changes** - Keep track of what you modify

## Related Documentation

- [SKILL.md](../../docs/SKILL.md) - Main package skill documentation
- [MIGRATION.md](../../docs/MIGRATION.md) - Migration guide
- [PROJECT_STRUCTURE.md](../../PROJECT_STRUCTURE.md) - Project structure overview
