# Tasklist

## Done

- [x] Wave 1: Canvas module — PIL wrapper with draw/save/base64/vision format (22 tests)
- [x] Wave 1: Config module — constants, env loading, LLM config, CLI args (17 tests)
- [x] Architect review Wave 1: removed module-level `load_dotenv()` side effect, added type hint
- [x] Wave 2: Tools module — drawing functions (rectangle, circle, line, polygon)
- [x] Wave 2: Hooks module — RoundTracker, image injection hooks
- [x] Architect review Wave 2: type annotations + docstrings on tool functions (needed for AG2 schema), fixed polygon validation order

## Todo

- [ ] Investigate `max_turns` vs `max_consecutive_auto_reply` — verify empirically whether tool call round-trips (Painter tool call → Critic executes → Painter summary) count as separate turns against `max_turns`. README and Wave 2 plan contradict each other. Affects how Wave 3 sets round count in `initiate_chat`.
- [ ] Fix README: `src/painter_critic/` path should be `painter_critic/` (no src/ prefix)
- [ ] Fix README: round control description says `max_consecutive_auto_reply` but decision is to use `max_turns`
- [ ] Wave 3: Agents module — Painter + Critic ConversableAgents
- [ ] Wave 4: Main module — CLI entrypoint, end-to-end integration
- [ ] README.md observations section (fill in after running 10 rounds)

## Future Improvements

- Consider returning `dict[str, Callable]` from `create_tools` instead of list — cleaner for AG2 `register_function` calls in Wave 3 (currently fragile index-based unpacking)
- Consider moving `RoundTracker` out of `hooks.py` — it's not a hook, it manages round lifecycle state; could live in `config.py` or its own module
- Consider `Canvas.width`/`Canvas.height` properties if Tools code needs frequent dimension access
- Consider `Canvas.clear()` if restart capability is needed
