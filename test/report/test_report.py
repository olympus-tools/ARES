r"""
________________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
|              $$ /  $$ |$$ |  $$ |$$  _____|$$ /  \__|                |
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

from pathlib import Path

import pytest

from ares.core.workflow import Workflow
from ares.pydantic_models.workflow_model import PluginElement, WorkflowModel
from ares.report import Report


def _workflow_with_order(names: list[str]) -> Workflow:
    """Builds a lightweight validated workflow fixture for report tests."""
    workflow = Workflow.__new__(Workflow)
    workflow._file_path = Path("workflow.json")
    workflow.workflow_order = names
    workflow.workflow = WorkflowModel(
        root={name: PluginElement(file_path=Path("plugin.py")) for name in names}
    )
    return workflow


# TEST: Report.save
def test_report_save_writes_diagram_and_ordered_list(tmp_path: Path):
    """
    Tests that a report contains the workflow order as a diagram and list.

    Args:
        tmp_path (Path): Pytest fixture providing a temporary output directory.
    """
    workflow = _workflow_with_order(["first", "second"])
    workflow.workflow["first"].hash_list = {"measurement_hash": []}
    workflow.workflow["second"].hash_list = {
        "function_a_hash": ["measurement_hash"],
        "function_b_hash": ["measurement_hash"],
        "merge_hash": ["function_a_hash", "function_b_hash"],
    }
    output_dir = tmp_path / "nested"

    Report(workflow).save(output_dir=output_dir)

    report = next(output_dir.glob("*.html")).read_text(encoding="utf-8")
    assert report.index(">first<") < report.index(">second<")
    assert 'aria-label="Workflow graph"' in report
    assert 'data-graph-edge-source="node-0"' in report
    assert 'data-graph-edge-target="node-1"' in report
    assert 'class="graph-node Plugin"' in report
    assert 'class="graph-edge"' in report
    assert "background: #000" in report
    assert "<title>ARES report</title>" in report
    assert "<h1>ARES report</h1>" in report
    assert "Workflow file (input)" in report
    assert "Report created" in report
    assert "data-graph-viewport" in report
    assert "pointerdown" in report
    assert "data-graph-reset" in report
    assert "Dependencies" in report
    assert 'aria-label="Hash dependency graph"' in report
    assert "measurement_..." in report
    assert "data-graph-edge-source" in report
    assert "data-graph-node-width" in report
    assert 'marker-end="url(#graph-arrow-workflow)"' in report
    assert 'marker-end="url(#graph-arrow-dependencies)"' in report
    assert "GRAPH_CONFIG" in report
    assert "max-width: 50cm" in report
    assert "overflow-x: hidden" in report
    assert "min-width: 40rem" in report
    assert "height: 32rem" in report
    assert "flex: 1 1 auto" in report
    assert "height: 100%" in report
    assert "width: 100%" in report
    assert "const graphScale" in report
    assert "canvas.viewBox.baseVal.width - nodeWidth" in report
    assert "<caption>" not in report
    assert "<th>Inputs</th>" not in report
    assert "<th>Element workflow</th>" not in report
    assert 'rx="8"' in report
    assert "https://github.com/olympus-tools/ARES" in report
    assert "https://github.com/olympus-tools/ARES/blob/master/LICENSE" in report


def test_report_save_escapes_element_names(tmp_path: Path):
    """
    Tests that workflow names are escaped before being written to HTML.

    Args:
        tmp_path (Path): Pytest fixture providing a temporary output directory.
    """
    workflow = _workflow_with_order(["<unsafe>&"])
    output_dir = tmp_path / "output"

    Report(workflow).save(output_dir=output_dir)

    report = next(output_dir.glob("*.html")).read_text(encoding="utf-8")
    assert "&lt;unsafe&gt;&amp;" in report
    assert "<unsafe>" not in report


def test_report_save_writes_empty_order(tmp_path: Path):
    """
    Tests that an empty workflow order produces an empty element table.

    Args:
        tmp_path (Path): Pytest fixture providing a temporary output directory.
    """
    output_dir = tmp_path / "output"

    Report(_workflow_with_order([])).save(output_dir=output_dir)

    report = next(output_dir.glob("*.html")).read_text(encoding="utf-8")
    assert '<table class="report-table element-table">' in report
    assert "<tbody>\n                \n            </tbody>" in report


def test_report_save_logs_unknown_workflow_element(tmp_path: Path, caplog):
    """
    Tests that an inconsistent workflow order is logged as a warning.

    Args:
        tmp_path (Path): Pytest fixture providing a temporary output directory.
        caplog: Pytest fixture capturing warning logs.
    """
    workflow = _workflow_with_order([])
    workflow.workflow_order = ["missing"]

    Report(workflow).save(output_dir=tmp_path)

    assert "unknown element" in caplog.text


# TEST: Report browser behavior
def test_report_html_supports_browser_graph_interaction(tmp_path: Path):
    """Tests report graph rendering and controls in a real browser.

    Args:
        tmp_path (Path): Pytest fixture providing a temporary output directory.
    """
    playwright_api = pytest.importorskip("playwright.sync_api")
    workflow = _workflow_with_order(["first", "second"])
    output_dir = tmp_path / "output"
    Report(workflow).save(output_dir=output_dir)
    report_path = next(output_dir.glob("*.html"))

    with playwright_api.sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except playwright_api.Error as exc:
            pytest.skip(f"Chromium is not installed: {exc}")

        with browser:
            page = browser.new_page(viewport={"width": 1200, "height": 900})
            page.goto(report_path.as_uri())

            assert page.title() == "ARES report"
            assert page.locator("[data-graph-viewport]").count() == 2
            assert page.locator("[data-graph-node]").first.is_visible()

            viewport = page.locator("[data-graph-viewport]").first
            viewport.hover()
            page.mouse.wheel(0, -500)
            transformed_canvas = page.locator("[data-graph-canvas]").first
            assert "scale(1.1)" in transformed_canvas.get_attribute("style")

            page.locator("[data-graph-reset]").first.click()
            assert "scale(1)" in transformed_canvas.get_attribute("style")

            node = page.locator("[data-graph-node]").first
            initial_transform = node.get_attribute("transform")
            node_box = node.bounding_box()
            assert node_box is not None
            page.mouse.move(
                node_box["x"] + node_box["width"] / 2,
                node_box["y"] + node_box["height"] / 2,
            )
            page.mouse.down()
            page.mouse.move(
                node_box["x"] + node_box["width"] / 2 + 40,
                node_box["y"] + node_box["height"] / 2 + 20,
            )
            page.mouse.up()
            assert node.get_attribute("transform") != initial_transform
