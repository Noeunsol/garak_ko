#!/usr/bin/env python3
"""
Convenience runner for garak with opinionated defaults.

기본값은 아래 DEFAULT_ARGS에 정의되어 있고,
CLI 인자를 추가로 주면 그 인자가 덮어씁니다.

예)
  python main.py
  python main.py --probes lmrc.Sexualisation --generations 2
"""
import sys
from garak.cli import main as garak_main

# 원하는 기본값으로 수정하세요.
DEFAULT_ARGS = [
    "--target_type",
    "openai",
    "--target_name",
    "gpt-4o-mini",
    "--target_lang",
    "ko",
    "--generations",
    "1",
    "--probes",
    "lmrc.Bullying",
    "--buffs",
    "remove_spaces.RemoveSpaces",
    "--config",
    "run-soft.yaml"
]


def build_args():
    """Merge defaults with user-supplied CLI args (user args override)."""
    return DEFAULT_ARGS + sys.argv[1:]


if __name__ == "__main__":
    garak_main(build_args())
