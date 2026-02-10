# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import pytest
import wn

import garak._plugins
import garak.seeds.base
import garak.seeds.topic


TEST_LEXICON = "oewn:2023"
TEST_TERM = "abortion"
TEST_SYNSET_ID = "oewn-00231191-n"

@pytest.fixture(scope="module")
def sysnet():
    garak.seeds.topic.WordnetBlockedWords()
    wn.download(TEST_LEXICON)
    w = wn.Wordnet(TEST_LEXICON)
    s = w.synset(TEST_SYNSET_ID)
    return s


SEEDS = [
    classname
    for (classname, active) in garak._plugins.enumerate_plugins("seeds")
    if ".topic.Wordnet" in classname
]


@pytest.mark.parametrize("seedname", SEEDS)
def test_topic_wordnet_load(seedname):
    p = garak._plugins.load_plugin(seedname)
    assert isinstance(p, garak.seeds.base.Seed)
    

@pytest.mark.parametrize("seedname", SEEDS)
def test_topic_wordnet_version(seedname):
    p = garak._plugins.load_plugin(seedname)
    assert p.lexicon == TEST_LEXICON


@pytest.mark.parametrize("seedname", SEEDS)
def test_topic_wordnet_get_node_terms(seedname, sysnet):
    p = garak._plugins.load_plugin(seedname)
    terms = p._get_node_terms(sysnet)
    assert list(terms) == ["abortion"]


@pytest.mark.parametrize("seedname", SEEDS)
def test_topic_wordnet_get_node_children(seedname, sysnet):
    p = garak._plugins.load_plugin(seedname)
    children = p._get_node_children(sysnet)
    assert children == [wn.synset("oewn-00231342-n"), wn.synset("oewn-00232028-n")]


@pytest.mark.parametrize("seedname", SEEDS)
def test_topic_wordnet_get_node_id(seedname, sysnet):
    p = garak._plugins.load_plugin(seedname)
    assert p._get_node_id(sysnet) == TEST_SYNSET_ID


def test_topic_wordnet_blocklist_get_initial_nodes(sysnet):
    p = garak.seeds.topic.WordnetBlockedWords()
    p.target_topic = TEST_TERM
    initial_nodes = p._get_initial_nodes()
    assert initial_nodes == [
        sysnet,
        wn.synset("oewn-07334252-n"),
        wn.synset("oewn-00231342-n"),
        wn.synset("oewn-00232028-n"),
    ]
