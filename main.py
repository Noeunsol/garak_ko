#!/usr/bin/env python3
import sys
from pathlib import Path

# src/ 하위의 garak 패키지를 import할 수 있도록 경로 추가
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import argparse
from garak.cli import main as garak_main


def build_garak_args(
    target_type: str,
    target_name: str,
    target_lang: str,
    generations: int,
    seeds: str,
    config: str | None,
    attackers: str | None,
    eval_threshold: float | None,
    report_prefix: str | None,
    soft_seed_prompt_cap: int | None,
    extra_args: list[str] | None,
) -> list[str]:
    args = [
        "--target_type",
        target_type,
        "--target_name",
        target_name,
        "--target_lang",
        target_lang,
        "--generations",
        str(generations),
        "--seeds",
        seeds,
    ]

    if config:
        args.extend(["--config", config])
    if soft_seed_prompt_cap is not None:
        args.extend(["--soft_seed_prompt_cap", str(soft_seed_prompt_cap)])
    if attackers:
        args.extend(["--attackers", attackers])
    if eval_threshold is not None:
        args.extend(["--eval_threshold", str(eval_threshold)])
    if report_prefix:
        args.extend(["--report_prefix", report_prefix])
    if extra_args:
        args.extend(extra_args)
    return args


def run_garak(
    target_type: str,
    target_name: str,
    target_lang: str,
    generations: int,
    seeds: str,
    config: str | None = None,
    attackers: str | None = None,
    eval_threshold: float | None = None,
    report_prefix: str | None = None,
    soft_seed_prompt_cap: int | None = None,
    extra_args: list[str] | None = None,
) -> None:
    args = build_garak_args(
        target_type=target_type,
        target_name=target_name,
        target_lang=target_lang,
        generations=generations,
        seeds=seeds,
        config=config,
        attackers=attackers,
        eval_threshold=eval_threshold,
        report_prefix=report_prefix,
        soft_seed_prompt_cap=soft_seed_prompt_cap,
        extra_args=extra_args,
    )
    garak_main(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run garak with function-style inputs")
    parser.add_argument("--target_type", required=True)
    parser.add_argument("--target_name", required=True)
    parser.add_argument("--target_lang", required=True)

    # optional
    parser.add_argument("--seeds", required=False, help="e.g. dan.DanInTheWild")
    parser.add_argument("--config", required=False)
    parser.add_argument("--attackers", required=False)
    parser.add_argument("--generations", required=False, type=int)
    parser.add_argument("--soft_seed_prompt_cap", required=False, type=int)
    parser.add_argument("--eval_threshold", required=False, type=float)
    parser.add_argument("--report_prefix", required=False)

    args, unknown_args = parser.parse_known_args()

    run_garak(
        target_type=args.target_type,
        target_name=args.target_name,
        target_lang=args.target_lang,
        generations=args.generations,
        seeds=args.seeds,
        config=args.config,
        attackers=args.attackers,
        eval_threshold=args.eval_threshold,
        report_prefix=args.report_prefix,
        soft_seed_prompt_cap=args.soft_seed_prompt_cap,
        extra_args=unknown_args,
    )

# 실행 코드 예시
# python3 main.py \s
#   --target_type openai \
#   --target_name gpt-4o-mini \
#   --target_lang ko \
#   --generations 1 \
#   --seeds grandma.Win10 \
#   --soft_seed_prompt_cap 3 \
#   --attackers remove_spaces.RemoveSpaces
