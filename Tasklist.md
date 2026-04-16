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

## Todo

- [x] README.md observations section (filled in after 10-round run)
- [x] Run full 10-round pipeline with real API and verify output
- [x] Update README round control and hook sections to reflect actual architecture

## Future Improvements

- Consider moving `RoundTracker` out of `hooks.py` — it's not a hook, it manages round lifecycle state
- Consider `Canvas.width`/`Canvas.height` properties if frequent dimension access needed
- Consider `Canvas.clear()` if restart capability is needed
- Unify canvas dimension source of truth: `Canvas()` defaults width/height independently from `config.CANVAS_SIZE`
- Consider moving `save_conversation_log` to its own module if more output formatters are added
