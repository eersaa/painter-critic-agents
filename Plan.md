# Plan: Multi-Agent Painter & Critic

## Overview

In this assignment you will build a multi-agent system using the AG2 framework (https://docs.ag2.ai/) in which two agents collaborate iteratively to produce a digital drawing. A Painter agent draws on a digital canvas, and a Critic agent evaluates the resulting drawing visually and provides actionable feedback to the Painter agent. The agents take turns in rounds: each round consists of the Painter drawing (or refining) the canvas, followed by the Critic reviewing it and suggesting improvements.

## Technical Setup

Use the provided OpenRouter API through the provided AWS proxy specified in the `.env`.

No API key is required when using the proxy URL. The OpenRouter-compatible API follows the OpenAI chat completions format.

Configure your AG2 agents to use one of the following models: openai/gpt-4.1-nano or qwen/qwen3.5-flash-02-23 or openai/gpt-4.1-mini

AG2 supports configuring custom base URLs and model names through its LLM configuration. Refer to the AG2 documentation on how to set up a custom OAI-compatible endpoint.

Use the AG2 framework. Your implementation must use AG2's classes and its built-in conversation mechanisms (e.g., initiate_chat).

Do not use raw API calls or other agent frameworks.

## Task Description

Build a system with the following two agents:

### Agent 1: Painter

- The Painter agent produces or modifies a digital drawing on a canvas. It should call tools for drawing pixels on the canvas.

- The Painter creates its drawing based on a given prompt or subject (you choose the subject).

- In subsequent rounds, the Painter receives the Critic's feedback and modifies the drawing accordingly. The Painter must use the feedback to iteratively improve the artwork.

- The output must be an actual image file (PNG or similar).

### Agent 2: Critic

- The Critic agent receives the image produced by the Painter and evaluates it. Since the model is multimodal, the Critic must receive the actual image (not just a textual description) in its input so it can visually assess the drawing.

- The Critic provides structured, actionable feedback: what works well, what should be changed, and specific suggestions for the next iteration.

- The Critic's feedback is passed back to the Painter for the next round.

### Round Structure

One round consists of exactly two steps: (1) the Painter produces/updates the drawing, and (2) the Critic reviews the image and provides feedback. Your system must support running multiple rounds. Each round should produce a saved image file so that the progression of the artwork can be observed.

## Requirements

1. Both agents must be implemented as AG2 class instances with appropriate system messages that define their roles.

2. Use a digital canvas of size 200x200.

3. The Painter must have at least three different tools at its disposal for drawing pixels on the digital canvas. It is recommended to always draw multiple pixels on the canvas instead of a single pixel. If you draw a single pixel, there will be hardly any progress visible.

4. Choose your own subject to draw and the amount of details in the subject prompt.

5. The Painter and Critic must receive the actual rendered image (using the model's multimodal/vision capability). The Critic must base its feedback on the visual output.

6. The system must run for a configurable number of rounds (at least 10). Each round's image must be saved so that iterative progress is visible.

7. The conversation between agents must use AG2's built-in conversation mechanisms (e.g., initiate_chat or equivalent). Do not orchestrate the turns with manual loops that bypass the framework.

8. Include a README.md with instructions on how to run your solution, the drawing subject you chose (subject prompt), and a brief explanation of your design decisions.

## Deliverables

- Your source code (Python script), either as a link to a public GitHub repo or in a zip file.

- The saved images from rounds 1, 5, 10 (round_01.png, round_05.png, and round_10.png).

- The full conversation log between the Painter and Critic (copy & paste text output or save to file).

- A README.md file explaining your approach, design choices (which pattern and why? which tools and why?), and how to run the code. Also include a section on observations on the painter's output images (e.g., what went well? what went wrong?)

## Grading Criteria

| Criterion | Points | What I look for |

| --------- | ------ | ---------------- |

| Agent architecture | 2 | Clear, well-defined system messages. Roles are distinct. A suitable design pattern is used. |

| Multimodal critic | 2 | The Painter sees the canvas. The Critic receives and analyzes the actual image. Vision capability of the models is used. |

| Iterative improvement | 1 | The drawing visibly improves across rounds. The Painter receives the feedback from the Critic. |

| Image generation | 1 | The Painter produces valid image files each round. |

| Image generation | 3 | The Painter has at least three different tools at its disposal for drawing on the canvas. |

| AG2 framework usage | 3 | The conversation is orchestrated via AG2-native mechanisms, not manual loops bypassing the framework. |

| Documentation & reproducibility | 3 | README.md is clear. Code runs as documented. Design decisions are explained. |

| Total | 15 | |

## Hints

- The Painter and Critic should `see` the canvas. (Don't make the Painter guess where to put pixels.)

- For working with images, explore how AG2 handles multimodal messages. The model accepts base64-encoded images in the OpenAI vision message format.

- Think carefully how you structure the system messages for each agent. The Painter should know it is drawing and the Critic should know it is evaluating visual output.

- Use the max_consecutive_auto_reply or a similar mechanism to control the number of rounds. Stop after 10 rounds.

- Save intermediate images with round numbers in the filename so you can see the progression.
