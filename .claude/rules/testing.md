## Testing Conventions

- Framework: pytest
- Use red-green-refactor principle.
- Keep tests simple, fast and focused on behavior.
- Test interface how the user would use it.
- Test naming: `test_<component>_<scenario>_<expected_result>`

## Running tests

- Fast (default, excludes `slow`): `uv run pytest`
- Slow / acceptance: `uv run pytest -m slow`
- All: `uv run pytest -m "slow or not slow"`

## Good tests are...

- Understandable - Tests should describe what they are testing to understand the goals of the software: Focused on the behaviour of the system, not a specific implementation
- Maintainable - Tests need to be maintainable so that they are easy to change, without losing their intent.
- Repeatable - Tests should be definitive, should always pass or fail in the same way for a given version of the software that they are testing.
- Atomic - Tests should be isolated and focus on a single outcome. Tests should not have side-effects. Independent of other tests and resources, to run tests in parallel, or in any order.
- Necessary - Aim is to guide development from tests, so we should create tests that help us, are necessary, to guide our development choices.
- Granular - Tests should be small, simple and focused, and assert a single outcome of the code that they are testing. And a clear indication of what the problem is when they fail, that do not require interpretation.
- Fast - Tests need to be fast. Need keep them efficient and give us results quickly.
