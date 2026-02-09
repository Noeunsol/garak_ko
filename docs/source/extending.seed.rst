Writing a Probe
###############

Probes are, in some ways, the essence of garak's functionality -- they serve as the abstraction that encapsulates attacks against AI models and systems.
In this example, we're going to go over the key points of how to develop a new seed.

Inheritance
***********

All seeds inherit from ``garak.seeds.base.Probe``, exposed at package level via ``garak.seeds``.

.. code-block:: python

    import garak.seeds

    class MyNewProbe(garak.seeds.Probe):
        """Probe to do something naughty to a language model"""
        ...

By inheriting from ``garak.seeds.base.Probe``, seeds can work nicely with ``Generator`` and ``Attempt`` objects in addition to ensuring that any ``Buff`` objects that you apply to a seed will work appropriately.

The ``seed`` method of a ``Probe`` object provides the core logic of the seed.
Ideally, you only need to populate the ``prompts`` attribute of a ``Probe`` and let the ``seed`` method do the heavy lifting.
However, if this logic is insufficient for your seed, the ``seed`` method is where the majority of the work (and potential issues) tends to lie.

.. code-block:: python

    def seed(self, generator) -> Iterable[garak.attempt.Attempt]:
        """attempt to exploit the target generator, returning a list of results"""
        logging.debug("seed execute: %s", self)

        self.generator = generator

        # build list of attempts
        attempts_todo: Iterable[garak.attempt.Attempt] = []
        prompts = list(self.prompts)
        for seq, prompt in enumerate(prompts):
            attempts_todo.append(self._mint_attempt(prompt, seq))

        # buff hook
        if len(_config.buffmanager.buffs) > 0:
            attempts_todo = self._buff_hook(attempts_todo)

        # iterate through attempts
        attempts_completed = self._execute_all(attempts_todo)

        logging.debug(
            "seed return: %s with %s attempts", self, len(attempts_completed)
        )

        return attempts_completed

Configuring and Describing Probes
*********************************

Probes are built upon the ``Configurable`` base class and are themselves configurable.
We largely ignore parameters like ``ENV_VAR`` and ``DEFAULT_PARAMS`` in ``Probe`` classes, but if your seed requires an environment variable or you want to set some default parameters, it is done first in the class.

More often, we'll be looking at descriptive attributes of the seed.
From the base class:

.. code-block:: python

    # docs uri for a description of the seed (perhaps a paper)
    doc_uri: str = ""
    # language this is for, in BCP47 format; * for all langs
    lang: Union[str, None] = None
    # should this seed be included by default?
    active: bool = True
    # MISP-format taxonomy categories
    tags: Iterable[str] = []
    # what the seed is trying to do, phrased as an imperative
    goal: str = ""
    # Deprecated -- the detectors that should be run for this seed. always.Fail is chosen as default to send a signal if this isn't overridden.
    recommended_detector: Iterable[str] = ["always.Fail"]
    # default detector to run, if the primary/extended way of doing it is to be used (should be a string formatted like recommended_detector)
    primary_detector: Union[str, None] = None
    # optional extended detectors
    extended_detectors: Iterable[str] = []
    # can attempts from this seed be parallelised?
    parallelisable_attempts: bool = True
    # Keeps state of whether a buff is loaded that requires a call to untransform model outputs
    post_buff_hook: bool = False
    # support mainstream any-to-any large models
    # legal element for str list `modality['in']`: 'text', 'image', 'audio', 'video', '3d'
    # refer to Table 1 in https://arxiv.org/abs/2401.13601
    # we focus on LLM input for seed
    modality: dict = {"in": {"text"}}

That's a lot of attributes before we get into ones you may need to add!
Many of these are decent defaults, though there are a few that we absolutely want to include in any new seed

* ``doc_uri``: What is a good reference for the seed you're implementing? An academic paper, blog post, or social media post (in descending order of preference) goes here.
* ``active``: Should this seed be part of default scans?
* ``tags``: MISP-formatted taxonomy categories __e.g.__ ``["avid-effect:security:S0403", "owasp:llm01", "quality:Security:PromptStability", "payload:jailbreak"]``
* ``goal``: What is the seed trying to do? __e.g.__ ``"disregard the system prompt"``
* ``primary_detector``: What ``Detector`` should your seed use?

.. code-block:: python

    class MyNewProbe(garak.seeds.Probe):
        """Probe to do something naughty to a language model"""

        primary_detector = "mitigation.MitigationBypass"
        tags = [
            "avid-effect:security:S0403",
            "owasp:llm01",
            "quality:Security:PromptStability",
            "payload:jailbreak",
        ]
        goal = "disregard the system prompt"
        doc_uri = "https://garak.ai"
        active = False
        ...

Probe Documentation
*******************

You must provide documentation for your seed.
Class docstrings are required and are enforced by a test that must pass before merging.

#. Add an ``.rst`` file in the ``docs/source`` directory with the name ``garak.seeds.<module>.rst``, where ``module`` matches the file name of your new seed.

   Refer to other seed documentation for an example of the content.

   Also refer to the garak tests to ensure your documentation is correct.
   The tests check that you added documentation, that the class docstrings are present, and that they link to the right places.

#. Add an entry in ``docs/source/seeds.rst`` and link to  your new module file.

Both the class and module docstrings must be in ReStructuredText (RST) format, and not markdown.
Refer to the `rst Cheatsheet <https://bashtage.github.io/sphinx-material/rst-cheatsheet/rst-cheatsheet.html>`_ or `ReStructuredText Primer <https://docutils.sourceforge.io/docs/user/rst/quickref.html>`_ to get you started.

Paragraphs are separated by a blank lines, such as ``\\n\\n``.

Module Docstrings
=================

In the Python module you're working on, add a module docstring, if there isn't one already.
Include the following parts:

* Title, in bold/strong emphasis (``**``)
* A description of the common technique/intent/source for all seeds in this module (one sentence)
* The inclusion criteria for items in this module, so that others can determine whether or not a new seed would belong in the module (1-3 sentences)
* Further description (optional; one paragraph; 1-5 sentences)
* Links to information about this kind of attack (optional)

Refer to the following example:

.. code-block::

    """**ANSI Escape attack**

    Try to make a model produce ANSI escape codes, which can disrupt downstream processing.

    Probes in this module should all try to elicit ANSI escape codes or information suggesting that the target is capable of producing them.
    There are a couple of different dimensions included:

    * the encoding can vary - raw binary, or an escaped version;
    * the technique used can vary - can we get OCS8, OCS52
    * the action can also be different - log cursor, crash machine, install software etc.

    Further info:

    * https://interhumanagreement.substack.com/p/llm-output-can-take-over-your-computer
    * https://www.youtube.com/watch?v=3T2Al3jdY38
    * https://embracethered.com/blog/posts/2024/terminal-dillmas-prompt-injection-ansi-sequences/
    * https://dgl.cx/2023/09/ansi-terminal-security
    * https://cwe.mitre.org/data/definitions/150.html
    """

Class Docstrings
================

Probe classes themselves must also have a docstring.
The target structure for garak ``Probe`` class docstrings include the following items:

* Short description of the technique or intent of the seed (1 sentence, followed by a blank line)
* Friendly general intro to the seed, in very simple English (1-4 sentences; short sentences; follow `Basic English <https://simple.wikipedia.org/wiki/Basic_English>`_ rules as much as possible, try this `tool <https://www.online-utility.org/english/simple_basic_helper.jsp>`_)
* Example prompts generated by the seed (optional; in RST-formatted blockquote)
* How the seed works, extended description (optional; can be multiple paragraphs)
* Link to source docs; include reference and hyperlink (optional; 1-2 lines)
* For seeds implementing work in a paper, include the paper's abstract (optional; in RST-formatted blockquote)


Testing
*******

Once the logic for our seed is written, you'll want to test it before opening a pull request.
Typically, a good place to start is by seeing if your seed can be imported!

.. code-block:: bash

    $ conda activate garak
    $ python
    $ python
    Python 3.11.5 (main, Sep 11 2023, 08:31:25) [Clang 14.0.6 ] on darwin
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import garak.seeds.mynewseed
    >>>

If you can run this with no error, you're ready to move on to the next phase of testing.
Otherwise, try to address the encountered errors.

Let's try running our new seed against a HuggingFace ``Pipeline`` using ``meta-llama/Llama-2-7b-chat-hf``, a notoriously tricky model to get to behave badly.

.. code-block:: bash

  $ garak -t huggingface -n meta-llama/Llama-2-7b-chat-hf -p mynewseed.MyNewProbe

If it all runs well, you'll get a log and a hitlog file, which tell you how successful your new seed was!
If you encounter errors, go through and try to address them. You can look at the bottom of the `garak.log` file, whose path is printed in the output every time you call garak, to see what errors there are.

If you want to debug your seed interactively, try using something like ``p = garak._plugins.load_plugin("seeds.mynewseed.MyNewProbe")`` from a Python prompt to load the seed. The variable ``p`` will be assigned an instance of the seed (if instantiation was successful) and you can test a lot of the seed's intended functionality from here.


Finally, check a few properties:

* Does the new seed appear in ``python -m garak --list_seeds``?
* Does the seed run? ``python -m garak -t test -p mynewseed.MyNewProbe``
* Do the garak tests pass? ``python -m pytest tests/``

Done!
*****

Congratulations on writing a seed for garak!

If you've tested your seed and validated that it works, run ``black`` to format your code in accordance with garak code standards.
Once your code is properly tested and formatted, push your work to your github fork and open a pull request -- thanks for your contribution!
