r"""
________________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
|              $$  __$$\ $$ |  $$ |$$  _____|$$  __$$\                 |
|              $$ /  $$ |$$$$$$$  |$$ |      $$ /  \__|                |
|              $$$$$$$$ |$$$$$$$  |$$$$$\    \$$$$$$\                  |
|              $$  __$$ |$$  __$$< $$  __|    \____$$\                 |
|              $$ |  $$ |$$ |  $$ |$$ |      $$\   $$ |                |
|              $$$$$$$$ |$$ |  $$ |$$$$$$$$\ \$$$$$$  |                |
|              \__|  \__|\__|  \__|\________| \______/                 |
|                                                                      |
|              Automated Rapid Embedded Simulation (c)                 |
|______________________________________________________________________|

Copyright 2025 olympus-tools contributors. Dependencies and licenses
are listed in the NOTICE file:

    https://github.com/olympus-tools/ARES/blob/master/NOTICE

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License:

    https://www.apache.org/licenses/LICENSE-2.0
"""

from ares.interface.data.ares_signal import AresSignal
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(name=__name__)


@typechecked
def select_signals_by_source_priority(
    sim_data: list[AresSignal],
    source_priority: list[str],
) -> list[AresSignal]:
    """Keep the highest-priority signal for each label.

    Args:
        sim_data (list[AresSignal]): Signals retrieved for a simulation.
        source_priority (list[str]): Source names ordered from highest to
            lowest priority.

    Returns:
        list[AresSignal]: At most one signal per label, selected using the
            configured source priority.
    """
    signals_by_label: dict[str, list[AresSignal]] = {}
    for signal in sim_data:
        if signal.label not in signals_by_label:
            signals_by_label[signal.label] = []
        signals_by_label[signal.label].append(signal)

    selected_signals: list[AresSignal] = []
    for label, candidates in signals_by_label.items():
        if len(candidates) == 1:
            selected_signals.append(candidates[0])
            continue

        selected_signal = next(
            (
                signal
                for source in source_priority
                for signal in candidates
                if signal.source == source
            ),
            None,
        )
        if selected_signal is None:
            selected_signal = candidates[0]
            available_sources = []
            for signal in candidates:
                if signal.source not in available_sources:
                    available_sources.append(signal.source)
            logger.warning(
                f"No signal for label '{label}' matched source priority "
                f"{source_priority}. Available sources: {available_sources}. "
                f"Using the first signal from source '{selected_signal.source}'."
            )

        selected_signals.append(selected_signal)

    return selected_signals
