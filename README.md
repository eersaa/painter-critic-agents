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

### Architecture Pattern: Two-Agent Chat

The system uses AG2's `initiate_chat` to orchestrate a direct two-agent conversation between the Critic (initiator) and Painter (recipient). This is the simplest AG2-native pattern that satisfies the round structure: the Critic sends feedback with the canvas image, the Painter responds by calling drawing tools, and the cycle repeats.

Alternatives considered and rejected:
- **GroupChat (3+ agents)**: Would add a separate tool executor agent. Rejected because it introduces unnecessary complexity in speaker selection and turn ordering for what is fundamentally a two-party interaction.
- **Nested chats**: Would have an orchestrator trigger separate sub-conversations with Painter and Critic. Rejected because it overcomplicates the simple back-and-forth and makes message/image passing between agents harder to manage.

The Critic acts as both the visual evaluator (via its LLM) and the tool executor (via AG2's caller/executor registration pattern). This is idiomatic AG2 -- the agent that receives tool calls executes them.

### Round Control

A "round" is one Painter draw + one Critic review. Tool execution in AG2 consumes extra turns within `initiate_chat`, so `max_turns` alone cannot control the number of painting rounds. Instead, termination is driven by `RoundTracker`: after the Painter's `process_message_before_send` hook saves a snapshot and increments the round counter, `painter._is_termination_msg` checks whether `tracker.current_round > rounds`. `max_turns=rounds*4` serves as an upper-bound safety net.

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

This decomposition allows each module to be tested independently without LLM calls.

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

## Running Tests

```bash
# Fast tests (no API calls)
uv run pytest

# Include slow integration tests (requires API access)
uv run pytest -m "slow"
```
