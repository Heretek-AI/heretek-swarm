"""Beta — validation agent node."""

from __future__ import annotations

from functools import partial
from typing import Awaitable, Callable

from tier1.deliberation.nodes._base import run_agent
from tier1.deliberation.state import DeliberationEvent, DeliberationState
from tier1.llm.garage import ModelGarage

EventSink = Callable[[DeliberationEvent], Awaitable[None]]


async def beta_node(
    state: DeliberationState,
    garage: ModelGarage,
    sink: EventSink | None = None,
) -> DeliberationState:
    return await run_agent(state, garage, agent="beta", sink=sink)


def make_beta_node(garage: ModelGarage, sink: EventSink | None = None):
    if sink is None:
        return partial(beta_node, garage=garage)
    return partial(beta_node, garage=garage, sink=sink)
