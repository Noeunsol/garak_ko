# SPDX-FileCopyrightText: Portions Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Flow for invoking garak from the command line"""

command_options = "list_judges list_seeds list_seed_groups list_targets list_attackers list_attackers list_config plugin_info interactive report version fix".split()


def parse_cli_plugin_config(plugin_type, args):
    import os
    import json
    import logging

    opts_arg = f"{plugin_type}_options"
    opts_file = f"{plugin_type}_option_file"
    opts_cli_config = None
    if opts_arg in args or opts_file in args:
        if opts_arg in args:
            opts_argv = getattr(args, opts_arg)
            try:
                opts_cli_config = json.loads(opts_argv)
            except json.JSONDecodeError as e:
                logging.warning("Failed to parse JSON %s: %s", opts_arg, e.args[0])

        elif opts_file in args:
            file_arg = getattr(args, opts_file)
            if not os.path.isfile(file_arg):
                raise FileNotFoundError(f"Path provided is not a file: {opts_file}")
            with open(file_arg, encoding="utf-8") as f:
                options_json = f.read().strip()
            try:
                opts_cli_config = json.loads(options_json)
            except json.decoder.JSONDecodeError as e:
                logging.warning("Failed to parse JSON %s: %s", opts_file, {e.args[0]})
                raise e
    return opts_cli_config


def _load_seed_groups_file(groups_file):
    """Load seed groups from YAML.

    The YAML can be either:
    - {seed_groups: {name: spec, ...}}
    - {seed_groups: [{id: ..., run: {seeds: [...]}, ...}, ...]}
    - {groups: [{id: ..., run: {seeds: [...]}, ...}, ...]}
    - {name: spec, ...}
    Where spec is a string (comma-separated seed_spec) or a list[str].
    """
    import os
    import yaml

    if groups_file is None:
        raise ValueError("seed groups file path is None")
    if not os.path.exists(groups_file):
        raise FileNotFoundError(f"Seed groups file not found: {groups_file}")

    with open(groups_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Seed groups file must be a YAML mapping, got: {type(data)}")

    if "groups" in data or (
        "seed_groups" in data and isinstance(data.get("seed_groups"), list)
    ):
        groups_list = data.get("groups")
        if groups_list is None:
            groups_list = data.get("seed_groups")
        groups_list = groups_list or []
        if not isinstance(groups_list, list):
            raise ValueError(
                f"'groups'/'seed_groups' must be a list, got: {type(groups_list)}"
            )
        groups = {}
        for entry in groups_list:
            if not isinstance(entry, dict):
                raise ValueError(
                    f"Each group entry must be a mapping, got: {type(entry)}"
                )
            gid = entry.get("id")
            if not isinstance(gid, str) or not gid.strip():
                raise ValueError("Each group entry must have a non-empty string 'id'")
            if gid in groups:
                raise ValueError(f"Duplicate seed group id: {gid}")
            groups[gid] = entry
        return groups

    groups = data.get("seed_groups", data)
    if groups is None:
        return {}
    if not isinstance(groups, dict):
        raise ValueError(
            f"'seed_groups' must be a mapping of name->spec, got: {type(groups)}"
        )
    return groups


def _spec_from_group_value(v) -> str:
    # New-style group descriptor: {id, name?, run: {seeds: [...]}, ...}
    if isinstance(v, dict):
        run = v.get("run", {}) if isinstance(v.get("run", {}), dict) else {}
        seeds = run.get("seeds", [])
        if isinstance(seeds, list):
            seed_names = []
            for p in seeds:
                if isinstance(p, str):
                    seed_names.append(p.strip())
                elif isinstance(p, dict) and isinstance(p.get("seed"), str):
                    seed_names.append(p["seed"].strip())
            return ",".join([p for p in seed_names if p])
        return ""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, list) and all(isinstance(i, str) for i in v):
        return ",".join([i.strip() for i in v if i.strip()])
    raise ValueError(
        f"Seed group spec must be a string or list[str], got: {type(v)}"
    )


def _merge_seed_specs(base_spec: str | None, extra_spec: str | None) -> str:
    base = (base_spec or "").strip()
    extra = (extra_spec or "").strip()
    if extra == "":
        return base
    if base == "" or base.lower() in ("auto", "none"):
        return extra
    if base.lower() in ("all", "*"):
        return base

    base_items = [i.strip() for i in base.split(",") if i.strip()]
    extra_items = [i.strip() for i in extra.split(",") if i.strip()]

    seen = set()
    merged = []
    for item in base_items + extra_items:
        if item in seen:
            continue
        seen.add(item)
        merged.append(item)
    return ",".join(merged)


def _apply_group_run_overrides(group_desc: dict):
    """Apply run/seed overrides from a new-style seed group descriptor."""
    from garak import _config

    run = group_desc.get("run", {})
    if not isinstance(run, dict):
        return

    # Basic run-level knobs
    for k, v in run.items():
        if k == "seeds":
            continue
        # only set known run attrs; ignore unknown keys to keep groups future-proof
        if hasattr(_config.run, k):
            setattr(_config.run, k, v)

    # Per-seed params
    seeds = run.get("seeds", [])
    if not isinstance(seeds, list):
        return
    for p in seeds:
        if not isinstance(p, dict):
            continue
        seed_name = p.get("seed")
        params = p.get("params", {})
        if not isinstance(seed_name, str) or not seed_name.strip():
            continue
        if params is None:
            params = {}
        if not isinstance(params, dict):
            raise ValueError(
                f"Seed params for {seed_name} must be a dict, got: {type(params)}"
            )
        # Config schema: plugins.seeds.<namespace>.<ClassName>.<param>
        if "." not in seed_name:
            # module-only; no class-level params supported here
            continue
        namespace, classname = seed_name.split(".", 1)
        namespace = namespace.strip()
        classname = classname.strip()
        if not namespace or not classname:
            continue
        if namespace not in _config.plugins.seeds:
            _config.plugins.seeds[namespace] = {}
        if classname not in _config.plugins.seeds[namespace]:
            _config.plugins.seeds[namespace][classname] = {}
        if not isinstance(_config.plugins.seeds[namespace][classname], dict):
            _config.plugins.seeds[namespace][classname] = {}
        _config.plugins.seeds[namespace][classname].update(params)


def _expand_matrix(matrix: dict) -> list[dict]:
    """Expand a matrix mapping into a list of override dicts (cartesian product).

    Example:
      {"target_lang": ["ko", "en"], "soft_seed_prompt_cap": [1, 5]}
    """
    if matrix is None:
        return []
    if not isinstance(matrix, dict):
        raise ValueError(f"matrix must be a mapping, got: {type(matrix)}")
    items = []
    for k, v in matrix.items():
        if isinstance(v, list):
            items.append((k, v))
        else:
            raise ValueError(f"matrix values must be lists; {k} was {type(v)}")

    if not items:
        return []

    # iterative cartesian product
    combos = [dict()]
    for k, vals in items:
        new_combos = []
        for c in combos:
            for val in vals:
                cc = dict(c)
                cc[k] = val
                new_combos.append(cc)
        combos = new_combos
    return combos


def main(arguments=None) -> None:
    """Main entry point for garak runs invoked from the CLI"""
    import datetime

    from garak import __description__
    from garak import _config, _plugins
    from garak.exception import GarakException

    _config.transient.starttime = datetime.datetime.now()
    _config.transient.starttime_iso = _config.transient.starttime.isoformat()

    if arguments is None:
        arguments = []

    import garak.command as command
    import logging
    import re
    from colorama import Fore, Style

    log_filename = command.start_logging()
    _config.load_base_config()

    print(
        f"garak {__description__} v{_config.version} ( https://github.com/NVIDIA/garak ) at {_config.transient.starttime_iso}"
    )

    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m garak",
        description="LLM safety & security scanning tool",
        epilog="See https://github.com/NVIDIA/garak",
        allow_abbrev=False,
    )

    ## SYSTEM
    parser.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=_config.system.verbose,
        help="add one or more times to increase verbosity of output during runtime",
    )
    parser.add_argument(
        "--report_prefix",
        type=str,
        default=_config.reporting.report_prefix,
        help="Specify an optional prefix for the report and hit logs",
    )
    parser.add_argument(
        "--narrow_output",
        action="store_true",
        help="give narrow CLI output",
    )
    parser.add_argument(
        "--parallel_requests",
        type=int,
        default=_config.system.parallel_requests,
        help="How many target requests to launch in parallel for a given prompt. Ignored for models that support multiple generations per call.",
    )
    parser.add_argument(
        "--parallel_attempts",
        type=int,
        default=_config.system.parallel_attempts,
        help="How many seed attempts to launch in parallel. Raise this for faster runs when using non-local models.",
    )
    parser.add_argument(
        "--skip_unknown",
        action="store_true",
        help="allow skip of unknown seeds, judges, or attackers",
    )

    ## RUN
    parser.add_argument(
        "--seed",
        "-s",
        type=int,
        default=_config.run.seed,
        help="random seed",
    )
    parser.add_argument(
        "--deprefix",
        action="store_false",
        help="remove the prompt from the front of target output",
    )
    parser.add_argument(
        "--eval_threshold",
        type=float,
        default=_config.run.eval_threshold,
        help="minimum threshold for a successful hit",
    )
    parser.add_argument(
        "--generations",
        "-g",
        type=int,
        default=_config.run.generations,
        help="number of generations per prompt",
    )
    parser.add_argument(
        "--soft_seed_prompt_cap",
        type=int,
        default=None,
        help="max number of prompts per seed (overrides config value)",
    )
    parser.add_argument(
        "--config", type=str, default=None, help="YAML or JSON config file for this run"
    )

    ## PLUGINS
    # targets
    parser.add_argument(
        "--target_type",
        "-t",
        "--model_type",
        "-m",
        type=str,
        help="module and optionally also class of the target, e.g. 'huggingface', or 'openai'",
    )
    parser.add_argument(
        "--target_name",
        "--model_name",
        "-n",
        type=str,
        default=None,
        help="name of the target, e.g. 'timdettmers/guanaco-33b-merged'",
    )
    # seeds
    parser.add_argument(
        "--seeds",
        "-p",
        type=str,
        default=_config.plugins.seed_spec,
        help="list of seed names to use, or 'all' for all (default).",
    )
    parser.add_argument(
        "--seed_group",
        type=str,
        default=None,
        help="seed group id(s) to run; comma-separated (e.g. 'smoke_ko,fast_sanity_check'). Groups are defined in seed_groups.yaml; see --list_seed_groups.",
    )
    parser.add_argument(
        "--seed_groups_file",
        type=str,
        default=None,
        help="path to a YAML file defining seed_groups (defaults to garak/resources/seed_groups.yaml). New-style schema: seed_groups: [{id,name,run:{target_lang,generations,soft_seed_prompt_cap,seeds:[{seed,params}]},matrix:{...}}, ...].",
    )
    parser.add_argument(
        "--seed_tags",
        default=_config.run.seed_tags,
        type=str,
        help="only include seeds with a tag that starts with this value (e.g. owasp:llm01)",
    )
    # judges
    parser.add_argument(
        "--judges",
        "-d",
        type=str,
        default=_config.plugins.judge_spec,
        help="list of judges to use, or 'all' for all. Default is to use the seed's suggestion.",
    )
    parser.add_argument(
        "--extended_judges",
        action="store_true",
        help="If judges aren't specified on the command line, should we run all judges? (default is just the primary judge, if given, else everything)",
    )
    # attackers (formerly "attackers")
    parser.add_argument(
        "--attackers",
        "-attack",
        type=str,
        default=getattr(
            _config.plugins, "attacker_spec", getattr(_config.plugins, "attacker_spec", "")
        ),
        help="list of attackers to use. Default is none",
    )
    ## Language
    parser.add_argument(
        "--target_lang",
        "--language",
        "--lang",
        type=str,
        default=_config.run.target_lang,
        help="specify a language to be used for the target model. e.g. 'en', 'ko'",
    )
    # file or json based config options
    plugin_types = sorted(
        zip([type.lower() for type in _plugins.PLUGIN_CLASSES], _plugins.PLUGIN_TYPES)
    )
    for plugin_type, _ in plugin_types:
        seed_args = parser.add_mutually_exclusive_group()
        seed_args.add_argument(
            f"--{plugin_type}_option_file",
            f"-{plugin_type[0].upper()}",
            type=str,
            help=f"path to JSON file containing options to pass to {plugin_type}",
        )
        seed_args.add_argument(
            f"--{plugin_type}_options",
            type=str,
            help=f"options to pass to {plugin_type}, formatted as a JSON dict",
        )
    ## REPORTING
    parser.add_argument(
        "--taxonomy",
        type=str,
        default=_config.reporting.taxonomy,
        help="specify a MISP top-level taxonomy to be used for grouping seeds in reporting. e.g. 'avid-effect', 'owasp' ",
    )

    ## COMMANDS
    # items placed here also need to be listed in command_options below
    parser.add_argument(
        "--plugin_info",
        type=str,
        help="show info about one plugin; format as type.plugin.class, e.g. seeds.lmrc.Profanity",
    )
    parser.add_argument(
        "--list_seeds",
        action="store_true",
        help="list all available seeds. Usage: combine with --seeds/-p to filter for seeds that will be activated based on a `seed_spec`, e.g. '--list_seeds -p dan' to show only active 'dan' family seeds.",
    )
    parser.add_argument(
        "--list_seed_groups",
        action="store_true",
        help="list seed groups available from the seed groups file (see --seed_groups_file).",
    )
    parser.add_argument(
        "--list_judges",
        action="store_true",
        help="list available judges. Usage: combine with --judges/-d to filter for judges that will be activated based on a `judge_spec`, e.g. '--list_judges -d misleading.Invalid' to show only that judge.",
    )
    parser.add_argument(
        "--list_targets",
        action="store_true",
        help="list available generation model interfaces",
    )
    parser.add_argument(
        "--list_attackers",
        action="store_true",
        help="list available attackers (formerly attackers/fuzzes)",
    )
    parser.add_argument(
        "--list_config",
        action="store_true",
        help="print active config info (and don't scan)",
    )
    parser.add_argument(
        "--version",
        "-V",
        action="store_true",
        help="print version info & exit",
    )
    parser.add_argument(
        "--report",
        "-r",
        type=str,
        help="process garak report into a list of AVID reports",
    )
    parser.add_argument(
        "--interactive",
        "-I",
        action="store_true",
        help="Enter interactive probing mode",
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="Update provided configuration with fixer migrations; requires one of --config / --*_option_file, / --*_options",
    )

    ## EXPERIMENTAL FEATURES
    if _config.system.enable_experimental:
        # place parser argument defs for experimental features here
        parser.description = (
            str(parser.description) + " - EXPERIMENTAL FEATURES ENABLED"
        )

    logging.debug("args - raw argument string received: %s", arguments)

    args = parser.parse_args(arguments)
    logging.debug("args - full argparse: %s", args)

    for deprecated_model_option in {"-m", "--model_name", "--model_type"}.intersection(
        set(arguments)
    ):
        command.deprecation_notice(f"{deprecated_model_option} on CLI", "0.13.1.pre1")

    # load site config before loading CLI config
    _cli_config_supplied = args.config is not None
    prior_user_agents = _config.get_http_lib_agents()
    try:
        _config.load_config(run_config_filename=args.config)
    except FileNotFoundError as e:
        logging.exception(e)
        print(f"❌{e}")
        exit(1)

    # extract what was actually passed on CLI; use a masking argparser
    aux_parser = argparse.ArgumentParser(argument_default=argparse.SUPPRESS)
    # print('VARS', vars(args))
    # aux_parser is going to get sys.argv and so also needs the argument shortnames
    # will extract those from parser internals and use them to populate aux_parser
    arg_names = {}
    for action in parser._actions:
        raw_option_strings = [
            re.sub("^" + re.escape(parser.prefix_chars) + "+", "", a)
            for a in action.option_strings
        ]
        if "help" not in raw_option_strings:
            for raw_option_string in raw_option_strings:
                arg_names[raw_option_string] = action.option_strings

    for arg, val in vars(args).items():
        if arg == "verbose":
            # the 'verbose' flag is currently unique and retrieved from `args` directly
            continue
        if isinstance(val, bool):
            if val:
                aux_parser.add_argument(*arg_names[arg], action="store_true")
            else:
                aux_parser.add_argument(*arg_names[arg], action="store_false")
        else:
            aux_parser.add_argument(*arg_names[arg], type=type(val))

    # cli_args contains items specified on CLI; the rest not to be overridden
    cli_args, _ = aux_parser.parse_known_args(arguments)

    # exception: action=count. only verbose uses this, let's bubble it through
    cli_args.verbose = args.verbose

    # print('ARGS', args)
    # print('CLI_ARGS', cli_args)

    # also force command vars through to cli_args, even if false, to make command code easier
    for command_option in command_options:
        setattr(cli_args, command_option, getattr(args, command_option))

    logging.debug("args - cli_args&commands stored: %s", cli_args)

    del args
    args = cli_args
    # stash cli_args
    _config.transient.cli_args = cli_args

    # save args info into config
    # need to know their type: plugin, system, or run
    # ignore params not listed here
    # - sorry, this means duping stuff, i know. maybe better argparse setup will help
    ignored_params = []
    for param, value in vars(args).items():
        if param in _config.system_params:
            setattr(_config.system, param, value)
        elif param in _config.run_params:
            setattr(_config.run, param, value)
        elif param in _config.plugins_params:
            setattr(_config.plugins, param, value)
        elif param in _config.reporting_params:
            setattr(_config.reporting, param, value)
        else:
            ignored_params.append((param, value))
    logging.debug("non-config params: %s", ignored_params)

    # put plugin spec into the _spec config value, if set at cli
    if "seeds" in args:
        _config.plugins.seed_spec = args.seeds
    if "judges" in args:
        _config.plugins.judge_spec = args.judges
    if "attackers" in args:
        _config.plugins.attacker_spec = args.attackers
    if "target_lang" in args:
        _config.run.target_lang = args.target_lang

    # expand seed groups (CLI convenience) into the seed_spec used by the run
    if getattr(args, "seed_group", None):
        from pathlib import Path

        groups_file = (
            Path(args.seed_groups_file)
            if getattr(args, "seed_groups_file", None)
            else (_config.transient.package_dir / "resources" / "seed_groups.yaml")
        )
        groups = _load_seed_groups_file(str(groups_file))
        group_names = [g.strip() for g in str(args.seed_group).split(",") if g.strip()]
        missing = [g for g in group_names if g not in groups]
        if missing:
            available = ", ".join(sorted(groups.keys()))
            raise ValueError(
                f"Unknown seed group(s): {', '.join(missing)}. Available: {available}"
            )
        # apply new-style run overrides and collect matrix (if any)
        matrices = []
        for g in group_names:
            if isinstance(groups[g], dict):
                _apply_group_run_overrides(groups[g])
                if "matrix" in groups[g]:
                    matrices.append((g, groups[g].get("matrix")))

        if len(matrices) > 1:
            raise ValueError(
                "Multiple selected seed groups define 'matrix'. Select one matrix group at a time."
            )
        if len(matrices) == 1:
            setattr(args, "_seed_group_matrix", matrices[0][1])
            setattr(args, "_seed_group_matrix_id", matrices[0][0])

        group_spec = ",".join([_spec_from_group_value(groups[g]) for g in group_names])
        # If the user didn't explicitly pass --seeds, treat it as empty so groups act
        # like a selector instead of being merged with the configured default.
        base_spec = getattr(args, "seeds", None) if ("seeds" in args) else ""
        merged_spec = _merge_seed_specs(base_spec, group_spec)
        _config.plugins.seed_spec = merged_spec
        # also reflect into args for downstream command handlers
        setattr(args, "seeds", merged_spec)

    # base config complete

    # post-config validation
    def worker_count_validation(workers):
        iworkers = int(workers)
        if iworkers <= 0:
            raise ValueError(
                "Need a number > 0 for --parallel_attempts, --parallel_requests"
            )
        if iworkers > _config.system.max_workers:
            raise ValueError(
                "Parallel worker count capped at %s (config.system.max_workers), try a lower value for --parallel_attempts or --parallel_requests"
                % _config.system.max_workers
            )
        return iworkers

    try:
        if _config.system.parallel_attempts is not False:
            _config.system.parallel_attempts = worker_count_validation(
                _config.system.parallel_attempts
            )

        if _config.system.parallel_requests is not False:
            _config.system.parallel_requests = worker_count_validation(
                _config.system.parallel_requests
            )
    except ValueError as e:
        logging.exception(e)
        print(e)
        exit(1)  # exit non zero indicated parsing error

    if hasattr(_config.run, "seed") and isinstance(_config.run.seed, int):
        import random

        random.seed(
            _config.run.seed
        )  # setting seed persists across re-imports of random

    # startup
    import sys
    import json

    import garak.evaluators

    try:
        has_config_file_or_json = False
        # do a special thing for CLI seed options, target options
        for plugin_type, plugin_plural in plugin_types:
            opts_cli_config = parse_cli_plugin_config(plugin_type, args)
            if opts_cli_config is not None:
                has_config_file_or_json = True
                config_plugin_type = getattr(_config.plugins, plugin_plural)

                config_plugin_type = _config._combine_into(
                    opts_cli_config, config_plugin_type
                )

        # process commands
        if args.interactive:
            from garak.interactive import interactive_mode

            try:
                command.start_run()  # start run to track actions
                interactive_mode()
            except Exception as e:
                logging.error(e)
                print(e)
                sys.exit(1)
            finally:
                command.end_run()

        if args.version:
            pass

        elif args.plugin_info:
            command.plugin_info(args.plugin_info)

        elif args.list_seeds:
            selected_seeds = None
            seed_spec = getattr(args, "seeds", None)
            if seed_spec and seed_spec.lower() not in ("", "auto", "all", "*"):
                selected_seeds, _ = _config.parse_plugin_spec(seed_spec, "seeds")
            command.print_seeds(selected_seeds)

        elif args.list_seed_groups:
            from pathlib import Path

            groups_file = (
                Path(args.seed_groups_file)
                if getattr(args, "seed_groups_file", None)
                else (_config.transient.package_dir / "resources" / "seed_groups.yaml")
            )
            groups = _load_seed_groups_file(str(groups_file))
            print(f"Seed groups from {groups_file}:")
            for name in sorted(groups.keys()):
                desc = groups[name]
                if isinstance(desc, dict):
                    label = desc.get("name", "")
                    label = f" ({label})" if isinstance(label, str) and label else ""
                    run = desc.get("run", {}) if isinstance(desc.get("run", {}), dict) else {}
                    run_bits = []
                    for k in ("target_lang", "soft_seed_prompt_cap", "generations"):
                        if k in run:
                            run_bits.append(f"{k}={run[k]}")
                    run_str = f" [{' '.join(run_bits)}]" if run_bits else ""
                    matrix = desc.get("matrix", None)
                    matrix_str = " [matrix]" if matrix else ""
                    print(
                        f"  {name}{label}:{run_str}{matrix_str} {_spec_from_group_value(desc)}"
                    )
                else:
                    print(f"  {name}: {_spec_from_group_value(desc)}")

        elif args.list_judges:
            selected_judges = None
            judge_spec = getattr(args, "judges", None)
            if judge_spec and judge_spec.lower() not in ("", "auto", "all", "*"):
                selected_judges, _ = _config.parse_plugin_spec(
                    judge_spec, "judges"
                )
            command.print_judges(selected_judges)

        elif getattr(args, "list_attackers", False) or getattr(args, "list_attackers", False):
            command.print_attackers()

        elif args.list_targets:
            command.print_targets()

        elif args.list_config:
            print("cli args:\n ", args)
            command.list_config()

        elif args.fix:
            from garak.resources import fixer
            import json
            import yaml

            # process all possible configuration entries
            # should this restrict the config updates to a single fixable value?
            # for example allowed commands:
            # --fix --config filename.yaml
            # --fix --target_option_file filename.json
            # --fix --target_options json
            #
            # disallowed commands:
            # --fix --config filename.yaml --target_option_file filename.json
            # --fix --target_option_file filename.json --seed_option_file filename.json
            #
            # already unsupported as only one is held:
            # --fix --target_option_file filename.json --target_options json_data
            #
            # How should this handle garak.site.yaml? Only if --fix was provided and no other options offered?
            # For now process all files registered a part of the config
            has_changes = False
            if has_config_file_or_json:
                for plugin_type, plugin_plural in plugin_types:
                    # cli plugins options stub out only a "plugins" sub key
                    plugin_cli_config = parse_cli_plugin_config(plugin_type, args)
                    if plugin_cli_config is not None:
                        cli_config = {
                            "plugins": {f"{plugin_plural}": plugin_cli_config}
                        }
                        migrated_config = fixer.migrate(cli_config)
                        if cli_config != migrated_config:
                            has_changes = True
                            msg = f"Updated '{plugin_type}' configuration: \n"
                            msg += json.dumps(
                                migrated_config["plugins"][plugin_plural], indent=2
                            )  # pretty print the config in json
                            print(msg)
            else:
                # check if garak.site.yaml needs to be fixed up?
                for filename in _config.config_files:
                    with open(filename, encoding="UTF-8") as file:
                        cli_config = yaml.safe_load(file)
                        migrated_config = fixer.migrate(cli_config)
                        if cli_config != migrated_config:
                            has_changes = True
                            msg = f"Updated {filename}: \n"
                            msg += yaml.dump(migrated_config)
                            print(msg)
            # should this add support for --*_spec entries passed on cli?
            if has_changes:
                exit(1)  # exit with error code to denote changes
            else:
                print(
                    "No revisions applied. Please verify options provided for `--fix`"
                )
        elif args.report:
            from garak.report import Report

            report_location = args.report
            print(f"📜 Converting garak reports {report_location}")
            report = Report(args.report).load().get_evaluations()
            report.export()
            print(f"📜 AVID reports generated at {report.write_location}")

        # model is specified, we're doing something
        elif _config.plugins.target_type:

            print(f"📜 logging to {log_filename}")

            conf_root = _config.plugins.targets
            for part in _config.plugins.target_type.split("."):
                if not part in conf_root:
                    conf_root[part] = {}
                conf_root = conf_root[part]
            if _config.plugins.target_name:
                # if passed target options and config files are already loaded
                # cli provided name overrides config from file
                conf_root["name"] = _config.plugins.target_name

            # Can this check be deferred to the target instantiation?
            if (
                _config.plugins.target_type
                in ("openai", "replicate", "ggml", "huggingface", "litellm")
                and not _config.plugins.target_name
            ):
                message = f"⚠️  Model type '{_config.plugins.target_type}' also needs a model name\n You can set one with e.g. --target_name \"billwurtz/gpt-1.0\""
                logging.error(message)
                raise ValueError(message)

            parsable_specs = ["seed", "judge", "attacker"]
            parsed_specs = {}
            for spec_type in parsable_specs:
                spec_namespace = f"{spec_type}s"
                config_spec = getattr(_config.plugins, f"{spec_type}_spec", "")
                config_tags = getattr(_config.run, f"{spec_type}_tags", "")
                names, rejected = _config.parse_plugin_spec(
                    config_spec, spec_namespace, config_tags
                )
                parsed_specs[spec_type] = names
                if rejected is not None and len(rejected) > 0:
                    if hasattr(args, "skip_unknown"):  # attribute only set when True
                        header = f"Unknown {spec_namespace}:"
                        skip_msg = Fore.LIGHTYELLOW_EX + "SKIP" + Style.RESET_ALL
                        msg = f"{Fore.LIGHTYELLOW_EX}{header}\n" + "\n".join(
                            [f"{skip_msg} {spec}" for spec in rejected]
                        )
                        logging.warning(f"{header} " + ",".join(rejected))
                        print(msg)
                    else:
                        msg_list = ",".join(rejected)
                        raise ValueError(f"❌Unknown {spec_namespace}❌: {msg_list}")

            evaluator = garak.evaluators.ThresholdEvaluator(_config.run.eval_threshold)

            from garak import _plugins

            target = _plugins.load_plugin(
                f"targets.{_config.plugins.target_type}", config_root=_config
            )

            if (
                not _cli_config_supplied
                and target.parallel_capable
                and _config.system.parallel_attempts is False
            ):
                command.hint(
                    f"This run can be sped up 🥳 Target '{target.fullname}' supports parallelism! Consider using `--parallel_attempts 16` (or more) to greatly accelerate your run. 🐌",
                    logging=logging,
                )

            def _run_once():
                command.start_run()  # start the run now that all config validation is complete
                print(f"📜 reporting to {_config.transient.report_filename}")

                if parsed_specs["judge"] == []:
                    command.seedwise_run(
                        target,
                        parsed_specs["seed"],
                        evaluator,
                        parsed_specs["attacker"],
                    )
                else:
                    command.pxd_run(
                        target,
                        parsed_specs["seed"],
                        parsed_specs["judge"],
                        evaluator,
                        parsed_specs["attacker"],
                    )

                command.end_run()

            matrix = getattr(args, "_seed_group_matrix", None)
            if matrix:
                import datetime

                base_prefix = _config.reporting.report_prefix
                matrix_id = getattr(args, "_seed_group_matrix_id", "matrix")
                combos = _expand_matrix(matrix)
                if not combos:
                    _run_once()
                else:
                    for combo in combos:
                        # Ensure seeds/judges reload with current _config (esp target_lang)
                        _plugins.PluginProvider.clear_cache()

                        # Apply matrix overrides to run config
                        for k, v in combo.items():
                            if hasattr(_config.run, k):
                                setattr(_config.run, k, v)

                        # Make report filename deterministic and unique per combo
                        suffix = ".".join([f"{k}-{v}" for k, v in combo.items()])
                        if base_prefix:
                            _config.reporting.report_prefix = f"{base_prefix}.{matrix_id}.{suffix}"
                        else:
                            _config.reporting.report_prefix = f"{matrix_id}.{suffix}"

                        _config.transient.starttime = datetime.datetime.now()
                        _config.transient.starttime_iso = _config.transient.starttime.isoformat()

                        _run_once()

                    # restore
                    _config.reporting.report_prefix = base_prefix
            else:
                _run_once()
        else:
            print("nothing to do 🤷  try --help")
            if _config.plugins.target_name and not _config.plugins.target_type:
                print(
                    "💡 try setting --target_type (--target_name is currently set but not --target_type)"
                )
            logging.info("nothing to do 🤷")
    except KeyboardInterrupt as e:
        msg = "User cancel received, terminating all runs"
        logging.exception(e)
        logging.info(msg)
        print(msg)
    except (ValueError, GarakException) as e:
        logging.exception(e)
        print(e)

    _config.set_http_lib_agents(prior_user_agents)
