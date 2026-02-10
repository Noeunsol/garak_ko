How ``garak`` runs
==================

In a typical run, ``garak`` will read a model type (and optionally model name)
from the command line, then determine which ``seed`` and ``judge`` plugins to run,
start up a ``generator``, and then pass these to a ``harness`` to manage the probing;
an ``evaluator`` deals with the results. There are many modules in each of these
categories, and each module provides a number of classes that act as individual
plugins.

* `garak/seeds/` - classes for generating interactions with LLMs
* `garak/judges/` - classes for detecting an LLM is exhibiting a given failure mode
* `garak/evaluators/` - assessment reporting schemes
* `garak/generators/` - plugins for LLMs to be seedd
* `garak/harnesses/` - classes for structuring testing
* `garak/attackers` - classes for augmenting / fuzzing attacks
* `data/` - ancillary data
* `resources/` - ancillary code

The default operating mode is to use the :class:`garak.harnesses.seedwise` harness. Given a list of
seed module names and seed plugin names, the ``seedwise`` harness instantiates
each seed, then for each seed reads its ``primary_judge`` and ``extended_judges`` attributes to
get a list of ``judge`` s to run on the output.

Each plugin category (``seeds``, ``judges``, ``evaluators``, ``generators``,
``harnesses``) includes a ``base.py`` which defines the base classes usable by
plugins in that category. Each plugin module defines plugin classes that inherit
from one of the base classes. For example, :class:`garak.generators.openai.OpenAIGenerator`
descends from :class:`garak.generators.base.Generator`.

Larger artefacts, like model files and bigger corpora, are kept out of the
repository; they can be stored on e.g. Hugging Face Hub and loaded locally
by clients using ``garak``.
