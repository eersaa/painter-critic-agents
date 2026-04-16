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

## Todo

- [ ] Wave 4: Main module — CLI entrypoint, end-to-end integration
- [ ] README.md observations section (fill in after running 10 rounds)
- [ ] Fix README: `src/painter_critic/` path should be `painter_critic/` (no src/ prefix)
- [ ] Fix README: round control description says `max_consecutive_auto_reply` but decision is to use `max_turns`

## Future Improvements

- Consider returning `dict[str, Callable]` from `create_tools` instead of list — fragile index-based unpacking; fix before Wave 4 adds another consumer
- Consider moving `RoundTracker` out of `hooks.py` — it's not a hook, it manages round lifecycle state; could live in `config.py` or its own module
- Consider removing `python-dotenv` from dependencies if main.py won't call `load_dotenv()`
- Consider `Canvas.width`/`Canvas.height` properties if Tools code needs frequent dimension access
- Consider `Canvas.clear()` if restart capability is needed
- Unify canvas dimension source of truth: `Canvas()` defaults width/height independently from `config.CANVAS_SIZE`; Wave 4 `main.py` must pass size explicitly to both `Canvas()` and `create_agents()` to avoid mismatch
