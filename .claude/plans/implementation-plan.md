# Plan: Multi-Agent Painter & Critic

## Context

Assignment requires building a two-agent system with AG2 framework where a Painter draws on a 200x200 canvas and a Critic evaluates the image visually, iterating for 10 rounds. API proxy is provided (no key needed). Greenfield project — no code exists yet.

## Architecture

Two AG2 `ConversableAgent`s in a direct `initiate_chat`:

```
Critic.initiate_chat(Painter, message=initial_prompt+canvas_image, max_turns=10)
```

**Per-turn flow:**
1. Critic sends feedback + canvas image to Painter
2. Painter LLM generates tool calls (draw_rectangle, etc.)
3. Critic executes tool calls (standard AG2 caller/executor pattern)
4. Tool results sent back to Painter
5. Painter responds with summary of what it drew
6. Critic's custom reply hook: renders canvas, saves round image, injects image into LLM context, generates visual feedback

**Round control:** `max_turns` may not map 1:1 to "rounds" since tool call exchanges count as turns. Need to verify with a minimal test. Fallback: use `max_consecutive_auto_reply` or a termination function checking `RoundTracker.current_round >= target`.

**Image injection:** AG2 hooks with guards to only inject on LLM-response messages (not tool execution results):
- `process_message_before_send` on Critic: attach canvas image to feedback messages (permanent in recipient history). Guard: skip if message contains tool execution results.
- `process_all_messages_before_reply` on Critic: inject canvas into LLM context (transient). Guard: skip if Critic is about to execute tools (not generate feedback).

## Module Behaviors

### Config (`config.py`)

Loads `API_URL` from `.env`. Provides `create_llm_config(model)` returning an AG2 `LLMConfig` pointed at the proxy. Exposes constants: `CANVAS_SIZE = 200`, `DEFAULT_ROUNDS = 10`, `OUTPUT_DIR = "output"`. Parses CLI args: required positional `prompt` (drawing subject), optional `--rounds`, `--painter-model`, `--critic-model`.

### Canvas (`canvas.py`)

Wraps a PIL `Image` of configurable size. Exposes `draw()` returning an `ImageDraw.Draw` handle for tools to use. `save(path)` writes PNG. `to_base64()` returns base64-encoded PNG string. `to_image_content()` returns OpenAI vision format dict `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}`. Canvas is mutable — tools modify it in place.

### Tools (`tools.py`)

Four drawing functions operating on a shared `Canvas` instance (captured via closure from `create_tools(canvas)`):
- `draw_rectangle(x1, y1, x2, y2, color)` — filled rectangle
- `draw_circle(cx, cy, radius, color)` — filled circle
- `draw_line(x1, y1, x2, y2, color, width)` — line with configurable width
- `draw_polygon(points, color)` — filled polygon from list of (x,y) tuples

Each returns a success description string (or error description on invalid input). Colors are hex strings. Coordinates clamped to canvas bounds. Input validation: hex color regex, polygon >= 3 points, coordinate clamping. Errors return descriptive strings instead of raising exceptions — keeps AG2 conversation flowing.

### Agents (`agents.py`)

Creates two `ConversableAgent`s. Painter (`openai/gpt-4.1-mini`): system message instructs it to draw using tools based on the user's subject prompt and critic feedback, coordinates within 0-199. Critic (`qwen/qwen3.5-flash-02-23`): system message instructs it to visually evaluate the canvas image and return structured feedback (progress, strengths, improvements, priority). Tools registered with `register_function(func, caller=painter, executor=critic)`.

### Hooks (`hooks.py`)

`RoundTracker` — tracks current round number, generates image paths (`round_01.png`), increments per turn.

Image injection hooks registered on the Critic:
- `process_message_before_send`: attaches canvas image to every outgoing message so the Painter sees the current canvas state
- `process_all_messages_before_reply`: temporarily injects canvas image into message context before the Critic's LLM call, so the Critic can visually evaluate without polluting message history with duplicate images

### Main (`main.py`)

CLI entrypoint. Parses args (prompt, rounds). Creates canvas, config, round tracker. Creates agents and registers tools + hooks. Builds initial multimodal message (subject prompt + blank canvas image). Calls `critic.initiate_chat(painter, message=..., max_turns=rounds)`. After chat completes, saves conversation log to `output/conversation.log`.

```
tests/
  test_canvas.py
  test_tools.py
  test_config.py
  test_hooks.py
  test_agents.py
```

## Key Design Decisions

- **Model defaults:** `openai/gpt-4.1-mini` for Painter, `qwen/qwen3.5-flash-02-23` for Critic. Configurable via CLI flags `--painter-model` and `--critic-model`
- **Subject:** User-provided via CLI argument. E.g. `python -m painter_critic "a house with a sun and trees"`
- **4 drawing tools:** `draw_rectangle`, `draw_circle`, `draw_line`, `draw_polygon` — covers all needed shapes (rectangles for walls/windows/sky, circle for sun, polygon for roof, lines for details)
- **Tool registration:** `register_function(func, caller=painter, executor=critic)` — AG2-idiomatic pattern
- **Canvas:** Mutable `Canvas` object shared via closures in tool functions
- **Image format:** Base64-encoded PNG in OpenAI vision format `{"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}`

## Acceptance Tests

High-level tests verifying end-to-end system behavior. Written first per CLAUDE.md workflow.

**File:** `tests/test_acceptance.py`

### Fast acceptance tests (mocked LLM)

Pipeline tests:
1. `test_system_produces_image_for_each_round` — full pipeline produces round_01.png through round_10.png
2. `test_output_images_are_200x200` — all saved images have correct dimensions
3. `test_images_change_between_rounds` — consecutive round images differ (canvas modified)
4. `test_canvas_persists_across_rounds` — round N canvas contains pixels from round N-1 (not fresh each time)
5. `test_conversation_log_is_saved` — log exists and contains both agent names
6. `test_number_of_rounds_is_configurable` — num_rounds=3 produces exactly 3 images

Agent architecture tests:
7. `test_agents_have_distinct_system_messages` — both agents have non-empty, different system messages
8. `test_painter_has_at_least_three_tools` — >= 3 tools registered on Painter

Multimodal tests:
10. `test_critic_receives_image_in_messages` — Critic LLM input contains image_url blocks
11. `test_painter_receives_image_in_messages` — Painter LLM input contains image_url blocks

Feedback loop tests:
12. `test_critic_feedback_reaches_painter` — Critic's feedback text appears in Painter's next-round LLM input

Tool behavior tests:
13. `test_each_drawing_tool_modifies_canvas` — calling each of the 4 tools on blank canvas changes pixel values

### Slow acceptance tests (real API, marked `@pytest.mark.slow`)

15. `test_full_run_with_real_api` — 2-round run with actual API produces images and conversation log

**Mocking strategy:** Mock LLM responses. Painter mock returns pre-scripted tool call messages (e.g. `draw_rectangle(x1=0, y1=0, x2=199, y2=100, color="#87CEEB")`) so tools execute and modify canvas. Critic mock returns pre-scripted feedback strings. Tests full wiring without API dependency.

## Implementation Phases

Module dependency graph:

```
Config ──────────────────┐
Canvas ──┬── Tools ──────┼── Agents ── Main
         └── Hooks ──────┘
```

Following the CLAUDE.md TDD workflow. Parallel waves where dependencies allow:

### Phase 0: Project Setup (sequential)

- Create `.mise.toml`, `pyproject.toml` (deps: `ag2[openai]`, `Pillow`, `python-dotenv`; dev: `pytest`, `ruff`)
- `uv sync`, verify imports work

### Wave 1 (parallel): Canvas + Config

- Canvas: TDD test_canvas.py -> canvas.py (dimensions, background, save, base64, image_content format)
- Config: TDD test_config.py -> config.py (env loading, LLM config, CLI args, constants)

### Wave 2 (parallel): Tools + Hooks (after Wave 1)

- Tools: TDD test_tools.py -> tools.py (pixel changes, bounds clamping, return descriptions, input validation)
- Hooks: TDD test_hooks.py -> hooks.py (RoundTracker, image injection with message-type guards)

### Wave 3 (sequential): Agents (after Wave 2)

- TDD: test_agents.py -> agents.py (system messages, tool registration, hook wiring, mocked LLM)

### Wave 4 (sequential): Integration & Main

- Implement main.py, run end-to-end with actual API
- Verify images saved, conversation flows, log written

### Phase 7: Documentation

- README.md with run instructions, design decisions, observations on output

## Verification

1. `pytest` — all unit/integration tests pass
2. `ruff check && ruff format --check` — clean linting
3. `python -m painter_critic "a house with a sun"` — full 10-round run producing:
   - `output/round_01.png` through `output/round_10.png`
   - `output/conversation.log`
4. Visual inspection of round images for iterative improvement

## Dependencies

```toml
[project]
dependencies = ["ag2[openai]>=0.11.0", "Pillow>=10.0.0", "python-dotenv>=1.0.0"]
[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.4.0"]
```

## Risks

1. **Small model spatial reasoning** — qwen may struggle with coordinates. Mitigation: detailed system messages with explicit coordinate guidance

## Resolved Questions

1. **Proxy vision support:** Tested all 3 models with base64 PNG image.
   - `openai/gpt-4.1-mini`: accepts vision but answered incorrectly (said "Blue" for red image)
   - `openai/gpt-4.1-nano`: does NOT support vision ("can't see the image")
   - `qwen/qwen3.5-flash-02-23`: accepts vision and answered correctly ("Red")
   - **Decision:** Use `openai/gpt-4.1-mini` for Painter (tool calling + spatial reasoning), `qwen/qwen3.5-flash-02-23` for Critic (accurate vision).

2. **AG2 hook mechanism:** `process_message_before_send` is best for image injection.
   - Signature: `(sender, message, recipient, silent) -> message`
   - Changes are permanent (persist in recipient's message history)
   - Runs after reply generation but before transmission
   - `process_all_messages_before_reply` is transient (changes don't persist) — useful for augmenting LLM context without polluting history
   - Both can be combined: use `process_message_before_send` for persistent image attachment, `process_all_messages_before_reply` for temporary context augmentation

3. **AG2 multimodal pipeline:** AG2 correctly passes list-based content (text + image_url blocks) through its message pipeline without flattening or stringifying. Also provides `pil_to_data_uri()` utility in `autogen.agentchat.contrib.img_utils`.
