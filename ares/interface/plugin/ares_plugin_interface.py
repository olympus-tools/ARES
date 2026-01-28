r"""
________________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
|              $$  __$$\ $$  __$$\ $$  _____|$$  __$$\                 |
|              $$ /  $$ |$$ |  $$ |$$ |      $$ /  \__|                |
|              $$$$$$$$ |$$$$$$$  |$$$$$\    \$$$$$$\                  |
|              $$  __$$ |$$  __$$< $$  __|    \____$$\                 |
|              $$ |  $$ |$$ |  $$ |$$ |      $$\   $$ |                |
|              $$ |  $$ |$$ |  $$ |$$$$$$$$\ \$$$$$$  |                |
|              \__|  \__|\__|  \__|\________| \______/                 |
|                                                                      |
|              Automated Rapid Embedded Simulation (c)                 |
|______________________________________________________________________|

Copyright 2025 olympus-tools contributors. Contributors to this project
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

    https://github.com/olympus-tools/ARES/blob/master/LICENSE
"""

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any

from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(__name__)


@typechecked
def AresPluginInterface(
    plugin_input: dict[str, Any],
):
    """Execute plugin based on wf_element_value configuration using importlib.

    Args:
        plugin_input (dict[str, Any]): Dictionary containing plugin configuration
    """
    try:
        plugin_path = plugin_input["plugin_path"]
        module_name = f"ares_plugin_{plugin_path.stem}_{os.getpid()}"

        # Create module specification
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None or spec.loader is None:
            logger.error(
                f"{plugin_input.get('wf_element_name')}: Could not load plugin {plugin_path}"
            )
            return

        # Create and configure module
        module = importlib.util.module_from_spec(spec)

        # Add plugin directory to sys.path temporarily
        plugin_dir = plugin_path.parent
        path_added = False
        if str(plugin_dir) not in sys.path:
            sys.path.insert(0, str(plugin_dir))
            path_added = True

        try:
            # Add to sys.modules and execute
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Call plugin's main function with explicit arguments
            if plugin_input["plugin_name"]:
                plugin_name = plugin_input["plugin_name"]
            else:
                plugin_name = "ares_plugin"

            if hasattr(module, plugin_name):
                getattr(module, plugin_name)(plugin_input=plugin_input)
            else:
                logger.error(
                    f"{plugin_input.get('wf_element_name')}: Plugin {plugin_path.name} does not have an 'ares_plugin' function"
                )
                return

            logger.debug(
                f"{plugin_input.get('wf_element_name')}: Plugin {plugin_path.name} executed successfully"
            )

        finally:
            # Cleanup
            if path_added and str(plugin_dir) in sys.path:
                sys.path.remove(str(plugin_dir))
            if module_name in sys.modules:
                del sys.modules[module_name]

    except Exception as e:
        logger.error(
            f"{plugin_input.get('wf_element_name')}: Plugin execution failed for {plugin_input['plugin_path'].name}: {e}"
        )
        return
