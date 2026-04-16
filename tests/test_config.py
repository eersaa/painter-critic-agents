import pytest

from painter_critic.config import (
    CANVAS_SIZE,
    DEFAULT_CRITIC_MODEL,
    DEFAULT_PAINTER_MODEL,
    DEFAULT_ROUNDS,
    OUTPUT_DIR,
    create_llm_config,
    load_api_url,
    parse_args,
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
        args = parse_args(
            [
                "trees",
                "--rounds",
                "5",
                "--painter-model",
                "custom/painter",
                "--critic-model",
                "custom/critic",
            ]
        )

        assert args.prompt == "trees"
        assert args.rounds == 5
        assert args.painter_model == "custom/painter"
        assert args.critic_model == "custom/critic"


class TestConfigUnit:
    # --- Constants ---

    def test_config_canvas_size_is_200(self):
        assert CANVAS_SIZE == 200

    def test_config_default_rounds_is_10(self):
        assert DEFAULT_ROUNDS == 10

    def test_config_output_dir_is_output(self):
        assert OUTPUT_DIR == "output"

    def test_config_default_painter_model_contains_gpt_4_1_mini(self):
        assert "gpt-4.1-mini" in DEFAULT_PAINTER_MODEL

    def test_config_default_critic_model_contains_qwen(self):
        assert "qwen" in DEFAULT_CRITIC_MODEL

    # --- load_api_url ---

    def test_config_load_api_url_returns_url_from_env(self, api_url_env):
        result = load_api_url()
        assert result == api_url_env

    def test_config_load_api_url_raises_when_env_missing(self, monkeypatch):
        monkeypatch.delenv("API_URL", raising=False)
        with pytest.raises(RuntimeError):
            load_api_url()

    # --- create_llm_config ---

    def test_config_create_llm_config_model_matches_argument(self, api_url_env):
        result = create_llm_config("my/model")
        assert result["config_list"][0]["model"] == "my/model"

    def test_config_create_llm_config_base_url_matches_env(self, api_url_env):
        result = create_llm_config("any/model")
        assert result["config_list"][0]["base_url"] == api_url_env

    def test_config_create_llm_config_api_key_is_nonempty_string(self, api_url_env):
        result = create_llm_config("any/model")
        key = result["config_list"][0]["api_key"]
        assert isinstance(key, str)
        assert len(key) > 0

    # --- parse_args ---

    def test_config_parse_args_custom_rounds(self):
        args = parse_args(["prompt text", "--rounds", "5"])
        assert args.rounds == 5

    def test_config_parse_args_custom_painter_model(self):
        args = parse_args(["prompt text", "--painter-model", "x/painter"])
        assert args.painter_model == "x/painter"

    def test_config_parse_args_custom_critic_model(self):
        args = parse_args(["prompt text", "--critic-model", "x/critic"])
        assert args.critic_model == "x/critic"

    def test_config_parse_args_missing_prompt_raises_system_exit(self):
        with pytest.raises(SystemExit):
            parse_args([])
