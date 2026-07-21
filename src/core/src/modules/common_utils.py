#!/usr/bin/env python
# coding: utf-8

import os


def load_config(config_path=None):
    """Load configuration from environment variables.

    Kept for backward compatibility. The config_path argument is ignored;
    all configuration is read from environment variables.
    """
    return os.environ


def get_api_key(config, section="API_KEYS", key="fmp_api_key"):
    """Retrieve an API key from environment variables.

    Maps legacy config.ini keys to environment variables:
      fmp_api_key       -> FMP_API_KEY
      deepseek_api_key  -> DEEPSEEK_API_KEY
      deepseek_base_url -> DEEPSEEK_BASE_URL
      deepseek_model    -> DEEPSEEK_MODEL
      adanos_api_key    -> ADANOS_API_KEY
      adanos_base_url   -> ADANOS_BASE_URL
    """
    env_map = {
        "fmp_api_key": "FMP_API_KEY",
        "deepseek_api_key": "DEEPSEEK_API_KEY",
        "deepseek_base_url": "DEEPSEEK_BASE_URL",
        "deepseek_model": "DEEPSEEK_MODEL",
        "adanos_api_key": "ADANOS_API_KEY",
        "adanos_base_url": "ADANOS_BASE_URL",
    }
    env_var = env_map.get(key, key.upper())
    value = os.getenv(env_var)
    if value is None:
        raise ValueError(
            f"Environment variable {env_var} not set. "
            f"Copy .env.example to .env and fill in your API keys."
        )
    return value
