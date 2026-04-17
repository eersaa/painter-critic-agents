# Tasklist

## Done

- [x] Wave 1: Canvas module — PIL wrapper with draw/save/base64/vision format (22 tests)
- [x] Wave 1: Config module — constants, env loading, LLM config, CLI args (17 tests)
- [x] Architect review Wave 1: removed module-level `load_dotenv()` side effect, added type hint
- [x] Wave 2: Tools module — drawing functions (rectangle, circle, line, polygon)
- [x] Wave 2: Hooks module — RoundTracker, image injection hooks
- [x] Architect review Wave 2: type annotations + docstrings on tool functions (needed for AG2 schema), fixed polygon validation order
- [x] Wave 3: Agents module — Painter + Critic ConversableAgents (20 tests)
- [x] Pre-Wave 4 Unit C: `create_save_hook` — side-effect hook that snapshots canvas after each Painter round (181 tests); hardened `_is_tool_message` to handle `str | dict`
- [x] Pre-Wave 4 Unit B: Wire canvas size, Painter image awareness, subject in Critic message
- [x] Investigate `max_turns` — tool execution happens inside `generate_reply()`, does not consume extra turns. Wave 4 should use `max_turns`
- [x] Confirm system prompts exist for both agents
- [x] Fix README: path `src/painter_critic/` → `painter_critic/`, round control → `max_turns`
- [x] Wave 4: Main module — `setup_pipeline`, `run_pipeline`, `save_conversation_log`, `main`, `__main__.py` (202 tests)
- [x] Architect review Wave 4: extracted `setup_pipeline` to eliminate test wiring duplication
- [x] README.md observations section (filled in after 10-round run)
- [x] Run full 10-round pipeline with real API and verify output
- [x] Update README round control and hook sections to reflect actual architecture
- [x] Painter (not Critic) executes drawing tools — introduced internal PainterExecutor agent, nested chat wiring, Painter-initiates flow (Phase 1 pre-draw + Phase 2 critique loop)
- [x] Rewrote Painter and Critic system messages to handle first-turn-blank-canvas explicitly and forbid premature completion claims
- [x] Fixed nested chat ValueError on multimodal Critic feedback via `_nested_chat_message` callable in `chat_queue`
- [x] Architect review post-nested-chat fix: dropped unused `rounds` param from `setup_pipeline`; extracted `_phase1_message(prompt, canvas)` helper to remove duplication between `run_pipeline` and `_run_mocked_pipeline`
- With following prompt I hit some limit. Is it because of some restriction of the API or is it programmed into this application? Prompt: "Paint a phorealistic, truelike, sportscar with shiny wheels in light blue body color."
  - Error message `>>>>>>>> TERMINATING RUN (f0a3180e-3a0d-4712-829a-9f9ac12ca1fe): Maximum turns (40) reached`
  - Addressed with rounds: `def run_pipeline(
    prompt,
    rounds=DEFAULT_ROUNDS,
    output_dir=OUTPUT_DIR,
    painter_model=DEFAULT_PAINTER_MODEL,
    critic_model=DEFAULT_CRITIC_MODEL,
):`
- [x] Decouple `MAX_TOOL_ITERATIONS` from hand-off signal: added `is_termination_msg` on `PainterExecutor` (receiver-side per AG2 docs) that terminates on text-only replies; rewrote Painter prompt step 5 to require end-of-turn text summary. Works uniformly in Phase 1 and Phase 2 nested chat; `summary_method="last_msg"` forwards the summary to Critic. Cap is now pure safety.
- [x] Fix quality degradation across rounds: split `create_strip_images_hook` into `create_strip_assistant_images_hook` (API compliance) + `create_prune_stale_user_images_hook` (prevents stale canvas accumulation). Registered strip→prune→reply chain on both Painter and Critic. Reworded Phase-2 opener to "Please critique the canvas." Rewrote Critic rule 2 to use named regions / shape anchors instead of pixel coordinates; dropped tool-prescription negation. 3-round end-to-end run shows monotonic detail gain and zero `(x, y)` pairs in Critic output.
- [x] Fix residual Painter image duplication + stale-mid-tool-loop: diagnostic trace on `worktree-diagnostic-ag2-trace` revealed Painter was seeing 2–3 canvas images per LLM call (via `_phase1_message` + `send_hook` + `reply_hook` all attaching) and seeing a stale snapshot inside nested tool-loop iterations (`reply_hook` skipped when last message was tool). Fix: `reply_hook` now scans backward for the last non-tool message, strips any existing `image_url` blocks from its content, then appends the current canvas. `prune_stale_user_images_hook` simplified to strip images from every user message unconditionally. Post-fix 3-round diagnostic: 11/11 LLM calls show exactly 1 image, mid tool-loop Painter calls now carry the canvas on the preceding user message.

## Todo

- The conversation log isn't most readable for the user. And same applies to the output what user gets to the terminal.
- It seems that there is some difference how the model wants to get the tools because with default models there is no this error but when I use the Qwen model for the painter I will get this error that the tools are listed in wrong kind of data structure.
  - `>>>>>>>> EXECUTED FUNCTION draw_polygon...
Call ID: call_47243106640e446c9d999772
Input arguments: {'points': [20, 150, 60, 120, 160, 115, 180, 140, 170, 165, 30, 165], 'color': '87CEEB'}
Output:
Error: 12 validation errors for draw_polygon
points.0
  Input should be a valid list [type=list_type, input_value=20, input_type=int]
    For further information visit https://errors.pydantic.dev/2.13/v/list_type
points.1
  Input should be a valid list [type=list_type, input_value=150, input_type=int]
    For further information visit https://errors.pydantic.dev/2.13/v/list_type
points.2
  Input should be a valid list [type=list_type, input_value=60, input_type=int]
    For further information visit https://errors.pydantic.dev/2.13/v/list_type
points.3
  Input should be a valid list [type=list_type, input_value=120, input_type=int]
    For further information visit https://errors.pydantic.dev/2.13/v/list_type
points.4
  Input should be a valid list [type=list_type, input_value=160, input_type=int]
    For further information visit https://errors.pydantic.dev/2.13/v/list_type
points.5
  Input should be a valid list [type=list_type, input_value=115, input_type=int]
    For further information visit https://errors.pydantic.dev/2.13/v/list_type
points.6
  Input should be a valid list [type=list_type, input_value=180, input_type=int]
    For further information visit https://errors.pydantic.dev/2.13/v/list_type
points.7
  Input should be a valid list [type=list_type, input_value=140, input_type=int]
    For further information visit https://errors.pydantic.dev/2.13/v/list_type
points.8
  Input should be a valid list [type=list_type, input_value=170, input_type=int]
    For further information visit https://errors.pydantic.dev/2.13/v/list_type
points.9
  Input should be a valid list [type=list_type, input_value=165, input_type=int]
    For further information visit https://errors.pydantic.dev/2.13/v/list_type
points.10
  Input should be a valid list [type=list_type, input_value=30, input_type=int]
    For further information visit https://errors.pydantic.dev/2.13/v/list_type
points.11
  Input should be a valid list [type=list_type, input_value=165, input_type=int]
    For further information visit https://errors.pydantic.dev/2.13/v/list_type`
- Need to document the updated agent architecture now that painter consists from two agents because of AG2 requirements and the critique agent is still one agent and additionally probably need to update the way they are working so painter is initiating the process if it is presented in the README file.


## Future Improvements

- Consider moving `RoundTracker` out of `hooks.py` — it's not a hook, it manages round lifecycle state
- Consider `Canvas.width`/`Canvas.height` properties if frequent dimension access needed
- Consider `Canvas.clear()` if restart capability is needed
- Unify canvas dimension source of truth: `Canvas()` defaults width/height independently from `config.CANVAS_SIZE`
- Consider moving `save_conversation_log` to its own module if more output formatters are added
- Rename `"TERMINATE"` in `_executor_mock` — `max_turns` handles termination now; the literal is misleading to readers
- Add unit test asserting Phase 1 `clear_history=True` is passed to `initiate_chat` (matters for repeatable runs)
- If `setup_pipeline` grows further, split into `_wire_tools` / `_wire_nested_chat` / `_wire_hooks`
- `_phase1_message` still attaches a blank canvas explicitly, which reply_hook now strips and replaces with the current canvas — harmless under the idempotent hook but adds wasted work. Consider dropping the explicit attachment in `_phase1_message`.
- Consider `wire_canvas_agent(agent, canvas, *, sends_canvas: bool)` helper if a third canvas-aware agent appears (currently 6 `register_hook` calls × 2 agents = tolerable duplication, extracting now would hide load-bearing order)
- Port `scripts/trace_run.py` (lightweight LLM-input trace hook diagnostic) from the `worktree-diagnostic-ag2-trace` branch to main if ongoing hook-chain work warrants a repeatable diagnostic
