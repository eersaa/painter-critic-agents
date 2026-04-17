# Multi-Agent Painter & Critic

A multi-agent system built with the [AG2 framework](https://docs.ag2.ai/) where a Painter agent draws on a digital canvas and a Critic agent evaluates the result visually, iterating over multiple rounds to improve the artwork.

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
python -m painter_critic "a house with a sun and trees"
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

### Output

Images and conversation log are saved to `output/`:

```
output/
  round_01.png
  round_02.png
  ...
  round_10.png
  conversation.log
```

## Design Decisions

### Architecture: From Two Agents to Three

**Initial approach — two-agent direct chat.** The first design used AG2's simplest pattern: `Critic.initiate_chat(Painter, …)`, with drawing tools registered as `register_for_llm(painter)` + `register_for_execution(critic)`. Reasoning: AG2 dispatches tool_calls to the *receiver* of a two-agent chat, so colocating execution on the Critic was the mechanically simplest way to get tools to run in the default topology. GroupChat and nested chats were rejected as overcomplicated for a two-party interaction.

**Why we pivoted.** The two-agent design was mechanically working but semantically inverted: the Critic literally executed every `draw_*` call, conversation logs attributed tool results to the Critic, and the Painter emitted tool_call JSON without ever touching the canvas. Role inversion broke cohesion — "Critic reviews" and "Critic draws" collapsed into one agent. Fulfilling the assignment's intent (Painter paints, Critic critiques) required the Painter to be the one drawing. AG2's tool-calling framework requires caller and executor to be **distinct** `ConversableAgent` instances, so "Painter draws" cannot be satisfied by a single agent in the original topology.

**Current design — three agents, two phases.** Behind a single user-facing Painter identity:

- **Painter** (LLM) — issues tool_calls; sees canvas via hook.
- **PainterExecutor** (no LLM) — runs the drawing functions. Internal helper; not surfaced in the outer conversation log.
- **Critic** (LLM) — unchanged role; visually evaluates.

Two-phase flow:

```
Phase 1 (pre-draw):
  PainterExecutor.initiate_chat(Painter, message=<text "Paint: X" + blank canvas>)
    → Painter LLM ↔ PainterExecutor tool loop until Painter replies in text

Phase 2 (critique loop, `rounds` iterations, max_turns = rounds * 2):
  Painter.initiate_chat(Critic, message=<"I have painted: X. Please review.">)
  Each round:
    Painter  ──(text summary + canvas via send_hook)─▶  Critic
    Critic   ──(structured feedback + canvas)───────▶  Painter
             └─ triggers nested chat: PainterExecutor ↔ Painter tool loop;
                Painter's final text summary becomes its reply to Critic
```

The nested tool loop is wired via `painter.register_nested_chats(trigger=critic, chat_queue=[{sender: painter_executor, recipient: painter, message: _nested_chat_message, …}])`. The outer `conversation.log` therefore shows only Painter ↔ Critic messages; internal tool traffic stays out. Painter-initiates direction matches the natural creative flow (user prompt → Painter paints → hands off to Critic for review).

### Round Control

A "round" = one Painter summary sent to Critic + one Critic feedback reply. Phase 2's `max_turns = rounds * 2` bounds the outer chat. Per-round internal tool iterations inside the nested chat are bounded separately by `MAX_TOOL_ITERATIONS = 8` (defined in `config.py`). `RoundTracker` increments on each Painter→Critic send (via `create_save_hook`) and produces the `round_NN.png` filenames. There is no custom `_is_termination_msg` — an earlier version used one to guard round count, but AG2 invokes it on *incoming* messages, which briefly killed both phases (Phase 1 terminated on the "Paint: X" message arriving; Phase 2 terminated on the first Critic feedback). `max_turns` alone is sufficient once the counts are set correctly.

Phase 1 pre-draw is capped separately by `max_turns = MAX_TOOL_ITERATIONS` and terminates naturally when Painter emits a text reply (no tool_calls): PainterExecutor has no LLM, so a text reply breaks the loop.

### Model Choice

- **Painter: `openai/gpt-4.1-mini`** -- Selected for its tool-calling capability and spatial reasoning. The Painter needs to translate feedback into specific drawing coordinates and tool calls.
- **Critic: `qwen/qwen3.5-flash-02-23`** -- Selected for accurate vision. Testing revealed that gpt-4.1-mini's vision is unreliable (identified a red image as blue), while qwen correctly identified colors. The Critic's primary job is visual evaluation, so vision accuracy is critical. Note: `gpt-4.1-nano` does not support vision at all.

Both models are configurable via CLI flags.

### Drawing Tools

Four tools were chosen to cover the geometric primitives needed for any scene:

| Tool | Purpose | Example use |
|------|---------|-------------|
| `draw_rectangle` | Filled rectangles | Sky, ground, walls, windows, doors |
| `draw_circle` | Filled circles | Sun, wheels, decorations |
| `draw_line` | Lines with configurable width | Outlines, fences, details |
| `draw_polygon` | Filled polygons from point lists | Roofs, mountains, irregular shapes |

Each tool operates on a shared mutable `Canvas` instance via closures, validates its inputs (hex colors, coordinate bounds, polygon point count), and returns descriptive strings instead of raising exceptions to keep the AG2 conversation flowing even on invalid input.

### Multimodal Image Handling

Both agents see the actual canvas image using base64-encoded PNGs in OpenAI's vision message format. Four hooks are registered to manage image flow and round tracking:

**On Critic:**

- **`create_send_hook`** (`process_message_before_send`) — attaches the current canvas image to outgoing feedback messages so the Painter sees what the canvas looks like. Changes are permanent in message history. Skips tool-execution messages.
- **`create_strip_images_hook`** (`process_all_messages_before_reply`) — strips `image_url` blocks from assistant-role messages before the Critic's LLM call. Required because some models (e.g. Qwen) reject images in assistant messages.
- **`create_reply_hook`** (`process_all_messages_before_reply`) — temporarily injects the current canvas into the last message before the Critic's LLM generates feedback, enabling visual evaluation without duplicating images in history.

**On Painter:**

- **`create_save_hook`** (`process_message_before_send`) — saves a PNG snapshot of the canvas after each Painter reply and increments the `RoundTracker`. Skips tool-execution messages.

**Nested-chat message callable.** When Critic's `send_hook` wraps feedback content as a multimodal list (`[{type: text}, {type: image_url}]`), AG2's default nested-chat machinery forwards that bare list directly to the inner `initiate_chat`, which then fails `_message_to_dict` validation. A small `_nested_chat_message` callable registered on the `chat_queue` wraps list content as `{"content": list}` before it reaches the nested chat, preserving the multimodal payload intact.

### Module Structure

The system is decomposed into six modules with clear separation of concerns:

```
painter_critic/
  config.py   -- Configuration, CLI args, LLM config
  canvas.py   -- Canvas state (PIL wrapper, PNG save, base64 encoding)
  tools.py    -- Drawing tool functions
  agents.py   -- AG2 agent creation and system messages
  hooks.py    -- Round tracking and image injection hooks
  main.py     -- CLI entrypoint wiring everything together
```

Module dependency graph:

```
Config ──────────────────┐
Canvas ──┬── Tools ──────┼── Agents ── Main
         └── Hooks ──────┘
```

This decomposition allows each module to be tested independently without LLM calls. `main.py` orchestrates the two-phase pipeline: Phase 1 pre-draw via `painter_executor.initiate_chat(painter, _phase1_message(prompt, canvas))`, Phase 2 critique loop via `painter.initiate_chat(critic, …, max_turns=rounds*2)`. It also owns the `_nested_chat_message` wiring helper and the `save_conversation_log` writer.

## Observations

Results from a 10-round run with prompt "a house with a sun and trees":

**What worked well:**
- The Critic's structured, numbered feedback (specific suggestions with coordinate guidance) effectively directed improvements. The Painter reliably translated feedback like "center the door" or "add a ground plane" into correct tool calls.
- Iterative refinement was clearly visible: the scene progressed from basic shapes (round 1) to a recognizable house with roof overhang, centered door with doorknob, round tree canopies, window with glass reflection, and a green lawn (round 6).
- The Painter batched 4-6 tool calls per turn, making substantial progress each round.

**What went wrong:**
- After round 6, the Critic ran out of substantive feedback and declared the scene "Excellent!" Both agents devolved into mutual congratulations for the remaining 4 rounds. Rounds 7-10 produced identical images — no further drawing occurred. A more directive Critic system message or a "never say the work is done" instruction could mitigate this.
- `draw_line` was never used. The Painter relied on rectangles, circles, and polygons exclusively. Line-based details (fences, outlines, rays) were suggested by the Critic but the Painter chose other tools instead.

**Model observations:**
- `openai/gpt-4.1-mini` (Painter) showed solid spatial reasoning, correctly interpreting relative positioning feedback and mapping it to pixel coordinates on the 200x200 canvas.
- `qwen/qwen3.5-flash-02-23` (Critic) provided detailed, well-structured visual feedback with clear priorities. Its vision capability accurately identified shape positioning issues (e.g., "the door looks like two separate rectangles").

*(Note: the "Excellent!" devolution described above motivated the subsequent Critic system-message rewrite, which now forbids declaring the work "done/excellent/complete/perfect" and requires 3–5 specific suggestions per round. A re-benchmark on the updated prompts has not yet been run.)*

## Running Tests

```bash
# Fast tests (no API calls)
uv run pytest

# Include slow integration tests (requires API access)
uv run pytest -m "slow"
```
