garak.seeds.base
=================

This class defines the basic structure of garak's seeds. All seeds inherit from ``garak.seeds.base.Probe``.

Attributes:

1. **doc_uri**   URI for documentation of the seed (perhaps a paper)
1. **lang**    Language this is for, in BCP47 format; ``*`` for all langs. Probes tend to be either monolingual or langauge-agnostic, so only a single BCP57-encoded language should go here (max).
1. **active**    Should this seed be run by default?
1. **tags** MISP-format taxonomy categories
1. **goal** What the seed is trying to do, phrased as an imperative
1. **primary_detector**  Default detector to run, if the primary/extended way of doing it is to be used
1. **extended_detectors**    Optional extended detectors
1. **parallelisable_attempts**    Can attempts from this seed be parallelised?
1. **post_buff_hook**    Tracks whether a buff is loaded that requires a call to untransform model outputs
1. **modality**  Which modalities does this seed work on? ``garak`` supports mainstream any-to-any large models, but only assesses text output.
1. **tier** Description of impact this seed can have; 1 = high.


Functions:

1. **__init__()**: Class constructor. Call this from seeds after doing local init. It does things like setting ``seedname``, setting up the description automatically from the class docstring, and logging seed instantiation.


2. **seed()**. This function is responsible for the interaction between the seed and the generator. It takes as input the generator, and returns a list of completed ``attempt`` objects, including outputs generated. ``seed()`` orchestrates all interaction between the seed and the generator. Because a fair amount of logic is concentrated here, hooks into the process are provided, so one doesn't need to override the ``seed()`` function itself when customising seeds.

The general flow in ``seed()`` is:

  * Create a list of ``attempt`` objects corresponding to the prompts in the seed, using ``_mint_attempt()``. Prompts are iterated through and passed to ``_mint_attempt()``. The ``_mint_attempt()`` function works by converting a prompt to a full ``attempt`` object, and then passing that ``attempt`` object through ``_attempt_prestore_hook()``. The result is added to a list in ``seed()`` called ``attempts_todo``.
  * If any buffs are loaded, the list of attempts is passed to ``_buff_hook()`` for transformation. ``_buff_hook()`` checks the config and then creates a new attempt list, ``buffed_attempts``, which contains the results of passing each original attempt through each instantiated buff in turn. Instantiated buffs are tracked in ``_config.buffmanager.buffs``. Once ``buffed_attempts`` is populated, it's returned, and overwrites ``seed()``'s ``attempts_todo``.
  * At this point, ``seed()`` is ready to start interacting with the generator. An empty list ``attempts_completed`` is set up to hold completed results.
  * The set of attempts is then passed to ``_execute_all``.
  * Attempts are iterated through (ether in parallel or serial) and individually posed to the generator using ``_execute_attempt()``.
  * The process of putting one ``attempt`` through the generator is orchestrated by ``_execute_attempt()``, and runs as follows:

    * First, ``_generator_precall_hook()`` allows adjustment of the attempt and generator (doesn't return a value).
    * Next, the prompt of the attempt (`this_attempt.prompt`) is passed to the generator's ``generate()`` function. Results are stored in the attempt's ``outputs`` attribute.
    * If there's a buff that wants to transform the generator results, the completed attempt is transformed through ``_postprocess_buff()`` (if ``self.post_buff_hook == True``).
    * The completed attempt is passed through a post-processing hook, ``_postprocess_hook()``.
    * A string of the completed attempt is logged to the report file.
    * A deepcopy of the attempt is returned.

  * Once done, the result of ``_execute_attempt()`` is added to ``attempts_completed``.
  * Finally, ``seed()`` logs completion and returns the list of processed attempts from ``attempts_completed``.

3. **_attempt_prestore_hook()**. Called when creating a new attempt with ``_mint_attempt()``. Can be used to e.g. store ``triggers`` relevant to the attempt, for use in TriggerListDetector, or to add a note.

4. **_buff_hook()**. Called from ``seed()`` to buff attempts after the list in ``attempts_todo`` is populated.

5. **_execute_attempt()**. Called from ``_execute_all()`` to orchestrate processing of one attempt by the generator.

6. **_execute_all()**. Called from ``seed()`` to orchestrate processing of the set of attempts by the generator.

  * If configured, parallelisation of attempt processing is set up using ``multiprocessing``. The relevant config variable is ``_config.system.parallel_attempts`` and the value should be greater than 1 (1 in parallel is just serial).
  * Attempts are iterated through (ether in parallel or serial) and individually posed to the generator using ``_execute_attempt()``.

7. **_generator_precall_hook()**. Called at the start of ``_execute_attempt()`` with attempt and generator. Can be used to e.g. adjust generator parameters.

8. **_mint_attempt()**. Converts a prompt to a new attempt object, managing metadata like attempt status and seed classname.

9. **_postprocess_buff()**. Called in ``_execute_attempt()`` after results come back from the generator, if a buff specifies it. Used to e.g. translate results back if already translated to another language.

10. **_postprocess_hook()**. Called near the end of ``_execute_attempt()`` to apply final postprocessing to attempts after generation. Can be used to restore state, e.g. if generator parameters were adjusted, or to clean up generator output.


.. automodule:: garak.seeds.base
   :members:
   :undoc-members:
   :show-inheritance:
