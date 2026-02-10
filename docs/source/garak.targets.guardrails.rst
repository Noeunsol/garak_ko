garak.targets.guardrails
===========================

This is a target for warpping a NeMo Guardrails configuration. Using this
garak target enables security testing of a Guardrails config.

The ``guardrails`` target expects a path to a valid Guardrails configuration
to be passed as its name. For example,

.. code-block::

   garak -t guardrails -n sample_abc/config

This target requires installation of the `guardrails <https://pypi.org/project/nemoguardrails/>`_
Python package.

When invoked, garak sends prompts in series to the Guardrails setup using
``rails.generate``, and waits for a response. The target does not support
parallisation, so it's recommended to run smaller seeds, or set ``generations``
to a low value, in order to reduce garak run time.

.. automodule:: garak.targets.guardrails
   :members:
   :undoc-members:
   :show-inheritance:
