CLI reference for garak
=======================

::

  garak LLM vulnerability scanner v0.14.0.pre1 ( https://github.com/NVIDIA/garak ) at 2026-01-12T10:55:00.848157
  usage: python -m garak [-h] [--verbose] [--report_prefix REPORT_PREFIX]
                         [--narrow_output]
                         [--parallel_requests PARALLEL_REQUESTS]
                         [--parallel_attempts PARALLEL_ATTEMPTS]
                         [--skip_unknown] [--seed SEED] [--deprefix]
                         [--eval_threshold EVAL_THRESHOLD]
                         [--generations GENERATIONS] [--config CONFIG]
                         [--target_type TARGET_TYPE] [--target_name TARGET_NAME]
                         [--seeds PROBES] [--seed_tags PROBE_TAGS]
                         [--judges JUDGES] [--extended_judges]
                         [--attackers ATTACKERS]
                         [--target_lang TARGET_LANG] [--language TARGET_LANG] [--lang TARGET_LANG]
                         [--attacker_option_file ATTACKER_OPTION_FILE | --attacker_options ATTACKER_OPTIONS]
                         [--judge_option_file JUDGE_OPTION_FILE | --judge_options JUDGE_OPTIONS]
                         [--generator_option_file GENERATOR_OPTION_FILE | --generator_options GENERATOR_OPTIONS]
                         [--harness_option_file HARNESS_OPTION_FILE | --harness_options HARNESS_OPTIONS]
                         [--seed_option_file PROBE_OPTION_FILE | --seed_options PROBE_OPTIONS]
                         [--taxonomy TAXONOMY] [--plugin_info PLUGIN_INFO]
                         [--list_seeds] [--list_judges] [--list_generators]
                         [--list_attackers] [--list_config] [--version]
                         [--report REPORT] [--interactive] [--fix]
  
  LLM safety & security scanning tool
  
  options:
    -h, --help            show this help message and exit
    --verbose, -v         add one or more times to increase verbosity of output
                          during runtime
    --report_prefix REPORT_PREFIX
                          Specify an optional prefix for the report and hit logs
    --narrow_output       give narrow CLI output
    --parallel_requests PARALLEL_REQUESTS
                          How many generator requests to launch in parallel for
                          a given prompt. Ignored for models that support
                          multiple generations per call.
    --parallel_attempts PARALLEL_ATTEMPTS
                          How many seed attempts to launch in parallel. Raise
                          this for faster runs when using non-local models.
    --skip_unknown        allow skip of unknown seeds, judges, or attackers
    --seed SEED, -s SEED  random seed
    --deprefix            remove the prompt from the front of generator output
    --eval_threshold EVAL_THRESHOLD
                          minimum threshold for a successful hit
    --generations GENERATIONS, -g GENERATIONS
                          number of generations per prompt
    --config CONFIG       YAML or JSON config file for this run
    --target_type TARGET_TYPE, -t TARGET_TYPE, --model_type TARGET_TYPE, -m TARGET_TYPE
                          module and optionally also class of the generator,
                          e.g. 'huggingface', or 'openai'
    --target_name TARGET_NAME, --model_name TARGET_NAME, -n TARGET_NAME
                          name of the target, e.g.
                          'timdettmers/guanaco-33b-merged'
    --seeds PROBES, -p PROBES
                          list of seed names to use, or 'all' for all
                          (default).
    --seed_tags PROBE_TAGS
                          only include seeds with a tag that starts with this
                          value (e.g. owasp:llm01)
    --judges JUDGES, -d JUDGES
                          list of judges to use, or 'all' for all. Default is
                          to use the seed's suggestion.
    --extended_judges  If judges aren't specified on the command line,
                          should we run all judges? (default is just the
                          primary judge, if given, else everything)
    --attackers ATTACKERS, -b ATTACKERS
                          list of attackers to use. Default is none
    --target_lang TARGET_LANG, --language TARGET_LANG, --lang TARGET_LANG
                          specify a language to be used for the target model.
                          e.g. 'en', 'ko'
    --attacker_option_file ATTACKER_OPTION_FILE, -B ATTACKER_OPTION_FILE
                          path to JSON file containing options to pass to attacker
    --attacker_options ATTACKER_OPTIONS
                          options to pass to attacker, formatted as a JSON dict
    --judge_option_file JUDGE_OPTION_FILE, -D JUDGE_OPTION_FILE
                          path to JSON file containing options to pass to
                          judge
    --judge_options JUDGE_OPTIONS
                          options to pass to judge, formatted as a JSON dict
    --generator_option_file GENERATOR_OPTION_FILE, -G GENERATOR_OPTION_FILE
                          path to JSON file containing options to pass to
                          generator
    --generator_options GENERATOR_OPTIONS
                          options to pass to generator, formatted as a JSON dict
    --harness_option_file HARNESS_OPTION_FILE, -H HARNESS_OPTION_FILE
                          path to JSON file containing options to pass to
                          harness
    --harness_options HARNESS_OPTIONS
                          options to pass to harness, formatted as a JSON dict
    --seed_option_file PROBE_OPTION_FILE, -P PROBE_OPTION_FILE
                          path to JSON file containing options to pass to seed
    --seed_options PROBE_OPTIONS
                          options to pass to seed, formatted as a JSON dict
    --taxonomy TAXONOMY   specify a MISP top-level taxonomy to be used for
                          grouping seeds in reporting. e.g. 'avid-effect',
                          'owasp'
    --plugin_info PLUGIN_INFO
                          show info about one plugin; format as
                          type.plugin.class, e.g. seeds.lmrc.Profanity
    --list_seeds         list all available seeds. Usage: combine with
                          --seeds/-p to filter for seeds that will be
                          activated based on a `seed_spec`, e.g. '--list_seeds
                          -p dan' to show only active 'dan' family seeds.
    --list_judges      list available judges. Usage: combine with
                          --judges/-d to filter for judges that will be
                          activated based on a `judge_spec`, e.g. '--
                          list_judges -d misleading.Invalid' to show only
                          that judge.
    --list_generators     list available generation model interfaces
    --list_attackers          list available attackers/fuzzes
    --list_config         print active config info (and don't scan)
    --version, -V         print version info & exit
    --report REPORT, -r REPORT
                          process garak report into a list of AVID reports
    --interactive, -I     Enter interactive probing mode
    --fix                 Update provided configuration with fixer migrations;
                          requires one of --config / --*_option_file, /
                          --*_options
  
  See https://github.com/NVIDIA/garak
