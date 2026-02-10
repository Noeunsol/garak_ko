garak.judges.judge
==================================

Implements LLM as a Judge.

This works by instantiating an LLM via the target interface, which will act as the judge.
Judge LLMs need to support the OpenAI API within garak, i.e. they should inherit OpenAICompatible.
This includes OpenAI, NIM, Azure and Groq targets.


.. automodule:: garak.judges.judge
   :members:
   :undoc-members:
   :show-inheritance:
