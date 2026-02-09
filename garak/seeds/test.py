"""**Test Seeds**

Seeds that help with testing garak, but aren't necessarily useful in
deployment practice."""

import garak.seeds


class Blank(garak.seeds.Seed):
    """Blank prompt

    Poses a blank prompt to the model"""

    lang = "*"
    active = False  # usually for testing
    goal = "see what the model has to say for itself given silence"
    doc_uri = ""
    tags = []
    tier = garak.seeds.Tier.UNLISTED

    primary_judge = "any.AnyOutput"
    prompts = [""]


class Test(garak.seeds.Seed):
    """Test seed

    Poses some test strings to a model; for use in tests"""

    lang = "*"
    active = False  # usually for testing
    goal = "send some test strings, ignore the response"
    doc_uri = ""
    tags = []
    tier = garak.seeds.Tier.UNLISTED

    primary_judge = "always.Pass"
    prompts = [
        "",
        "The quick brown fox jumps over the lazy dog",
        "Liberté, égalité, fraternité",
        "有朋自远方来，不亦乐乎?",
        'ZX*fC-np~z0)#cj32{"qWh',
        "t=};h+WzTq2wypk4fL/6UV",
        "T9btvwOX'EV/)q2+o$kF7#",
        "\\",
    ]
