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

The assignment defines a "round" as one Painter draw + one Critic review. AG2's `max_turns` counts conversational exchanges, which may not map 1:1 to rounds because tool call and result messages also count as exchanges. To ensure exactly the configured number of rounds, we use `max_consecutive_auto_reply` or a termination function that checks the `RoundTracker` counter against the target, rather than relying solely on `max_turns`.

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

Both agents see the actual canvas image using base64-encoded PNGs in OpenAI's vision message format. Image injection uses two AG2 hook mechanisms:

- **`process_message_before_send`** on the Critic attaches the rendered canvas to outgoing feedback messages so the Painter sees what the canvas looks like before deciding what to draw next. These changes are permanent in the message history.
- **`process_all_messages_before_reply`** on the Critic temporarily injects the canvas into the LLM context before generating feedback, so the Critic can visually evaluate the artwork without duplicating images in the conversation history.

Both hooks include guards to skip image injection on tool-execution result messages.

### Module Structure

The system is decomposed into six modules with clear separation of concerns:

```
src/painter_critic/
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

*This section will be updated after running the system.*

<!-- TODO: Add observations after running 10 rounds -->
<!-- - What went well in the drawing progression? -->
<!-- - What went wrong or was unexpected? -->
<!-- - How did the Critic's feedback influence the Painter? -->
<!-- - Which tools were most/least used? -->

## Running Tests

```bash
# Fast tests (no API calls)
uv run pytest

# Include slow integration tests (requires API access)
uv run pytest -m "slow"
```
