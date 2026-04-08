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

    https://github.com/olympus-tools/ARES/blob/master/LICENSE
"""

import importlib.util
import os
import sys
from pathlib import Path

from ares.pydantic_models.workflow_model import WorkflowElement
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger

logger = create_logger(__name__)


@typechecked
def AresPluginInterface(
    plugin_element_name: str,
    workflow_scope: dict[str, WorkflowElement],
):
    """Execute plugin based on wf_element_value configuration using importlib.

    Args:
        plugin_element_name (str): The name of the workflow element.
        workflow_scope (dict[str, WorkflowElement]): The scope of the workflow containing all elements.
    """
    try:
        plugin_element_value = workflow_scope[plugin_element_name]
        plugin_path: Path = getattr(plugin_element_value, "plugin_path")

        module_name = f"ares_plugin_{plugin_path.stem}_{os.getpid()}"

        # Create module specification
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        if spec is None or spec.loader is None:
            logger.error(f"{plugin_element_name}: Could not load plugin {plugin_path}")
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

            # Determine the plugin entry-point function name
            plugin_name: str = (
                getattr(plugin_element_value, "plugin_name", None) or "ares_plugin"
            )

            if hasattr(module, plugin_name):
                getattr(module, plugin_name)(workflow_scope=workflow_scope)
            else:
                logger.error(
                    f"{plugin_element_name}: Plugin {plugin_path.name} does not have an '{plugin_name}' function"
                )
                return

            logger.debug(
                f"{plugin_element_name}: Plugin {plugin_path.name} executed successfully"
            )

        finally:
            # Cleanup
            if path_added and str(plugin_dir) in sys.path:
                sys.path.remove(str(plugin_dir))
            if module_name in sys.modules:
                del sys.modules[module_name]

    except Exception as e:
        logger.error(f"{plugin_element_name}: Plugin execution failed: {e}")
        return
