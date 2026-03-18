#!/usr/bin/env python3

# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""
count the number of characters and tokens sent and received based on prompts, outputs, and generations

자모 분해 방식으로 토큰을 계산합니다:
- 영어: 글자 수 = 토큰 수 (a→1, hello→5)
- 한국어: 초성+중성+종성 분해 수 (ㄱ→1, 안→3, 안녕→6)

한/영 동일 의미의 텍스트가 동등한 정보량으로 측정됩니다.

usage

./count_tokens.py <report.jsonl filename>
"""

import json
import sys
import argparse

import garak


def _to_text(o):
    """attempt/output 객체에서 텍스트를 추출"""
    if isinstance(o, str):
        return o
    if isinstance(o, dict):
        for k in ("text", "content", "response"):
            v = o.get(k)
            if isinstance(v, str):
                return v
    return str(o)


def _count_jamo(text: str) -> int:
    """영어는 글자 수, 한국어는 자모 분해 수로 토큰 계산"""
    count = 0
    for ch in text:
        if "\uAC00" <= ch <= "\uD7A3":
            # 한글 음절 → 초성+중성(+종성) 분해
            final = (ord(ch) - 0xAC00) % 28
            count += 3 if final else 2
        elif "\u3131" <= ch <= "\u3163":
            count += 1  # 단독 자모
        elif ch.isspace():
            continue
        else:
            count += 1  # 영어/숫자/기타
    return count


def count_tokens(report_path: str) -> None:
    calls = 0
    input_chars = 0
    output_chars = 0
    input_tokens = 0
    output_tokens = 0
    generations = 10

    with open(report_path, encoding="utf-8") as reportfile:
        for line in reportfile:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            if "run.generations" in r:
                generations = r["run.generations"]
                continue
            if "status" in r and r["status"] == 2:
                prompt_text = _to_text(r.get("prompt", ""))
                input_chars += len(prompt_text) * generations
                input_tokens += _count_jamo(prompt_text) * generations
                calls += generations

                outputs = r.get("outputs", [])
                if isinstance(outputs, list):
                    output_text = "".join(_to_text(o) for o in outputs)
                else:
                    output_text = str(outputs)
                output_chars += len(output_text)
                output_tokens += _count_jamo(output_text)

    total_chars = input_chars + output_chars
    total_tokens = input_tokens + output_tokens

    print(f"Calls: {calls}")
    print(f"{'':>9s} {'chars':>10s} {'tokens':>10s}")
    print(f"{'Input':>9s} {input_chars:>10,} {input_tokens:>10,}")
    print(f"{'Output':>9s} {output_chars:>10,} {output_tokens:>10,}")
    print(f"{'Total':>9s} {total_chars:>10,} {total_tokens:>10,}")


def main(argv=None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    garak._config.load_config()
    print(
        f"garak {garak.__description__} v{garak._config.version} ( https://github.com/NVIDIA/garak )"
    )

    parser = argparse.ArgumentParser(
        prog="python -m garak.analyze.count_tokens",
        description="Count approximate token-like character totals from a garak JSONL report",
        epilog="See https://github.com/NVIDIA/garak",
        allow_abbrev=False,
    )
    parser.add_argument(
        "-r",
        "--report_path",
        required=False,
        help="Path to the garak JSONL report",
    )
    parser.add_argument(
        "report_path_positional",
        nargs="?",
        help="Path to the garak JSONL report (positional)",
    )
    args = parser.parse_args(argv)
    report_path = args.report_path or args.report_path_positional
    if not report_path:
        parser.error("a report path is required (positional or -r/--report_path)")

    sys.stdout.reconfigure(encoding="utf-8")
    count_tokens(report_path)


if __name__ == "__main__":
    main()
