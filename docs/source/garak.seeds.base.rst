garak.seeds.base
=================

This class defines the basic structure of garak's seeds. All seeds inherit from ``garak.seeds.base.Seed``.

Attributes:

1. **doc_uri**   URI for documentation of the seed (perhaps a paper)
1. **lang**    Language this is for, in BCP47 format; ``*`` for all langs. Seeds tend to be either monolingual or langauge-agnostic, so only a single BCP57-encoded language should go here (max).
1. **active**    Should this seed be run by default?
1. **tags** MISP-format taxonomy categories
1. **goal** What the seed is trying to do, phrased as an imperative
1. **primary_judge**  Default judge to run, if the primary/extended way of doing it is to be used
1. **extended_judges**    Optional extended judges
1. **parallelisable_attempts**    Can attempts from this seed be parallelised?
1. **post_attacker_hook**    Tracks whether a attacker is loaded that requires a call to untransform model outputs
1. **modality**  Which modalities does this seed work on? ``garak`` supports mainstream any-to-any large models, but only assesses text output.
1. **tier** Description of impact this seed can have; 1 = high.


Functions:

1. **__init__()**: Class constructor. Call this from seeds after doing local init. It does things like setting ``seedname``, setting up the description automatically from the class docstring, and logging seed instantiation.


2. **seed()**. This function is responsible for the interaction between the seed and the target. It takes as input the target, and returns a list of completed ``attempt`` objects, including outputs generated. ``seed()`` orchestrates all interaction between the seed and the target. Because a fair amount of logic is concentrated here, hooks into the process are provided, so one doesn't need to override the ``seed()`` function itself when customising seeds.

The general flow in ``seed()`` is:

  * Create a list of ``attempt`` objects corresponding to the prompts in the seed, using ``_mint_attempt()``. Prompts are iterated through and passed to ``_mint_attempt()``. The ``_mint_attempt()`` function works by converting a prompt to a full ``attempt`` object, and then passing that ``attempt`` object through ``_attempt_prestore_hook()``. The result is added to a list in ``seed()`` called ``attempts_todo``.
  * If any attackers are loaded, the list of attempts is passed to ``_attacker_hook()`` for transformation. ``_attacker_hook()`` checks the config and then creates a new attempt list, ``attackered_attempts``, which contains the results of passing each original attempt through each instantiated attacker in turn. Instantiated attackers are tracked in ``_config.attackermanager.attackers``. Once ``attackered_attempts`` is populated, it's returned, and overwrites ``seed()``'s ``attempts_todo``.
  * At this point, ``seed()`` is ready to start interacting with the target. An empty list ``attempts_completed`` is set up to hold completed results.
  * The set of attempts is then passed to ``_execute_all``.
  * Attempts are iterated through (ether in parallel or serial) and individually posed to the target using ``_execute_attempt()``.
  * The process of putting one ``attempt`` through the target is orchestrated by ``_execute_attempt()``, and runs as follows:

    * First, ``_target_precall_hook()`` allows adjustment of the attempt and target (doesn't return a value).
    * Next, the prompt of the attempt (`this_attempt.prompt`) is passed to the target's ``generate()`` function. Results are stored in the attempt's ``outputs`` attribute.
    * If there's a attacker that wants to transform the target results, the completed attempt is transformed through ``_postprocess_attacker()`` (if ``self.post_attacker_hook == True``).
    * The completed attempt is passed through a post-processing hook, ``_postprocess_hook()``.
    * A string of the completed attempt is logged to the report file.
    * A deepcopy of the attempt is returned.

  * Once done, the result of ``_execute_attempt()`` is added to ``attempts_completed``.
  * Finally, ``seed()`` logs completion and returns the list of processed attempts from ``attempts_completed``.

3. **_attempt_prestore_hook()**. Called when creating a new attempt with ``_mint_attempt()``. Can be used to e.g. store ``triggers`` relevant to the attempt, for use in TriggerListJudge, or to add a note.

4. **_attacker_hook()**. Called from ``seed()`` to attacker attempts after the list in ``attempts_todo`` is populated.

5. **_execute_attempt()**. Called from ``_execute_all()`` to orchestrate processing of one attempt by the target.

6. **_execute_all()**. Called from ``seed()`` to orchestrate processing of the set of attempts by the target.

  * If configured, parallelisation of attempt processing is set up using ``multiprocessing``. The relevant config variable is ``_config.system.parallel_attempts`` and the value should be greater than 1 (1 in parallel is just serial).
  * Attempts are iterated through (ether in parallel or serial) and individually posed to the target using ``_execute_attempt()``.

7. **_target_precall_hook()**. Called at the start of ``_execute_attempt()`` with attempt and target. Can be used to e.g. adjust target parameters.

8. **_mint_attempt()**. Converts a prompt to a new attempt object, managing metadata like attempt status and seed classname.

9. **_postprocess_attacker()**. Called in ``_execute_attempt()`` after results come back from the target, if a attacker specifies it. Used to e.g. translate results back if already translated to another language.

10. **_postprocess_hook()**. Called near the end of ``_execute_attempt()`` to apply final postprocessing to attempts after generation. Can be used to restore state, e.g. if target parameters were adjusted, or to clean up target output.


.. automodule:: garak.seeds.base
   :members:
   :undoc-members:
   :show-inheritance:
