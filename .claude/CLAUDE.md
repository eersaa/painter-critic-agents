# Multi-Agent Painter & Critic

## Project Overview


## Architecture


## **Important** Development Workflow

When you are creating a plan, implementing or fixing issue always use following approach:

1. Make sure that ALL fast tests pass. Ask user what to do if they fail.
2. Main agent writes or edits acceptance tests for the described behavior in the current session plan.
3. Main agent reviews tests with **reviewer** sub-agent.
4. Main agent refactors, improves and simplifies the tests based on the feedback.
5. Ask user to review the acceptance tests.
6. Main agent commits changes to tests.
7. Implementation with red-green-refactor loop (sub-agents commit their own changes):
   1. **test-writer** - red - writes or edits integration and unit level tests covering behavior of the acceptance tests.
   2. **implementer** - green - creates the implementation making the tests pass.
   3. **reviewer** - refactor - lints, refactors for quality.
8. Review the project with **system-architect**, make changes based on feedback and run **all** test suites.

Finally, update `Tasklist.md` for Todo items, done task history and future improvements.

## System design principles

- Modular design - break down a complex system into smaller, self-contained modules. Each module serves a specific purpose, can be maintained separately, and can be replaced with a more efficient alternative when needed.
- Abstraction and Simplifying complexity - Hide unnecessary details and expose essential functionalities. Create clear interfaces and reduce complexity of interactions between software modules.
- Cohesion - Keep related functionalities together to enhance maintainability and comprehensibility.
- Separation of concerns - Isolate different aspects of a system to focus on one job at a time. Break down code into small, independent units that handle specific tasks.
- Coupling and Managing dependencies - Prefer loose coupling, as it reduces the interdependencies between modules, making the system more flexible and easier to modify.

## Testing

Read `.claude/rules/testing.md`

## Key Dependencies


## Python

- Control Python version with `mise`
- Use `uv` for package management.
