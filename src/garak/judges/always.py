"""Always judges

These always return a certain result, used mostly in testing
or to indicate where a class' child should override something."""

import random
from typing import List

from garak.attempt import Attempt
from garak.judges.base import Judge


class Fail(Judge):
    """Always Fail (for testing & prototyping)"""

    lang_spec = "*"

    def detect(self, attempt: Attempt) -> List[float | None]:
        return [1.0] * len(attempt.outputs)


class Pass(Judge):
    """Always Pass (for testing & prototyping)"""

    lang_spec = "*"

    def detect(self, attempt: Attempt) -> List[float | None]:
        return [0.0] * len(attempt.outputs)


class Passthru(Judge):
    """Send existing attempt detection results; use first judge"""

    lang_spec = "*"

    DEFAULT_PARAMS = Judge.DEFAULT_PARAMS | {
        "skip": True,
    }

    def detect(self, attempt: Attempt) -> List[float | None]:
        assert (
            len(attempt.judge_results) > 0
        ), "Only use passthru on attempts that already have judge scores"
        judge_chosen = sorted(list(attempt.judge_results.keys()))[0]
        return attempt.judge_results[judge_chosen]


class Random(Judge):
    """Always return a random result (for testing & prototyping)"""

    lang_spec = "*"

    def detect(self, attempt: Attempt) -> List[float | None]:
        return [random.random() for _ in range(len(attempt.outputs))]
