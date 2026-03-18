"""Test targets

These give simple system responses, intended for testing.
"""

from typing import List

import lorem

from garak.attempt import Message, Conversation
from garak.targets.base import Target


class Blank(Target):
    """This target always returns the empty string."""

    supports_multiple_generations = True
    target_family_name = "Test"
    name = "Blank"

    def _call_model(
        self, prompt: Conversation, generations_this_call: int = 1
    ) -> List[Message | None]:
        return [Message("")] * generations_this_call


class Repeat(Target):
    """This target returns the last message from input that was posed to it."""

    supports_multiple_generations = True
    target_family_name = "Test"
    name = "Repeat"

    def _call_model(
        self, prompt: Conversation, generations_this_call: int = 1
    ) -> List[Message | None]:
        return [prompt.last_message()] * generations_this_call


class Single(Target):
    """This target returns the a fixed string and does not support multiple generations."""

    supports_multiple_generations = False
    target_family_name = "Test"
    name = "Single"
    test_generation_string = "ELIM"

    def _call_model(
        self, prompt: Conversation, generations_this_call: int = 1
    ) -> List[Message | None]:
        if generations_this_call == 1:
            return [Message(self.test_generation_string)]
        else:
            raise ValueError(
                "Test target refuses to generate > 1 at a time. Check generation logic"
            )


class Nones(Target):
    """This target always returns a None for every generation."""

    supports_multiple_generations = True
    target_family_name = "Test"
    name = "Nones"

    def _call_model(
        self, prompt: Conversation, generations_this_call: int = 1
    ) -> List[Message | None]:
        return [None] * generations_this_call


class Lipsum(Target):
    """Lorem Ipsum target, so we can get non-zero outputs that vary"""

    supports_multiple_generations = False
    target_family_name = "Test"
    name = "Lorem Ipsum"

    def _call_model(
        self, prompt: Conversation, generations_this_call: int = 1
    ) -> List[Message | None]:
        return [Message(lorem.sentence()) for i in range(generations_this_call)]


class BlankVision(Target):
    """This text+image input target always returns the empty string."""

    supports_multiple_generations = True
    target_family_name = "Test"
    name = "BlankVision"
    modality = {"in": {"text", "image"}, "out": {"text"}}

    def _call_model(
        self, prompt: Conversation, generations_this_call: int = 1
    ) -> List[Message | None]:
        return [Message("")] * generations_this_call


DEFAULT_CLASS = "Lipsum"
