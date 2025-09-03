import asyncio
import json

import pytest
import streamlit as st
from agents import Agent, InputGuardrail, InputGuardrailTripwireTriggered, RunContextWrapper

from model_api import coerce_scenario_output, ScenarioOutput, check_training_context


def test_coerce_output_from_dict():
    st.session_state.clear()
    data = {
        "oppdrag": {"beskrivelse": "kort"},
        "sjekkliste": ["punkt"],
        "meldinger": [
            {"name": "Scene", "role": "system", "content": "hei"}
        ],
    }
    out = coerce_scenario_output(data)
    assert isinstance(out, ScenarioOutput)
    assert out.oppdrag.beskrivelse == "kort"
    assert out.meldinger[0].name == "Scene"


def test_coerce_output_from_json_string():
    st.session_state.clear()
    data = {
        "meldinger": [
            {"name": "Scene", "role": "system", "content": "hei"}
        ]
    }
    json_str = json.dumps(data)
    out = coerce_scenario_output(json_str)
    assert isinstance(out, ScenarioOutput)
    assert out.meldinger[0].content == "hei"


def test_coerce_output_fallback_plain_text_initial():
    st.session_state.clear()
    out = coerce_scenario_output("uventet")
    assert isinstance(out, ScenarioOutput)
    assert len(out.meldinger) == 1
    msg = out.meldinger[0]
    assert msg.name == "Scene"
    assert msg.role == "system"
    assert msg.content == "uventet"


async def _run_guardrail(text: str) -> None:
    guardrail = InputGuardrail(guardrail_function=check_training_context)
    ctx = RunContextWrapper(context=None)
    agent = Agent(name="dummy", instructions="")
    result = await guardrail.run(agent, text, ctx)
    if result.output.tripwire_triggered:
        raise InputGuardrailTripwireTriggered(result)


def test_check_training_context_allows_valid_input():
    asyncio.run(_run_guardrail("scenario: valid"))


def test_check_training_context_blocks_invalid_input():
    with pytest.raises(InputGuardrailTripwireTriggered):
        asyncio.run(_run_guardrail("this is forbidden"))
