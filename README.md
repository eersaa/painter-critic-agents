# Multi-Agent Painter & Critic

A multi-agent system built with the [AG2 framework](https://docs.ag2.ai/) where a Painter agent draws on a digital canvas and a Critic agent evaluates the result visually, iterating over multiple rounds.

## How to Run

### Prerequisites

- [mise](https://mise.jdx.dev/) for Python version management
- [uv](https://docs.astral.sh/uv/) for package management

### Setup

```bash
mise install
uv sync
```

### Run

```bash
uv run python -m painter_critic "a house with a sun and trees"
```

Options:

```
python -m painter_critic <prompt> [--rounds N] [--painter-model MODEL] [--critic-model MODEL]
```

| Flag | Default | Description |
|------|---------|-------------|
| `prompt` | (required) | Drawing subject for the Painter |
| `--rounds` | 10 | Number of painting/critique rounds |
| `--painter-model` | `openai/gpt-4.1-mini` | Model for the Painter agent |
| `--critic-model` | `qwen/qwen3.5-flash-02-23` | Model for the Critic agent |

Images (`round_NN.png`) and `conversation.log` are written to `output/`.

## Design Decisions

### Three-agent topology

**How we got here.** The first design was a two-agent direct chat: `Critic.initiate_chat(Painter)` with drawing tools registered as `register_for_llm(painter)` + `register_for_execution(critic)`. Mechanically this worked — AG2 dispatches tool_calls to the receiver of a two-agent chat, so the Critic ran them. But it was semantically inverted: the Critic literally drew the pixels, the Painter only emitted tool_call JSON, and the conversation log attributed drawing to the wrong agent. Since AG2 requires caller and executor to be **distinct** `ConversableAgent` instances, "Painter paints" couldn't be satisfied without adding a third agent.

Final design:

- **Painter** (LLM) — issues `draw_*` tool_calls; sees canvas via hook.
- **PainterExecutor** (no LLM) — runs the drawing functions. Internal; stays out of the conversation log.
- **Critic** (LLM) — visually evaluates.

Two-phase orchestration:

```
Phase 1 (pre-draw):
  PainterExecutor.initiate_chat(Painter) — Painter ↔ Executor tool loop.
Phase 2 (critique, max_turns = rounds):
  Painter.initiate_chat(Critic)
    Critic's reply triggers a nested Painter ↔ Executor tool loop.
    Nested chat's last message (Painter's text summary) becomes Painter's
    reply to Critic via summary_method="last_msg".
```

The outer `conversation.log` only shows Painter ↔ Critic messages.

### Termination

Early versions relied on `MAX_TOOL_ITERATIONS` (meant as a safety cap) as the *de facto* hand-off signal, because the Painter prompt forbade stopping and Painter never emitted a text-only reply for the executor to terminate on. That made the knob load-bearing in two incompatible ways (raise it → outer `max_turns` overruns on complex prompts; lower it → Painter cut off mid-composition).

Current design decouples the two:

- **Termination predicate** on PainterExecutor: `is_termination_msg = lambda msg: not msg.get("tool_calls")`. Works in both phases (Executor is the receiver both times).
- **Painter prompt** requires a one-sentence text summary after each turn's tool calls. That summary fires the predicate *and* becomes the hand-off payload forwarded to Critic via `summary_method="last_msg"`.

`MAX_TOOL_ITERATIONS = 8` is now a pure safety cap.

### Drawing tools

| Tool | Purpose |
|------|---------|
| `draw_rectangle` | Sky, ground, walls, windows, doors |
| `draw_circle` | Sun, wheels, decorations |
| `draw_line` | Outlines, fences, details |
| `draw_polygon` | Roofs, mountains, irregular shapes |

Four geometric primitives cover most scenes. Each tool validates inputs (hex colors, coordinate bounds, polygon point count) and returns descriptive strings instead of raising, to keep the AG2 conversation flowing on invalid input.

### Multimodal image handling

Both agents see the canvas as a base64 PNG in OpenAI's vision format. Hooks:

- **Critic `send_hook`** — attaches the current canvas to outgoing critiques.
- **Painter `save_hook`** — writes `round_NN.png` and increments `RoundTracker`.
- **Both agents, pre-reply:** `strip_assistant_images` (API compliance) → `prune_stale_user_images` (avoid history bloat as canvases accumulate round-over-round) → `reply_hook` (inject current canvas). Order is pinned by unit tests.
- **`_nested_chat_message`** wrapper lifts Critic's multimodal list into `{"content": list}` so the nested `initiate_chat` doesn't reject it.

### Critic feedback style

Critic describes location by named regions ("upper-left", "below the left tree"), not pixel coordinates. And gives suggestions how to improve the drawing.

### Module structure

```
painter_critic/
  config.py — CLI args, LLM config
  canvas.py — PIL wrapper, PNG save, base64
  tools.py  — drawing functions
  agents.py — agent creation, system messages
  hooks.py  — image injection, round tracking
  main.py   — entrypoint + two-phase orchestration
```

## Observations

Results from a 10-round run with prompt "a photorealistic light blue sportscar with shiny wheels":

**What worked well:**
- Critic never declared the work "done/excellent/perfect" and produced 3–5 coordinate-aware suggestions per turn across all 10 rounds.
- Painter's text summary drove the hand-off cleanly; no `max_turns` cutoff artifacts.
- Visible progression: There was visible changes on every iteration. And painter was using usually multiple tools and mutliple times.

**What went wrong:**
- **Non-monotonic progress.** Round 5 is less coherent than round 1. Painter reworks geometry aggressively each round instead of preserving what already looked good. I.e. The final result is worse than the first iteration.
- **Critic loops on impossible asks.** "Shinier wheels", "less boxy", "glossier paint" recur — a 200×200 canvas without anti-aliasing can't deliver photorealism.
- **`draw_line` was not really utilized.** Painter preferred rectangles/circles/polygons even when Critic asked for outlines.

### Models

- **Painter: `openai/gpt-4.1-mini`** — tool-calling + spatial reasoning. Solid spatial reasoning, weak at preserving prior-round structure.
- **Critic: `qwen/qwen3.5-flash-02-23`** — accurate vision, structured output held across all rounds.

## Running Tests

```bash
uv run pytest             # fast (no API)
uv run pytest -m "slow"   # integration (requires API access)
```
