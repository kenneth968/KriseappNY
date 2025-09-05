import json
import re
import time
from typing import List, Dict, Optional, Literal

import streamlit as st
from pydantic import BaseModel, Field

from config import MIN_STREAM_TIME_SEC
from async_utils import run_async

# Agents framework
from agents import Agent, GuardrailFunctionOutput, InputGuardrail, Runner
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions


class Oppdrag(BaseModel):
    beskrivelse: Optional[str] = Field(default=None, description="Kort oppsummering (maks fire setninger)")


class ScenarioMessage(BaseModel):
    name: str
    role: Literal["system", "customer", "employee", "student", "bystander"]
    content: str


class ScenarioResult(BaseModel):
    name: Literal["Scenarioresultat"]
    role: Literal["system"]
    content: str


class ScenarioFeedback(BaseModel):
    name: Literal["Tilbakemelding"]
    role: Literal["system"]
    content: str


class ScenarioOutput(BaseModel):
    oppdrag: Optional[Oppdrag] = None
    sjekkliste: Optional[List[str]] = None
    meldinger: List[ScenarioMessage]
    scenarioresultat: Optional[ScenarioResult] = None
    tilbakemelding: Optional[ScenarioFeedback] = None


# Guardrail to ensure scenario inputs stay on topic
def check_training_context(
    context, agent, compiled_input: str | List[Dict]
) -> GuardrailFunctionOutput:
    """Validate that the input contains expected scenario markers and no disallowed content."""

    if isinstance(compiled_input, list):
        text = " ".join(str(item) for item in compiled_input)
    else:
        text = str(compiled_input)

    lowered = text.lower()
    allowed_markers = [
        "scenario",
        "bruker",
        "historikk",
        "runde",
        "vanskelighetsgrad",
    ]
    has_marker = any(marker in lowered for marker in allowed_markers)
    has_disallowed = any(bad in lowered for bad in ["forbidden", "disallowed"])

    if has_disallowed or not has_marker:
        return GuardrailFunctionOutput(
            output_info="Input failed training context check.",
            tripwire_triggered=True,
        )

    return GuardrailFunctionOutput(output_info="ok", tripwire_triggered=False)


# Persona agents (configurable, available for handoff)
scene_agent = Agent(
    name="Scene Agent",
    handoff_description="Genererer første 'Scene'-melding",
    instructions=prompt_with_handoff_instructions(
        "Output: nøyaktig ÉN meldingsobjekt (ikke liste), som JSON/dict, "
        "med {name: 'Scene', role: 'system', content: <2–4 setninger>}. "
        "Skriv på norsk (Bokmål), uten meta-tekst, ingen kodeblokker. "
        "Innhold: sett scenen på Sit Kafe her og nå (presens), med 1–2 konkrete og troverdige detaljer (f.eks. travle morgenminutter, lukt av kaffe, søl, lang kø, feil bestilling, allergi, betalingsproblem). "
        "Ikke nevn spesifikke personnavn; bruk nøytrale betegnelser som 'kunden' og 'kollega'. "
        "Ikke løs konflikten; kun etablér situasjonen kort."
    ),
)

customer_agent = Agent(
    name="Kunde Agent",
    handoff_description="Skriver realistisk sint kundereplikk",
    instructions=prompt_with_handoff_instructions(
        "Output: nøyaktig ÉN meldingsobjekt (ikke liste), som JSON/dict, for en kunde med role 'customer'. "
        "Sett 'name' til et realistisk norsk fornavn (f.eks. Kari, Anders, Nora, Ola, Mari, Jon, Ingrid). "
        "Innhold: 1–4 setninger på norsk, konkret og relevant for scenen. "
        "Inkluder minst én spesifikk detalj (bestilling, ventetid, pris, kvittering, søl, allergi, tidspunkt). "
        "Kalibrer styrke etter 'difficulty' i konteksten: Lett = irritert men saklig; Medium = bestemt og utålmodig; Vanskelig = hevet stemme, avbryter og stiller krav (uten trusler). "
        "Ikke løs situasjonen, ikke metakommentarer, ingen emojis."
    ),
)

bystander_agent = Agent(
    name="Forbipasserende Agent",
    handoff_description="Legger til sjeldne kommenterer fra forbipasserende",
    instructions=prompt_with_handoff_instructions(
        "Output: nøyaktig ÉN meldingsobjekt (ikke liste) for en forbipasserende med role 'bystander'. "
        "Sett 'name' til et realistisk norsk fornavn. 1–3 setninger, norsk. "
        "Tone: observatør. Kommentér kort og troverdig på det som skjer, uten å ta over samtalen. "
        "Medium: kan mildt støtte eller be om ro; Vanskelig: kan uttrykke utålmodighet eller legge press, men aldri bli truende eller grov. "
        "Ingen metatekst, ingen løsninger på egne vegne."
    ),
)

colleague_agent = Agent(
    name="Kollega Agent",
    handoff_description="Gir støtte fra en kollega ved behov",
    instructions=prompt_with_handoff_instructions(
        "Output: nøyaktig ÉN meldingsobjekt (ikke liste) fra en kollega med role 'employee'. "
        "Sett 'name' til et realistisk norsk fornavn som IKKE er lik 'user_name' i konteksten. 1–3 setninger, norsk. "
        "Støtt den ansatte høflig: tilby konkret hjelp (sjekke kvittering, hente ny drikk, tilkalle leder), holde ro, avklare misforståelser. "
        "Ikke overstyr kunden eller den ansatte, ikke løft saker du ikke har mandat til, ingen metatekst. Bare ved Medium/Vanskelig."
    ),
)


# Director agent composes the structured output
scenario_agent = Agent(
    name="Scenarioleder",
    instructions=prompt_with_handoff_instructions(
        "Du er scenarieleder for en kriseøvelse ved Sit Kafe. Svar alltid på norsk. Returner KUN et JSON/dict som samsvarer med Schema 'ScenarioOutput' "
        "med feltene: oppdrag (valgfritt), sjekkliste (valgfritt), meldinger (påkrevd), scenarioresultat (valgfritt), tilbakemelding (valgfritt). "
        "Ingen kodeblokker, ingen metatekst. Følg reglene:\n"
        "- Første tur (turn_count == '0'): returner nøyaktig TO meldinger i denne rekkefølgen: (1) Scene {name:'Scene', role:'system'} og (2) sint kunde {role:'customer'}. Bruk handoffs til Scene/Kunde for disse.\n"
        "- Etter første tur: fortsett dialogen logisk basert på 'Brukerens siste svar' fra input. Produser normalt 1 melding (kunden). "
        "  Hvis 'difficulty' er 'Medium' eller 'Vanskelig', kan du SOME ganger legge til ÉN ekstra kommentar fra forbipasserende ELLER kollega (aldri begge samtidig).\n"
        "- Maks 4 setninger per melding. Bruk realistiske norske fornavn. Hvis det finnes 'user_name' i konteksten, kan kunden tiltale den ansatte ved dette navnet.\n"
        "- Hold kontinuitet: behold samme sak og detaljer som tidligere. Ikke introduser ny informasjon som strider mot historikken.\n"
        "- Oppdrag/sjekkliste (valgfritt): etter første tur kan du kort gi 'oppdrag.beskrivelse' (<=4 setninger) og 2–4 sjekklistepunkter for den ansatte (f.eks. 'Bekreft problemet', 'Hold rolig tone', 'Tilby konkret løsning').\n"
        "- Slutt: senest innen 'max_turns' eller når konflikten er tydelig løst/feilet, fyll ut 'scenarioresultat' (1–2 setninger) og 'tilbakemelding' (1–3 setninger, konkret og hjelpsom). Ikke før.\n"
        "- Delegér for meldingsinnhold via handoffs til Scene/Kunde/Forbipasserende/Kollega ved behov."
    ),
    handoffs=[scene_agent, customer_agent, bystander_agent, colleague_agent],
    input_guardrails=[InputGuardrail(guardrail_function=check_training_context)],
    output_type=ScenarioOutput,
)


class EndDecision(BaseModel):
    should_end: bool
    result: Optional[str] = None
    feedback: Optional[str] = None


end_monitor_agent = Agent(
    name="Avslutningsvakt",
    handoff_description="Overvåker om scenariet skal avsluttes",
    instructions=(
        "Returner KUN et JSON/dict med feltene: should_end (bool), result (valgfri tekst), feedback (valgfri tekst). "
        "Vurder siste meldinger, 'difficulty', 'turn_count' og 'max_turns' fra konteksten. "
        "Hvis turn_count >= max_turns eller konflikten virker tydelig løst/feilet, sett should_end=true og fyll 'result' (1–2 setninger, norsk) og 'feedback' (1–3 setninger, norsk og konstruktiv). "
        "Ellers: should_end=false. Ingen kodeblokker."
    ),
    output_type=EndDecision,
)


def coerce_scenario_output(val) -> ScenarioOutput:
    """Coerce various return types into a ``ScenarioOutput`` instance.

    Accepts ``ScenarioOutput`` objects, raw dicts, JSON strings or plain text.
    On invalid input a minimal structured fallback is produced so callers can
    rely on receiving a valid ``ScenarioOutput``.
    """
    try:
        if isinstance(val, ScenarioOutput):
            return val
        if isinstance(val, dict):
            return ScenarioOutput(**val)
        if isinstance(val, str):
            cleaned = val.strip()
            cleaned = re.sub(r"^```\w*\n|```$", "", cleaned)
            cleaned = cleaned.strip().strip("`")
            data = None
            try:
                data = json.loads(cleaned)
            except Exception:
                try:
                    import ast

                    data = ast.literal_eval(cleaned)
                except Exception:
                    data = None
            if isinstance(data, dict):
                # Either a full ScenarioOutput or a single message object
                if {"name", "role", "content"} <= set(data.keys()):
                    msg = ScenarioMessage(**data)
                    return ScenarioOutput(
                        oppdrag=None,
                        sjekkliste=[],
                        meldinger=[msg],
                        scenarioresultat=None,
                        tilbakemelding=None,
                    )
                return ScenarioOutput(**data)
            if isinstance(data, list):
                try:
                    msgs = [ScenarioMessage(**m) for m in data if isinstance(m, dict)]
                    return ScenarioOutput(
                        oppdrag=None,
                        sjekkliste=[],
                        meldinger=msgs,
                        scenarioresultat=None,
                        tilbakemelding=None,
                    )
                except Exception:
                    pass

        # Fallback: wrap plain text into a minimal structured object
        is_initial_local = (
            st.session_state.get("turns", 0) == 0
            and len(st.session_state.get("history", [])) == 0
        )
        msg_role = "system" if is_initial_local else "customer"
        msg_name = "Scene" if is_initial_local else "Kunde"
        content = str(val)
        return ScenarioOutput(
            oppdrag=None,
            sjekkliste=[],
            meldinger=[
                ScenarioMessage(name=msg_name, role=msg_role, content=content)
            ],
            scenarioresultat=None,
            tilbakemelding=None,
        )
    except Exception:
        # Final fallback: empty conversation step
        return ScenarioOutput(
            oppdrag=None,
            sjekkliste=[],
            meldinger=[],
            scenarioresultat=None,
            tilbakemelding=None,
        )


def call_model(compiled_input: str, stream_placeholder: Optional[object] = None) -> List[Dict]:
    # Show typing indicator right away
    start_time = time.time()
    if stream_placeholder is not None:
        stream_placeholder.markdown(
            "<div class='typing-indicator'><span>Jobber</span> "
            "<span class='typing-dots'><span></span><span></span><span></span></span>"
            "</div>",
            unsafe_allow_html=True,
        )

    def _ctx() -> Dict[str, str]:
        return {
            "difficulty": str(st.session_state.get("difficulty", "")),
            "user_name": str(st.session_state.get("user_name", "")),
            "turn_count": str(st.session_state.get("turns", 0)),
            "max_turns": str(st.session_state.get("max_turns", 6)),
        }

    async def _run():
        result = await Runner.run(scenario_agent, compiled_input, context=_ctx())
        return result.final_output

    raw_out = run_async(_run())
    # Robustly coerce the agent output into ScenarioOutput
    out: ScenarioOutput = coerce_scenario_output(raw_out)

    # Minimum indicator time for perceived streaming feel
    elapsed = time.time() - start_time
    if stream_placeholder is not None and elapsed < MIN_STREAM_TIME_SEC:
        time.sleep(MIN_STREAM_TIME_SEC - elapsed)

    # Build cleaned messages and optional meta
    cleaned: List[Dict] = []
    is_initial = (st.session_state.get("turns", 0) == 0 and len(st.session_state.get("history", [])) == 0)

    # Save meta except on initial turn (keeps first turn minimal)
    if not is_initial:
        st.session_state.last_meta = {
            "oppdrag": (out.oppdrag.beskrivelse if out.oppdrag else None),
            "sjekkliste": out.sjekkliste or [],
            "scenarioresultat": (out.scenarioresultat.dict() if out.scenarioresultat else None),
            "tilbakemelding": (out.tilbakemelding.dict() if out.tilbakemelding else None),
        }
    else:
        st.session_state.last_meta = {}

    messages = out.meldinger or []
    # On the very first turn we expect two messages: Scene (system) then a customer.
    # Some models may occasionally only return the scene. If so, synthesize the
    # first customer reply using the dedicated customer_agent to keep UX consistent.
    if is_initial:
        try:
            has_customer = any(getattr(m, "role", "") == "customer" for m in messages)
            if not has_customer:
                scene_text = ""
                for m in messages:
                    if getattr(m, "role", "") == "system" or str(getattr(m, "name", "")).strip().lower() in {"scene", "forteller"}:
                        scene_text = m.content or ""
                        break

                async def _gen_customer() -> Optional[List[ScenarioMessage]]:
                    prompt = (
                        "Scenen som er satt:\n" + (scene_text or "Sit Kafe, en kunde er misfornøyd.") +
                        "\n\nSkriv den første kundereplikken som matcher scenen."
                    )
                    res = await Runner.run(customer_agent, prompt, context=_ctx())
                    out_val = res.final_output
                    # Parse with the shared coercer and extract messages
                    try:
                        parsed = coerce_scenario_output(out_val)
                        msgs = parsed.meldinger or []
                    except Exception:
                        msgs = []
                    # If coercion fails, wrap the text as a customer line
                    if not msgs:
                        if isinstance(out_val, str) and out_val.strip():
                            return [
                                ScenarioMessage(
                                    name="Kunde", role="customer", content=str(out_val).strip()
                                )
                            ]
                    return msgs

                new_msgs = run_async(_gen_customer())
                if new_msgs:
                    messages.extend(new_msgs)
        except Exception:
            # Graceful fallback: ensure at least a basic customer line exists
            if not any(getattr(m, "role", "") == "customer" for m in messages):
                messages.append(
                    ScenarioMessage(
                        name="Kunde",
                        role="customer",
                        content=(
                            "Hei, dette er ikke greit. Jeg har ventet lenge og bestillingen min ble feil."
                        ),
                    )
                )
        # Keep only the first two messages for the bootstrap (Scene + Kunde)
        messages = messages[:2]

    for m in messages:
        cleaned.append({"name": m.name, "role": m.role, "content": m.content})

    # If no explicit end produced and not initial, let monitor decide
    has_explicit_end = bool(out.scenarioresultat and out.tilbakemelding)
    if (not is_initial) and (not has_explicit_end):
        async def _monitor() -> EndDecision:
            summary = {
                "meldinger": [m.dict() for m in out.meldinger] if out.meldinger else [],
                "scenarioresultat": (out.scenarioresultat.dict() if out.scenarioresultat else None),
                "tilbakemelding": (out.tilbakemelding.dict() if out.tilbakemelding else None),
            }
            monitor_input = json.dumps(summary, ensure_ascii=False)
            res = await Runner.run(end_monitor_agent, monitor_input, context=_ctx())
            out_val = res.final_output
            if isinstance(out_val, EndDecision):
                return out_val
            if isinstance(out_val, dict):
                try:
                    return EndDecision(**out_val)
                except Exception:
                    return EndDecision(should_end=False)
            if isinstance(out_val, str):
                try:
                    data = json.loads(out_val)
                    if isinstance(data, dict):
                        return EndDecision(**data)
                except Exception:
                    pass
            return EndDecision(should_end=False)

        decision: EndDecision = run_async(_monitor())
        if decision and decision.should_end:
            st.session_state.last_meta = {
                "oppdrag": (out.oppdrag.beskrivelse if out.oppdrag else None),
                "sjekkliste": out.sjekkliste or [],
                "scenarioresultat": {"name": "Scenarioresultat", "role": "system", "content": decision.result or ""},
                "tilbakemelding": {"name": "Tilbakemelding", "role": "system", "content": decision.feedback or ""},
            }

    return cleaned
