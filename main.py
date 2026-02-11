#!/usr/bin/env python3
import argparse
from garak.cli import main as garak_main


def build_garak_args(
    target_type: str,
    target_name: str,
    target_lang: str,
    generations: int,
    seeds: str,
    config: str,
    attackers: str | None,
    eval_threshold: float | None,
    report_prefix: str | None,
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
        "--config",
        config,
    ]

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
    config: str,
    attackers: str | None = None,
    eval_threshold: float | None = None,
    report_prefix: str | None = None,
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
        extra_args=extra_args,
    )
    garak_main(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run garak with function-style inputs")
    parser.add_argument("--target-type", required=True)
    parser.add_argument("--target-name", required=True)
    parser.add_argument("--target-lang", required=True)
    parser.add_argument("--seeds", required=True, help="e.g. dan.DanInTheWild")

    # optional
    parser.add_argument("--config", required=False)
    parser.add_argument("--attackers", required=False)
    parser.add_argument("--generations", required=False, type=int)
    parser.add_argument("--eval-threshold", required=False, type=float)
    parser.add_argument("--report-prefix", required=False)

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
        extra_args=unknown_args,
    )

# 실행 코드 예시
# python3 main.py \
#   --target-type openai \
#   --target-name gpt-4o-mini \
#   --target-lang ko \
#   --generations 1 \
#   --seeds grandma.Win10 \
#   --config run-soft.yaml \
#   --attackers remove_spaces.RemoveSpaces
