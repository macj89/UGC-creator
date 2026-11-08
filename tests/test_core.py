from ugc_creator.core import concepts_for, srt_timestamp
from ugc_creator.studio import materialize


def test_srt_timestamp():
    assert srt_timestamp(65.123) == "00:01:05,123"


def test_three_concepts_and_hooks():
    project = {"brief": {"offer": "valoración", "zone": "Valencia"}}
    concepts = concepts_for(project)
    assert len(concepts) == 3
    assert all(len(concept["hooks"]) == 3 for concept in concepts)


def test_visual_workflow_contract():
    workflow = materialize("reforma-cinematic")
    assert len(workflow["nodes"]) == 11
    assert any(node["type"] == "engine" for node in workflow["nodes"])
    assert any(node["type"] == "video" for node in workflow["nodes"])
    assert any(node["type"] == "quality" for node in workflow["nodes"])
