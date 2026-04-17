# Multi-Agent Painter & Critic

## Project Overview

Multi-agent system built on AG2 (autogen). Painter agent draws on a 200×200 canvas via tool calls; Critic agent visually evaluates the PNG and sends feedback. Iterates for N rounds. Model and round count configurable via CLI. Outputs PNGs and conversation logs to `output/`.

## Architecture

Three agents, two-phase flow:

- **Painter** (LLM) — issues drawing tool calls; sees canvas image via hook.
- **PainterExecutor** (non-LLM) — executes tools (AG2 tool-calling pattern).
- **Critic** (LLM) — visually evaluates canvas, returns structured feedback.

Phase 1 (pre-draw): `PainterExecutor.initiate_chat()` → Painter nested LLM↔tool loop for first attempt.
Phase 2 (critique loop): `Painter.initiate_chat(Critic)` with `max_turns=rounds`.

Pre-reply hook order on both agents (load-bearing): `strip_assistant_images` → `prune_stale_user_images` → `reply_hook`. Reply must run last so the injected current canvas survives pruning.

Key modules (under `painter_critic/`):

- [main.py](../painter_critic/main.py) — `setup_pipeline`, `run_pipeline`.
- [agents.py](../painter_critic/agents.py) — `create_agents()` → (Painter, PainterExecutor, Critic).
- [canvas.py](../painter_critic/canvas.py) — PIL wrapper, base64, PNG save.
- [tools.py](../painter_critic/tools.py) — `draw_rectangle`/`circle`/`line`/`polygon`.
- [hooks.py](../painter_critic/hooks.py) — `RoundTracker`, image injection/stripping.
- [config.py](../painter_critic/config.py) — CLI args, LLM config.

## **Important** Development Workflow

When you are creating a plan, implementing or fixing issue always use following approach:

Throughout every step below:

- **Think Before acting / Surface assumptions / ask when unclear.** Don't silently pick between interpretations. If a simpler approach exists, say so. Stop and name confusion rather than guessing.
- **Surgical changes.** Every changed line should trace to the request. Don't "improve" adjacent code, comments, or formatting. Match existing style. Remove only orphans your own change created; flag pre-existing dead code rather than deleting it.

1. Make sure that ALL fast tests pass. Ask user what to do if they fail.
2. Main agent writes or edits acceptance tests for the described behavior in the current session plan.
3. Main agent reviews tests with **reviewer** sub-agent.
4. Main agent refactors, improves and simplifies the tests based on the feedback.
5. Ask user to review the acceptance tests.
6. Main agent commits changes to tests.
7. Implementation with red-green-refactor loop (sub-agents commit their own changes):
   1. **test-writer** - red - writes or edits integration and unit level tests covering behavior of the acceptance tests.
   2. **implementer** - green - creates the implementation making the tests pass.
   3. **reviewer** - refactor - lints, refactors for quality.
8. Review the project with **system-architect**, make changes based on feedback and run **all** test suites.

Finally, update `Tasklist.md` for:
1. Todo items
2. Done task history
3. Future improvements.

## System design principles

- Modular design - break down a complex system into smaller, self-contained modules. Each module serves a specific purpose, can be maintained separately, and can be replaced with a more efficient alternative when needed.
- Abstraction and Simplifying complexity - Hide unnecessary details and expose essential functionalities. Create clear interfaces and reduce complexity of interactions between software modules.
- Cohesion - Keep related functionalities together to enhance maintainability and comprehensibility.
- Separation of concerns - Isolate different aspects of a system to focus on one job at a time. Break down code into small, independent units that handle specific tasks.
- Coupling and Managing dependencies - Prefer loose coupling, as it reduces the interdependencies between modules, making the system more flexible and easier to modify.

## Testing

Read `.claude/rules/testing.md`

## Key Dependencies

Runtime:

- `ag2[openai]>=0.11.0`
- `Pillow>=10.0.0`
- `python-dotenv>=1.0.0`

Dev: `pytest>=8.0`, `ruff>=0.4.0`. Python `>=3.13` (pinned via `mise`).

## Python

- Control Python version with `mise`
- Use `uv` for package management.
