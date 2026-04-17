import argparse
import os

CANVAS_SIZE = 200
DEFAULT_ROUNDS = 10
OUTPUT_DIR = "output"
# Safety cap only; natural termination is handled by PainterExecutor.is_termination_msg.
MAX_TOOL_ITERATIONS = 8
DEFAULT_PAINTER_MODEL = "openai/gpt-4.1-mini"
DEFAULT_CRITIC_MODEL = "qwen/qwen3.5-flash-02-23"


def load_api_url() -> str:
    url = os.environ.get("API_URL")
    if not url:
        raise RuntimeError("API_URL not set")
    return url


def create_llm_config(model: str) -> dict:
    api_url = load_api_url()
    return {
        "config_list": [{"model": model, "base_url": api_url, "api_key": "not-needed"}]
    }


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt")
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS)
    parser.add_argument("--painter-model", default=DEFAULT_PAINTER_MODEL)
    parser.add_argument("--critic-model", default=DEFAULT_CRITIC_MODEL)
    return parser.parse_args(argv)
