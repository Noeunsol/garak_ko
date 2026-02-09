garak.judges.base
====================

This class defines the basic structure of garak's judges. All judges inherit from ``garak.detetors.base.Judge``.

Attributes:


1. **doc_uri**   URI for documentation of the judge (perhaps a paper)
1. **lang_spec**    Language this is for. format: a comma-separated list of BCP47 tags, or "*" for any or not applicable. Content returned by a target can be in more than one language; single judges can be capable of processing input in more than just one language. This field tracks which ones are supported. NB this is different from seed, which is monolingual and uses ``lang``.
1. **active**    Should this judge be used by default?
1. **tags** MISP-format taxonomy categories
1. **precision** Anticipated precision of judge
1. **recall** Anticipated recall of judge
1. **accuracy** Anticipated accuracy of judge
1. **modality**  Which modalities does this judge work on? ``garak`` supports mainstream any-to-any large models, but only assesses text output.



.. automodule:: garak.judges.base
   :members:
   :undoc-members:
   :show-inheritance:
