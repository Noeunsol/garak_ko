#!/usr/bin/env python3

# SPDX-FileCopyrightText: Portions Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# generate a qualitative review of a garak report
# highlight failing seeds
# give ten +ve and ten -ve examples from failing seeds
# takes report.jsonl, optional bag.json (e.g. data/calibration/calibration.json) as input

from collections import defaultdict
import json
import random
import sys
import argparse

import garak
import garak.analyze
import garak.analyze.calibration
from garak.seeds import Tier

SEED_JUDGE_SEP = "+"


def build_tiers() -> dict:
    from garak._plugins import enumerate_plugins, plugin_info

    tiers = {}
    for tier in Tier:
        tiers[tier] = []

    for plugin, _ in enumerate_plugins("seeds"):
        details = plugin_info(plugin)
        _, plugin_name = plugin.split(".", 1)
        tiers[Tier(details["tier"])].append(plugin_name)

    return tiers


def qual_review(report_path: str) -> None:
    tiers = build_tiers()
    c = garak.analyze.calibration.Calibration()
    seed_judge_scores = {}
    pos_examples = defaultdict(list)
    neg_examples = defaultdict(list)

    print("# garak Qualitative review")
    print(
        "Analysis of failing & passing seeds/judges, grouped by tier, including prompt & response samples for failing entries"
    )
    print("source filename: ", report_path)

    with open(report_path, "r", encoding="utf-8") as report_file:
        g = (json.loads(line.strip()) for line in report_file if line.strip())
        for record in g:
            if record["entry_type"] == "eval":
                passrate = (
                    record["passed"] / record["total_evaluated"]
                    if record["total_evaluated"] > 0
                    else 0
                )
                seed_module, seed_classname = record["seed"].split(".", 1)
                judge = record["judge"].replace("judge.", "")
                judge_module, judge_classname = judge.split(".", 1)
                z = c.get_z_score(
                    seed_module,
                    seed_classname,
                    judge_module,
                    judge_classname,
                    passrate,
                )
                seed_judge_scores[
                    f"{record['seed']}{SEED_JUDGE_SEP}{judge}"
                ] = {
                    "passrate": passrate,
                    "z": z,
                }
            elif record["entry_type"] == "attempt" and record["status"] == 2:
                results = record["judge_results"]
                for judge_name in results:
                    for i, score in enumerate(results[judge_name]):
                        try:
                            fields = [record["prompt"], record["outputs"][i]]
                            if "triggers" in record.get("notes", {}).keys():
                                fields.append(record["notes"]["triggers"])
                            if score > 0.5:
                                pos_examples[
                                    record["seed_classname"]
                                    + SEED_JUDGE_SEP
                                    + judge_name
                                ].append(fields)
                            else:
                                neg_examples[
                                    record["seed_classname"]
                                    + SEED_JUDGE_SEP
                                    + judge_name
                                ].append(fields)
                        except IndexError:
                            continue

    def _print_examples(seed_judge):
        print("\n#### Examples of responses marked failing")
        excerpt = pos_examples[seed_judge]
        random.shuffle(excerpt)
        for index, entry in enumerate(excerpt[0:10]):
            print(f"##### Example {index+1}")
            print()
            print("  * **prompt**:\n```\n" + repr(entry[0]) + "\n```\n")
            if len(entry) == 3:
                print("  * **trigger**:\n```\n" + repr(entry[2]) + "\n```\n")
            print("  * **response**:\n```\n" + repr(entry[1]) + "\n```\n")
            print()
        print("\n#### Examples of responses marked passing")
        excerpt = neg_examples[seed_judge]
        random.shuffle(excerpt)
        for entry in excerpt[0:10]:
            print()
            print("  * **prompt**:\n```\n" + repr(entry[0]) + "\n```\n")
            if len(entry) == 3:
                print("  * **trigger**:\n```\n" + repr(entry[2]) + "\n```\n")
            print("  * **response**:\n```\n" + repr(entry[1]) + "\n```\n")
            print()

    print("## Tier 1 seed results")
    t1_seed_names = tiers[Tier.OF_CONCERN]
    for seed_judge in seed_judge_scores.keys():
        if seed_judge.split(SEED_JUDGE_SEP)[0] in t1_seed_names:
            z, passrate = (
                seed_judge_scores[seed_judge]["z"],
                seed_judge_scores[seed_judge]["passrate"],
            )
            print("\n### Seed and judge: " + seed_judge)
            print(f"\n\n * passrate: `{passrate:0.4f}`\n * z: `{z}`\n\n")
            if passrate < garak.analyze.ABSOLUTE_DEFCON_BOUNDS.BELOW_AVG or (
                z is not None and z < garak.analyze.RELATIVE_DEFCON_BOUNDS.BELOW_AVG
            ):
                print("Issues found:")
                if passrate < garak.analyze.ABSOLUTE_DEFCON_BOUNDS.BELOW_AVG:
                    print(f"* low pass rate `{passrate:0.4f}`")
                if z is not None and z < garak.analyze.RELATIVE_DEFCON_BOUNDS.BELOW_AVG:
                    print(f"* low z         `{z:-0.4f}`")
                _print_examples(seed_judge)
            else:
                print("All performance within bounds")

    print("## Tier 2 seed results")
    t2_seed_names = tiers[Tier.COMPETE_WITH_SOTA]
    for seed_judge in seed_judge_scores.keys():
        if seed_judge.split(SEED_JUDGE_SEP)[0] in t2_seed_names:
            z, passrate = (
                seed_judge_scores[seed_judge]["z"],
                seed_judge_scores[seed_judge]["passrate"],
            )
            print("\n### Seed and judge: " + seed_judge)
            print(f"\n\n * passrate: `{passrate:0.4f}`\n * z: `{z}`\n\n")
            if z is not None and z < garak.analyze.RELATIVE_DEFCON_BOUNDS.BELOW_AVG:
                print("Issues found:")
                print(f"* low z   `{z:-0.4f}`")
                _print_examples(seed_judge)
            else:
                print("All performance within bounds")

    print("\n## Seed/judge pairs not processed:")
    t1_t2_seeds = t1_seed_names + t2_seed_names
    for entry in [
        seed_judge
        for seed_judge in seed_judge_scores.keys()
        if seed_judge.split(SEED_JUDGE_SEP)[0] not in t1_t2_seeds
    ]:
        print("*", entry)


def main(argv=None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    garak._config.load_config()
    print(
        f"garak {garak.__description__} v{garak._config.version} ( https://github.com/NVIDIA/garak )"
    )

    parser = argparse.ArgumentParser(
        prog="python -m garak.analyze.qual_review",
        description="Qualitative review of failing/passing seeds and judges with sample prompts/responses",
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
    qual_review(report_path)


if __name__ == "__main__":
    main()
