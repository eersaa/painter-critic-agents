import pytest

from painter_critic.config import (
    create_llm_config,
    parse_args,
    DEFAULT_ROUNDS,
    DEFAULT_PAINTER_MODEL,
    DEFAULT_CRITIC_MODEL,
)


class TestConfigAcceptance:
    def test_config_create_llm_config_returns_valid_ag2_config(self, api_url_env):
        result = create_llm_config("test/model")

        config_list = result["config_list"]
        assert len(config_list) == 1
        entry = config_list[0]
        assert entry["model"] == "test/model"
        assert entry["base_url"] == api_url_env
        assert entry["api_key"]  # proxy needs no key, but AG2 requires non-empty

    def test_config_parse_args_returns_prompt_and_defaults(self):
        args = parse_args(["a house with a sun"])

        assert args.prompt == "a house with a sun"
        assert args.rounds == DEFAULT_ROUNDS
        assert args.painter_model == DEFAULT_PAINTER_MODEL
        assert args.critic_model == DEFAULT_CRITIC_MODEL

    def test_config_parse_args_overrides_with_custom_flags(self):
        args = parse_args([
            "trees",
            "--rounds", "5",
            "--painter-model", "custom/painter",
            "--critic-model", "custom/critic",
        ])

        assert args.prompt == "trees"
        assert args.rounds == 5
        assert args.painter_model == "custom/painter"
        assert args.critic_model == "custom/critic"
