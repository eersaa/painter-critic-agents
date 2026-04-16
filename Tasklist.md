# Tasklist

## Done

- [x] Wave 1: Canvas module — PIL wrapper with draw/save/base64/vision format (22 tests)
- [x] Wave 1: Config module — constants, env loading, LLM config, CLI args (17 tests)
- [x] Architect review: removed module-level `load_dotenv()` side effect, added type hint

## Todo

- [ ] Wave 2: Tools module — drawing functions (rectangle, circle, line, polygon)
- [ ] Wave 2: Hooks module — RoundTracker, image injection hooks
- [ ] Wave 3: Agents module — Painter + Critic ConversableAgents
- [ ] Wave 4: Main module — CLI entrypoint, end-to-end integration
- [ ] README.md

## Future Improvements

- Consider `Canvas.width`/`Canvas.height` properties if Tools code needs frequent dimension access
- Consider `Canvas.clear()` if restart capability is needed
