r"""
________________________________________________________________________
|                                                                      |
|               $$$$$$\  $$$$$$$\  $$$$$$$$\  $$$$$$\                  |
|              $$  __$$\ $$ |  $$ |$$  _____|$$  __$$\                 |
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

import getpass
from datetime import datetime
from html import escape
from pathlib import Path

from ares.core.workflow import Workflow
from ares.core.version import __commit_id__, __version__
from ares.utils.decorators import typechecked_dev as typechecked
from ares.utils.logger import create_logger


_ELEMENT_STYLES: dict[str, str] = {
    "data": "Data",
    "parameter": "Parameters",
    "plugin": "Plugin",
    "sim_unit": "SW_Unit",
    "merge": "Merge",
}
_GRAPH_NODE_WIDTH = 220
_GRAPH_NODE_HEIGHT = 64
_GRAPH_HORIZONTAL_GAP = 100
_GRAPH_VERTICAL_GAP = 40
_GRAPH_PADDING = 40
_GRAPH_MIN_WIDTH = 760
_GRAPH_MIN_HEIGHT = 240

_HTML_STYLE = """
* {
    box-sizing: border-box;
}
html {
    background: #000;
}
body {
    background: #000;
    color: #eee;
    font-family: sans-serif;
    margin: 0;
    overflow-x: hidden;
    padding: 2rem 2rem 4.5rem;
}
h1 {
    color: #fff;
    margin-left: auto;
    margin-right: auto;
    max-width: 50cm;
    margin-top: 0;
    text-align: left;
    width: 100%;
}
.report-section {
    margin: 1.5rem 0;
}
.report-table {
    border-collapse: collapse;
    margin: 0 auto;
    max-width: 50cm;
    width: 100%;
}
.report-table th,
.report-table td {
    border: 1px solid #333;
    padding: 0.7rem;
    text-align: left;
    vertical-align: top;
}
.report-table th {
    background: #1b1b1b;
    color: #fff;
    white-space: nowrap;
}
.report-table tr:nth-child(even) {
    background: #0d0d0d;
}
.workflow-window {
    background: #111;
    border: 1px solid #444;
    border-radius: 8px;
    box-shadow: 0 0 1rem #000;
    display: flex;
    flex-direction: column;
    height: 32rem;
    min-width: 40rem;
    overflow: hidden;
    width: 100%;
}
.workflow-window-header {
    align-items: center;
    background: #1b1b1b;
    border-bottom: 1px solid #444;
    display: flex;
    justify-content: space-between;
    padding: 0.65rem 0.8rem;
}
.workflow-window-title {
    color: #fff;
    font-weight: 600;
}
.workflow-window-hint {
    color: #888;
    font-size: 0.8rem;
}
.workflow-controls {
    display: flex;
    gap: 0.3rem;
}
.workflow-controls button {
    background: #2a2a2a;
    border: 1px solid #555;
    border-radius: 4px;
    color: #ddd;
    cursor: pointer;
    padding: 0.2rem 0.5rem;
}
.workflow-controls button:hover {
    background: #3a3a3a;
}
.workflow-viewport {
    background: #050505;
    cursor: grab;
    flex: 1 1 auto;
    min-height: 0;
    overflow: hidden;
    position: relative;
    touch-action: none;
    width: 100%;
}
.workflow-viewport.is-dragging {
    cursor: grabbing;
}
.graph-canvas {
    display: block;
    height: 100%;
    transform-origin: 0 0;
    width: 100%;
}
.graph-node {
    cursor: grab;
}
.graph-node.is-dragging {
    cursor: grabbing;
}
.graph-node-shape {
    fill: #151515;
    stroke: #888;
    stroke-width: 2;
}
.graph-node-label {
    fill: #eee;
    font-size: 13px;
    text-anchor: middle;
}
.graph-node-owner {
    fill: #999;
    font-size: 11px;
    text-anchor: middle;
}
.graph-node.Data .graph-node-shape {
    stroke: #1e9bec;
}
.graph-node.Data .graph-node-label {
    fill: #1e9bec;
}
.graph-node.Parameters .graph-node-shape {
    stroke: #a44300;
}
.graph-node.Parameters .graph-node-label {
    fill: #a44300;
}
.graph-node.Plugin .graph-node-shape {
    stroke: #e5d300;
}
.graph-node.Plugin .graph-node-label {
    fill: #e5d300;
}
.graph-node.SW_Unit .graph-node-shape {
    stroke: #d30000;
}
.graph-node.SW_Unit .graph-node-label {
    fill: #d30000;
}
.graph-node.Merge .graph-node-shape {
    stroke: #7b2d8b;
}
.graph-node.Merge .graph-node-label {
    fill: #7b2d8b;
}
.graph-edge {
    fill: none;
    stroke: #888;
    stroke-width: 2;
}
.graph-empty {
    color: #888;
    padding: 5rem;
}
.report-footer {
    background: #080808;
    border-top: 1px solid #222;
    bottom: 0;
    color: #666;
    font-size: 0.8rem;
    left: 0;
    padding: 0.65rem 1rem;
    position: fixed;
    right: 0;
    text-align: center;
    z-index: 10;
}
.report-footer a {
    color: #888;
    text-decoration: none;
}
.report-footer a:hover {
    color: #ccc;
    text-decoration: underline;
}
"""

_HTML_SCRIPT = """
(() => {
    const GRAPH_CONFIG = {
        initialScale: 1,
        minScale: 0.5,
        maxScale: 2.5,
        zoomStep: 0.1,
    };

    document.querySelectorAll("[data-graph-viewport]").forEach((viewport) => {
        const canvas = viewport.querySelector("[data-graph-canvas]");
        const resetButton = viewport
            .closest(".workflow-window")
            .querySelector("[data-graph-reset]");
        if (!canvas || !resetButton) {
            return;
        }

        let scale = GRAPH_CONFIG.initialScale;
        let offsetX = 0;
        let offsetY = 0;
        let viewportDrag = null;
        let nodeDrag = null;
        const nodes = new Map(
            [...canvas.querySelectorAll("[data-graph-node]")].map((node) => [
                node.dataset.graphNodeId,
                node,
            ])
        );
        const edges = [...canvas.querySelectorAll("[data-graph-edge]")];

        const applyTransform = () => {
            canvas.style.transform =
                `translate(${offsetX}px, ${offsetY}px) scale(${scale})`;
        };

        const updateEdges = () => {
            edges.forEach((edge) => {
                const source = nodes.get(edge.dataset.graphEdgeSource);
                const target = nodes.get(edge.dataset.graphEdgeTarget);
                if (!source || !target) {
                    return;
                }
                const sourceX = Number(source.dataset.graphNodeX);
                const sourceY = Number(source.dataset.graphNodeY);
                const targetX = Number(target.dataset.graphNodeX);
                const targetY = Number(target.dataset.graphNodeY);
                const sourceWidth = Number(source.dataset.graphNodeWidth);
                const targetWidth = Number(target.dataset.graphNodeWidth);
                const sourceHeight = Number(source.dataset.graphNodeHeight);
                const targetHeight = Number(target.dataset.graphNodeHeight);
                const sourceCenterX = sourceX + sourceWidth / 2;
                const targetCenterX = targetX + targetWidth / 2;
                const startsOnRight = sourceCenterX <= targetCenterX;
                edge.setAttribute(
                    "x1",
                    String(sourceX + (startsOnRight ? sourceWidth : 0))
                );
                edge.setAttribute("y1", String(sourceY + sourceHeight / 2));
                edge.setAttribute(
                    "x2",
                    String(targetX + (startsOnRight ? 0 : targetWidth))
                );
                edge.setAttribute("y2", String(targetY + targetHeight / 2));
            });
        };

        const centerCanvas = () => {
            const width = canvas.clientWidth;
            const height = canvas.clientHeight;
            offsetX = (viewport.clientWidth - width * scale) / 2;
            offsetY = (viewport.clientHeight - height * scale) / 2;
            applyTransform();
        };

        const graphScale = () => {
            const widthScale =
                canvas.clientWidth / canvas.viewBox.baseVal.width;
            const heightScale =
                canvas.clientHeight / canvas.viewBox.baseVal.height;
            return Math.min(widthScale, heightScale);
        };

        viewport.addEventListener("pointerdown", (event) => {
            viewportDrag = {
                pointerId: event.pointerId,
                startX: event.clientX,
                startY: event.clientY,
                offsetX,
                offsetY,
            };
            viewport.classList.add("is-dragging");
            viewport.setPointerCapture(event.pointerId);
        });

        viewport.addEventListener("pointermove", (event) => {
            if (!viewportDrag || viewportDrag.pointerId !== event.pointerId) {
                return;
            }
            offsetX = viewportDrag.offsetX + event.clientX - viewportDrag.startX;
            offsetY = viewportDrag.offsetY + event.clientY - viewportDrag.startY;
            applyTransform();
        });

        const stopDragging = (event) => {
            if (!viewportDrag || viewportDrag.pointerId !== event.pointerId) {
                return;
            }
            viewportDrag = null;
            viewport.classList.remove("is-dragging");
            viewport.releasePointerCapture(event.pointerId);
        };

        viewport.addEventListener("pointerup", stopDragging);
        viewport.addEventListener("pointercancel", stopDragging);
        viewport.addEventListener("wheel", (event) => {
            event.preventDefault();
            scale = Math.min(
                GRAPH_CONFIG.maxScale,
                Math.max(
                    GRAPH_CONFIG.minScale,
                    scale
                        + (event.deltaY < 0
                            ? GRAPH_CONFIG.zoomStep
                            : -GRAPH_CONFIG.zoomStep)
                )
            );
            applyTransform();
        }, {passive: false});

        nodes.forEach((node) => {
            node.addEventListener("pointerdown", (event) => {
                event.stopPropagation();
                nodeDrag = {
                    node,
                    pointerId: event.pointerId,
                    startX: event.clientX,
                    startY: event.clientY,
                    x: Number(node.dataset.graphNodeX),
                    y: Number(node.dataset.graphNodeY),
                };
                node.classList.add("is-dragging");
                node.setPointerCapture(event.pointerId);
            });
            node.addEventListener("pointermove", (event) => {
                if (!nodeDrag || nodeDrag.pointerId !== event.pointerId) {
                    return;
                }
                const nodeWidth = Number(node.dataset.graphNodeWidth);
                const nodeHeight = Number(node.dataset.graphNodeHeight);
                const maxX = Math.max(
                    0,
                    canvas.viewBox.baseVal.width - nodeWidth
                );
                const maxY = Math.max(
                    0,
                    canvas.viewBox.baseVal.height - nodeHeight
                );
                const x = Math.min(
                    maxX,
                    Math.max(
                        0,
                        nodeDrag.x
                            + (event.clientX - nodeDrag.startX)
                                / (scale * graphScale())
                    )
                );
                const y = Math.min(
                    maxY,
                    Math.max(
                        0,
                        nodeDrag.y
                            + (event.clientY - nodeDrag.startY)
                                / (scale * graphScale())
                    )
                );
                node.dataset.graphNodeX = String(x);
                node.dataset.graphNodeY = String(y);
                node.setAttribute("transform", `translate(${x}, ${y})`);
                updateEdges();
            });
            const stopNodeDragging = (event) => {
                if (!nodeDrag || nodeDrag.pointerId !== event.pointerId) {
                    return;
                }
                node.classList.remove("is-dragging");
                node.releasePointerCapture(event.pointerId);
                nodeDrag = null;
            };
            node.addEventListener("pointerup", stopNodeDragging);
            node.addEventListener("pointercancel", stopNodeDragging);
        });

        resetButton.addEventListener("click", () => {
            scale = GRAPH_CONFIG.initialScale;
            centerCanvas();
        });

        window.addEventListener("resize", centerCanvas);
        updateEdges();
        centerCanvas();
    });
})();
"""

logger = create_logger(name=__name__)


class Report:
    """Creates a self-contained HTML report for a processed workflow."""

    @typechecked
    def __init__(self, workflow: Workflow):
        """Initializes a report for a workflow.

        Args:
            workflow (Workflow): The processed workflow to render.
        """
        self.workflow = workflow

    @typechecked
    def save(self, output_dir: Path) -> None:
        """Writes the workflow report to the workflow output directory.

        Args:
            output_dir (Path): The workflow output directory.
        """
        try:
            report_path = self._get_output_path(output_dir=output_dir)
            report_html = self._render_html()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as file:
                file.write(report_html)
            logger.info(
                "Workflow report successfully written to %s.", report_path.resolve()
            )
        except (OSError, ValueError) as exc:
            logger.warning("Workflow report could not be written: %s", exc)

    def _get_output_path(self, output_dir: Path) -> Path:
        """Determines the report path from the workflow output directory."""
        report_path = self.workflow._eval_output_path(
            dir_path=output_dir, output_format="html"
        )
        if report_path is None:
            raise OSError("Could not determine the workflow report output path.")
        return report_path

    def _render_html(self) -> str:
        """Renders the complete HTML document."""
        elements = [
            self._resolve_element(name) for name in self.workflow.workflow_order
        ]
        diagram = self._render_diagram(elements)
        dependency_graph = self._render_dependency_graph()
        metadata = self._render_metadata()
        element_table = self._render_element_table()

        return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>ARES report</title>
    <style>
{_HTML_STYLE}
    </style>
</head>
<body>
    <h1>ARES report</h1>
    <section class="report-section">
        <table class="report-table metadata-table">
            <thead>
                <tr><th>Field</th><th>Value</th></tr>
            </thead>
            <tbody>
                {metadata}
            </tbody>
        </table>
    </section>
    <section class="report-section">
        <div class="workflow-window">
            <div class="workflow-window-header">
                <span class="workflow-window-title">Workflow</span>
                <span class="workflow-window-hint">Drag to move · Scroll to zoom</span>
                <div class="workflow-controls">
                    <button type="button" data-graph-reset>Reset view</button>
                </div>
            </div>
            <div class="workflow-viewport" data-graph-viewport>
                {diagram}
            </div>
        </div>
    </section>
    <section class="report-section">
        <div class="workflow-window">
            <div class="workflow-window-header">
                <span class="workflow-window-title">Dependencies</span>
                <span class="workflow-window-hint">Drag to move · Scroll to zoom</span>
                <div class="workflow-controls">
                    <button type="button" data-graph-reset>Reset view</button>
                </div>
            </div>
            <div class="workflow-viewport" data-graph-viewport>
                {dependency_graph}
            </div>
        </div>
    </section>
    <section class="report-section">
        <table class="report-table element-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Hashes</th>
                </tr>
            </thead>
            <tbody>
                {element_table}
            </tbody>
        </table>
    </section>
    <footer class="report-footer">
        <a href="https://github.com/olympus-tools/ARES">olympus-tools/ARES</a>
        · ARES {escape(__version__)} ({escape(__commit_id__)})
        · <a href="https://github.com/olympus-tools/ARES/blob/master/LICENSE">
            Apache License 2.0
          </a>
    </footer>
    <script>
{_HTML_SCRIPT}
    </script>
</body>
</html>
"""

    def _render_metadata(self) -> str:
        """Renders report metadata rows."""
        metadata = (
            ("Workflow file (input)", self.workflow._file_path.name),
            (
                "Report created",
                datetime.now().astimezone().isoformat(timespec="seconds"),
            ),
            ("User", getpass.getuser()),
        )
        return "".join(
            f"<tr><th>{escape(label)}</th><td>{escape(str(value))}</td></tr>"
            for label, value in metadata
        )

    @staticmethod
    def _render_svg_graph(
        graph_id: str,
        aria_label: str,
        graph_width: int,
        graph_height: int,
        nodes: list[tuple[str, float, float, str, str, str]],
        edges: list[tuple[str, str]],
    ) -> str:
        """Renders a graph with draggable nodes and dynamically updated edges."""
        svg_parts = [
            f'<svg class="graph-canvas" data-graph-canvas '
            f'viewBox="0 0 {graph_width} {graph_height}" '
            f'width="{graph_width}" height="{graph_height}" role="img" '
            f'aria-label="{escape(aria_label, quote=True)}">',
            f'<defs><marker id="graph-arrow-{escape(graph_id, quote=True)}" '
            'markerWidth="10" markerHeight="10" refX="8" refY="3" '
            'orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#888"/>'
            "</marker></defs>",
        ]
        node_lookup = {node_id: node for node_id, *node in nodes}
        for index, (source_id, target_id) in enumerate(edges):
            source = node_lookup[source_id]
            target = node_lookup[target_id]
            source_x, source_y, _, _, _ = source
            target_x, target_y, _, _, _ = target
            svg_parts.append(
                f'<line class="graph-edge" data-graph-edge '
                f'data-graph-edge-source="{escape(source_id, quote=True)}" '
                f'data-graph-edge-target="{escape(target_id, quote=True)}" '
                f'x1="{source_x}" y1="{source_y + _GRAPH_NODE_HEIGHT / 2}" '
                f'x2="{target_x}" y2="{target_y + _GRAPH_NODE_HEIGHT / 2}" '
                f'marker-end="url(#graph-arrow-{escape(graph_id, quote=True)})" '
                f'aria-label="Graph edge {index + 1}"/>'
            )

        for node_id, x, y, css_class, label, owner in nodes:
            owner_markup = (
                f'<text class="graph-node-owner" x="{_GRAPH_NODE_WIDTH / 2}" '
                f'y="{_GRAPH_NODE_HEIGHT - 17}">{escape(owner)}</text>'
                if owner
                else ""
            )
            title = escape(f"{label} ({owner})" if owner else label)
            svg_parts.append(
                f'<g class="graph-node {escape(css_class, quote=True)}" '
                f'data-graph-node data-graph-node-id="{escape(node_id, quote=True)}" '
                f'data-graph-node-x="{x}" data-graph-node-y="{y}" '
                f'data-graph-node-width="{_GRAPH_NODE_WIDTH}" '
                f'data-graph-node-height="{_GRAPH_NODE_HEIGHT}" '
                f'transform="translate({x}, {y})">'
                f"<title>{title}</title>"
                f'<rect class="graph-node-shape" x="0" y="0" '
                f'width="{_GRAPH_NODE_WIDTH}" height="{_GRAPH_NODE_HEIGHT}" rx="8"/>'
                f'<text class="graph-node-label" x="{_GRAPH_NODE_WIDTH / 2}" y="27">'
                f"{escape(label)}</text>"
                f"{owner_markup}</g>"
            )

        svg_parts.append("</svg>")
        return "".join(svg_parts)

    def _render_dependency_graph(self) -> str:
        """Renders the hash dependency graph as an inline SVG."""
        nodes: dict[str, set[str]] = {}
        node_types: dict[str, set[str]] = {}
        edges: set[tuple[str, str]] = set()
        for name in self.workflow.workflow_order:
            element = self.workflow.workflow.get(name)
            if element is None:
                raise ValueError(f"Workflow order references unknown element '{name}'.")
            _, css_class = self._resolve_element(name)

            for output_hash, dependencies in element.hash_list.items():
                nodes.setdefault(output_hash, set()).add(name)
                node_types.setdefault(output_hash, set()).add(css_class)
                for dependency_hash in dependencies:
                    nodes.setdefault(dependency_hash, set())
                    edges.add((dependency_hash, output_hash))

        if not nodes:
            return '<p class="graph-empty">No hash dependencies available.</p>'

        incoming = {node: set() for node in nodes}
        outgoing = {node: set() for node in nodes}
        for source, target in edges:
            incoming[target].add(source)
            outgoing[source].add(target)

        levels = {
            node: 0 for node, dependencies in incoming.items() if not dependencies
        }
        remaining_incoming = {
            node: set(dependencies) for node, dependencies in incoming.items()
        }
        queue = list(levels)
        while queue:
            source = queue.pop(0)
            for target in outgoing[source]:
                levels[target] = max(levels.get(target, 0), levels[source] + 1)
                remaining_incoming[target].discard(source)
                if not remaining_incoming[target]:
                    queue.append(target)
        for node in nodes:
            levels.setdefault(node, 0)

        columns: dict[int, list[str]] = {}
        for node, level in levels.items():
            columns.setdefault(level, []).append(node)
        for column in columns.values():
            column.sort()

        node_width = _GRAPH_NODE_WIDTH
        node_height = _GRAPH_NODE_HEIGHT
        horizontal_gap = _GRAPH_HORIZONTAL_GAP
        vertical_gap = _GRAPH_VERTICAL_GAP
        padding = _GRAPH_PADDING
        max_level = max(columns)
        max_column_size = max(len(column) for column in columns.values())
        graph_width = max(
            _GRAPH_MIN_WIDTH,
            (max_level + 1) * node_width + max_level * horizontal_gap + 2 * padding,
        )
        graph_height = max(
            _GRAPH_MIN_HEIGHT,
            max_column_size * node_height
            + (max_column_size - 1) * vertical_gap
            + 2 * padding,
        )

        positions: dict[str, tuple[float, float]] = {}
        for level, column in columns.items():
            column_height = len(column) * node_height + (len(column) - 1) * vertical_gap
            start_y = padding + (graph_height - 2 * padding - column_height) / 2
            x = padding + level * (node_width + horizontal_gap)
            for index, node in enumerate(column):
                positions[node] = (
                    x,
                    start_y + index * (node_height + vertical_gap),
                )

        node_ids = {
            node: f"node-{index}" for index, node in enumerate(sorted(positions))
        }
        graph_nodes = [
            (
                node_ids[node],
                x,
                y,
                sorted(node_types.get(node, {"Dependency"}))[0],
                f"{node[:12]}..." if len(node) > 12 else node,
                ", ".join(sorted(nodes[node])) or "dependency",
            )
            for node, (x, y) in positions.items()
        ]
        graph_edges = [
            (node_ids[source], node_ids[target]) for source, target in sorted(edges)
        ]
        return self._render_svg_graph(
            graph_id="dependencies",
            aria_label="Hash dependency graph",
            graph_width=graph_width,
            graph_height=graph_height,
            nodes=graph_nodes,
            edges=graph_edges,
        )

    def _render_element_table(self) -> str:
        """Renders the workflow element details table."""
        rows: list[str] = []
        for name in self.workflow.workflow_order:
            display_name, css_class = self._resolve_element(name)
            element = self.workflow.workflow.get(name)
            if element is None:
                raise ValueError(f"Workflow order references unknown element '{name}'.")

            hashes = self._format_hashes(element)
            rows.append(
                "<tr>"
                f"<td>{escape(display_name)}</td>"
                f'<td><span class="element-type {css_class}">{escape(element.type)}</span></td>'
                f"<td>{escape(hashes)}</td>"
                "</tr>"
            )
        return "".join(rows)

    @staticmethod
    def _format_hashes(element: object) -> str:
        """Formats the hash lists of a workflow element."""
        hash_list = getattr(element, "hash_list", {}) or {}
        return (
            "; ".join(
                f"{key}: {', '.join(str(value) for value in values) or '—'}"
                for key, values in hash_list.items()
            )
            or "—"
        )

    def _resolve_element(self, name: str) -> tuple[str, str]:
        """Resolves a workflow name into its display name and style.

        Args:
            name (str): The workflow element name from the execution order.

        Returns:
            tuple[str, str]: Display name and CSS class.

        Raises:
            ValueError: If the name or element type is invalid.
        """
        element = self.workflow.workflow.get(name)
        if element is None:
            raise ValueError(f"Workflow order references unknown element '{name}'.")
        if element.name is None:
            raise ValueError(f"Workflow element '{name}' has no name.")

        css_class = _ELEMENT_STYLES.get(element.type)
        if css_class is None:
            raise ValueError(
                f"Workflow element '{name}' has unsupported type '{element.type}'."
            )

        return element.name, css_class

    @staticmethod
    def _render_diagram(elements: list[tuple[str, str]]) -> str:
        """Renders workflow elements as a draggable SVG graph.

        Args:
            elements (list[tuple[str, str]]): Resolved workflow elements.

        Returns:
            str: The rendered diagram markup.
        """
        node_width = _GRAPH_NODE_WIDTH
        node_height = _GRAPH_NODE_HEIGHT
        horizontal_gap = _GRAPH_HORIZONTAL_GAP
        padding = _GRAPH_PADDING
        graph_width = max(
            _GRAPH_MIN_WIDTH,
            len(elements) * node_width
            + max(0, len(elements) - 1) * horizontal_gap
            + 2 * padding,
        )
        graph_height = _GRAPH_MIN_HEIGHT
        start_y = (graph_height - node_height) / 2
        graph_nodes = [
            (
                f"node-{index}",
                padding + index * (node_width + horizontal_gap),
                start_y,
                css_class,
                element_name,
                "",
            )
            for index, (element_name, css_class) in enumerate(elements)
        ]
        graph_edges = [
            (f"node-{index}", f"node-{index + 1}")
            for index in range(max(0, len(elements) - 1))
        ]
        return Report._render_svg_graph(
            graph_id="workflow",
            aria_label="Workflow graph",
            graph_width=graph_width,
            graph_height=graph_height,
            nodes=graph_nodes,
            edges=graph_edges,
        )
