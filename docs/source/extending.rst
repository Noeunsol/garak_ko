Extending ``garak``
===================

``garak`` has a modular, extensible structure.
If there's a function you're missing in ``garak``, it is in many cases relatively simple to add that by adding a plugin.
Plugins in garak are typically single Python modules (i.e. a single Python file), added into the seeds, judges, targets, or attackers directories (packages).
``garak`` provides many tests which, while not complete, are extensive, and offer a good description of expectations new code should meet.
We hope that the messages within the tests are helpful to developers and guide you quickly to building good code that works well with the ``garak`` GenAI assessment kit.

Code structure
--------------

We have a page describing the :doc:`top-level concepts in garak <basic>`.
Rather than repeat that, take a look, so you have an idea about the code base!

Developing your own plugins
---------------------------

Plugins are targets, seeds, judges, attackers, harnesses, and evaluators. Each category of plugin gets its own directory in the source tree. The first four categories are where most of the new functionality is.

The recipe for writing a new plugin or plugin class isn't outlandish:

* Only start a new module if none of the current modules could fit
* Take a look at how other plugins do it
   * For an example Target, check out :class:`garak.targets.replicate`
   * For an example Seed, check out :class:`garak.seeds.malwaregen`
   * For an example Judge, check out :class:`garak.judges.toxicity` or :class:`garak.judges.specialwords`
   * For an example Attacker, check out :class:`garak.attackers.lowercase`
* Start a new module inheriting from one of the base classes, e.g. :class:`garak.seeds.base.Seed`
* Override as little as possible.

If you use custom modules not included in garak's default list, include these in the plugin's top-level ``extra_dependency_names`` parameter.
Garak's plugin loader (``garak._plugins.load_plugin()``) will manage the import and inject the requested module as ``self.<module>``.


Guides to writing plugins
-------------------------

Here are our tutorials on plugin writing:

* :doc:`Building a garak target <extending.target>` -- step-by-step guide to building an interface for a real API-based model service
* :doc:`Building a garak seed <extending.seed>` -- A guide to writing your own custom seeds

Testing during development
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can test your code in a few ways:

* Start an interactive Python session
   * Instantiate the plugin, e.g. ``import garak._plugins`` then ``seed = garak._plugins.load_plugin("garak.seeds.mymodule.MySeed")``
   * Check out that the values and methods work as you'd expect
* Get ``garak`` to list all the plugins of the type you're writing, with ``--list_seeds``, ``--list_judges``, or ``--list_targets``: ``python3 -m garak --list_seeds``
* Run a scan with test plugins
   * For seeds, try a blank target and always.Pass judge: ``python3 -m garak -t test.Blank -p mymodule -d always.Pass``
   * For judges, try a blank target and a blank seed: ``python3 -m garak -t test.Blank -p test.Blank -d mymodule``
   * For targets, try a blank seed and always.Pass judge: ``python3 -m garak -t mymodule -p test.Blank -d always.Pass``


garak supports pytest tests in garak/tests. You can run these with ``python -m pytest tests/`` from the root directory.
All the tests should pass for any code there's a pull request for, and all tests must pass in any PR before it can be merged.

Contributing
~~~~~~~~~~~~

Did you write something that makes ``garak`` better?
We love community contributions and are used to shepherding in useful work.
Take a look at our docs on :doc:`contributing <contributing>` your work to the project.
