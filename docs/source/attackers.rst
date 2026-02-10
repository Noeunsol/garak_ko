garak.attackers
==============

Attacker plugins augment, constrain, or otherwise perturb the interaction
between seeds and a target.  These allow things like mapping
seeds into a different language, or expanding prompts to various
paraphrases, and so on.

Attackers must inherit the base class.
`Attacker` serves as a template showing what expectations there are for
implemented attackers.

.. toctree::
   :maxdepth: 2

   garak.attackers
   garak.attackers.base
   garak.attackers.encoding
   garak.attackers.low_resource_languages
   garak.attackers.lowercase
   garak.attackers.paraphrase
   garak.attackers.remove_spaces
