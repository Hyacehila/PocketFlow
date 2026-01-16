import collections
import warnings

from . import Flow


def visualize(
    flow: Flow,
    namespace: dict,
    *,
    direction: str = "LR",
    show_default: bool = False,
    highlight_starts: bool = True,
    max_nodes: int = 1000,
) -> str:
    """Export the connected flow graph to Mermaid (Markdown fenced).

    This function **does not execute any node logic**. It only inspects structural
    attributes such as `successors` and `start_node`.

    Args:
        flow (Flow):
            The entry flow to visualize.
        namespace (dict[str, object]):
            A mapping from variable name -> object reference, used to recover
            readable display names for nodes/flows (recommended: `locals()`).
            If not provided or empty, this function emits a warning and falls back
            to class-name based labels.
        direction (str):
            Mermaid direction: LR/RL/TB/TD/BT (case-insensitive; output is uppercased).
        show_default (bool):
            When False, "default" edges are rendered without a label (`A --> B`).
            When True, they are rendered as `A -->|default| B`.
        highlight_starts (bool):
            When True, highlights the "real start" for each Flow (entry and subflows),
            by following `start_node` through nested Flows until reaching a non-Flow.
        max_nodes (int):
            Maximum number of unique nodes to traverse; exceeded raises RuntimeError.

    Returns:
        str: Markdown fenced Mermaid flowchart.
    """
    # ============================================================
    # Configuration and validation
    # ============================================================

    direction_u = (direction or "LR").upper()
    if direction_u not in {"LR", "RL", "TB", "TD", "BT"}:
        raise ValueError("direction must be one of LR/RL/TB/TD/BT")
    if not isinstance(max_nodes, int) or max_nodes <= 0:
        raise ValueError("max_nodes must be a positive integer")

    # Normalize namespace to dict, warn if invalid
    if not namespace or not isinstance(namespace, dict):
        warnings.warn("Missing or invalid namespace; falling back to class-name labels")
        namespace = {}

    # ============================================================
    # Helper functions
    # ============================================================

    def _sort_keys(d):
        """Sort dictionary keys, handling non-comparable types gracefully."""
        try:
            return sorted(d)
        except Exception:
            return sorted(d, key=lambda x: str(x))

    def _escape(s: str, is_edge: bool = False) -> str:
        """Escape special characters for Mermaid syntax."""
        s = str(s).replace("\\", "\\\\")
        return s.replace("|", "\\|") if is_edge else s.replace('"', '\\"')

    def _get_successors(obj):
        """Get successors dict for an object, always returning a dict."""
        return getattr(obj, "successors", None) or {}

    # ============================================================
    # Label generation
    # ============================================================

    # Build mapping from object id to list of variable names
    names_by_obj_id = {
        id(v): [k]
        for k, v in namespace.items()
        if isinstance(k, str) and hasattr(v, "successors")
    }

    warned_multi_names, warned_missing_names = set(), set()
    unnamed_counter_by_class, label_cache = {}, {}

    def _label_for(obj) -> str:
        """Generate a human-readable label for a node or flow."""
        obj_id = id(obj)
        if obj_id in label_cache:
            return label_cache[obj_id]

        cls = obj.__class__.__name__
        names = names_by_obj_id.get(obj_id) or []

        if names:
            if len(names) > 1 and obj_id not in warned_multi_names:
                warned_multi_names.add(obj_id)
                warnings.warn(f"Multiple variable names for the same node/flow: {sorted(names)}")
            label = sorted(names)[0]
        else:
            if obj_id not in warned_missing_names:
                warned_missing_names.add(obj_id)
                warnings.warn(f"Missing variable name for object {cls}")
            n = unnamed_counter_by_class.get(cls, 0) + 1
            unnamed_counter_by_class[cls] = n
            label = cls if n == 1 else f"{cls}#{n}"

        label_cache[obj_id] = label
        return label

    # ============================================================
    # Step 1: Discover all nodes and edges via graph traversal
    # ============================================================

    obj_by_id, visit_order, visited = {}, [], set()
    edges = set()
    queue = collections.deque([flow])

    while queue:
        curr = queue.popleft()
        if curr is None:
            continue

        curr_id = id(curr)
        if curr_id in visited:
            continue

        visited.add(curr_id)
        obj_by_id[curr_id] = curr
        visit_order.append(curr_id)

        if len(visit_order) > max_nodes:
            raise RuntimeError(f"max_nodes exceeded: {max_nodes}")

        # Enqueue start node if this is a Flow
        if isinstance(curr, Flow):
            start_node = getattr(curr, "start_node", None)
            if start_node is not None:
                queue.append(start_node)

        # Enqueue all successors
        for action in _sort_keys(_get_successors(curr)):
            next_node = _get_successors(curr).get(action)
            if next_node is not None:
                edges.add((curr_id, str(action), id(next_node)))
                queue.append(next_node)

    # Build lookup tables
    order_index_by_obj_id = {obj_id: i for i, obj_id in enumerate(visit_order)}
    mermaid_id_by_obj_id = {obj_id: f"n{i}" for obj_id, i in order_index_by_obj_id.items()}

    # ============================================================
    # Step 2: Compute body nodes for each Flow
    # ============================================================

    flow_ids = [obj_id for obj_id in visit_order if isinstance(obj_by_id.get(obj_id), Flow)]
    body_by_flow_id = {}

    for flow_id in flow_ids:
        flow_obj = obj_by_id[flow_id]
        start_node = getattr(flow_obj, "start_node", None)

        if start_node is None:
            body_by_flow_id[flow_id] = set()
            continue

        # BFS to find all nodes in this flow's body
        body, queue, seen = set(), collections.deque([start_node]), set()

        while queue:
            node = queue.popleft()
            if node is None:
                continue

            node_id = id(node)
            if node_id in seen:
                continue

            seen.add(node_id)
            body.add(node_id)

            for action in _sort_keys(_get_successors(node)):
                next_node = _get_successors(node).get(action)
                if next_node is not None:
                    queue.append(next_node)

        body_by_flow_id[flow_id] = body

    # ============================================================
    # Step 3: Determine containment relationships
    # ============================================================

    # Map each node to its containing flow (first flow that includes it)
    container_flow_by_node_id = {}
    for flow_id in flow_ids:
        for node_id in body_by_flow_id.get(flow_id, set()):
            container_flow_by_node_id.setdefault(node_id, flow_id)

    # Map flows to their parent flows (flows that contain them as nodes)
    parent_flow_by_flow_id = {
        flow_id: container_flow_by_node_id[flow_id]
        for flow_id in flow_ids
        if (
            container_flow_by_node_id.get(flow_id) is not None
            and container_flow_by_node_id[flow_id] != flow_id
            and isinstance(obj_by_id.get(container_flow_by_node_id[flow_id]), Flow)
        )
    }

    # ============================================================
    # Step 4: Rewrite edges for expanded flows
    # ============================================================

    real_start_cache = {}

    def _real_start(flow_obj):
        """Find the first non-Flow node by following start_node chain."""
        flow_id = id(flow_obj)
        if flow_id in real_start_cache:
            return real_start_cache[flow_id]

        current = getattr(flow_obj, "start_node", None)
        seen = set()

        while isinstance(current, Flow) and getattr(current, "start_node", None) is not None:
            current_id = id(current)
            if current_id in seen:
                real_start_cache[flow_id] = None
                return None
            seen.add(current_id)
            current = current.start_node

        real_start_cache[flow_id] = current
        return current

    def _is_expanded_flow(obj) -> bool:
        """Check if a Flow should be expanded in the diagram."""
        return (
            isinstance(obj, Flow)
            and getattr(obj, "start_node", None) is not None
            and _real_start(obj) is not None
        )

    def _entry_node_id(obj) -> int:
        """Get the entry node ID for an object (expanded flows use real start)."""
        if _is_expanded_flow(obj):
            real = _real_start(obj)
            if real is not None:
                return id(real)
        return id(obj)

    exit_cache, exit_computing = {}, set()

    def _exit_source_node_ids(obj) -> set:
        """Find all exit node IDs for an object."""
        obj_id = id(obj)

        if not _is_expanded_flow(obj):
            return {obj_id}
        if obj_id in exit_cache:
            return exit_cache[obj_id]
        if obj_id in exit_computing:
            real = _real_start(obj)
            return {id(real)} if real is not None else {obj_id}

        exit_computing.add(obj_id)

        # Find leaf nodes (nodes with no successors)
        start_node = getattr(obj, "start_node", None)
        leaves, seen = set(), set()
        queue = collections.deque([start_node])

        while queue:
            node = queue.popleft()
            if node is None:
                continue

            node_id = id(node)
            if node_id in seen:
                continue

            seen.add(node_id)
            successors = _get_successors(node)

            if successors:
                for action in _sort_keys(successors):
                    next_node = successors.get(action)
                    if next_node is not None:
                        queue.append(next_node)
            else:
                leaves.add(node_id)

        # Resolve leaves (expand if they are flows)
        resolved = set()
        for leaf_id in leaves:
            leaf_obj = obj_by_id.get(leaf_id)
            if leaf_obj is None:
                continue
            if _is_expanded_flow(leaf_obj):
                resolved.update(_exit_source_node_ids(leaf_obj))
            else:
                resolved.add(leaf_id)

        # Fallback: if no resolved exits, use real start
        if not resolved:
            real = _real_start(obj)
            if real is not None:
                resolved.add(id(real))

        exit_cache[obj_id] = resolved or {obj_id}
        exit_computing.remove(obj_id)
        return exit_cache[obj_id]

    # Rewrite edges to connect exits to entries
    render_edges = set()
    for src_id, action, tgt_id in edges:
        src_obj = obj_by_id.get(src_id)
        tgt_obj = obj_by_id.get(tgt_id)
        if src_obj is None or tgt_obj is None:
            continue

        tgt_entry = _entry_node_id(tgt_obj)
        for exit_src_id in _exit_source_node_ids(src_obj):
            render_edges.add((exit_src_id, action, tgt_entry))

    expanded_flow_ids = {obj_id for obj_id in flow_ids if _is_expanded_flow(obj_by_id.get(obj_id))}

    def _get_ancestors(container_flow_id):
        """Yield ancestor flow IDs from innermost to outermost (ending with None)."""
        seen = set()
        current = container_flow_id
        while current is not None and current not in seen:
            seen.add(current)
            yield current
            current = parent_flow_by_flow_id.get(current)
        yield None

    def _edge_container(src_id: int, tgt_id: int):
        """Find the common container for rendering an edge."""
        src_container = container_flow_by_node_id.get(src_id)
        tgt_container = container_flow_by_node_id.get(tgt_id)
        tgt_ancestors = set(_get_ancestors(tgt_container))

        for ancestor in _get_ancestors(src_container):
            if ancestor in tgt_ancestors:
                return ancestor
        return None

    # Group edges by container
    edges_by_container = {}
    for src_id, action, tgt_id in render_edges:
        container = _edge_container(src_id, tgt_id)
        edges_by_container.setdefault(container, []).append((src_id, action, tgt_id))

    # Sort edges within each container
    for container in edges_by_container:
        edges_by_container[container].sort(
            key=lambda e: (
                order_index_by_obj_id[e[0]],
                str(e[1]),
                order_index_by_obj_id[e[2]]
            )
        )

    # ============================================================
    # Step 5: Render Mermaid diagram
    # ============================================================

    lines = ["```mermaid", f"flowchart {direction_u}"]

    # Add start node
    start_target_id = id(flow)
    if _is_expanded_flow(flow):
        real = _real_start(flow)
        if real is not None:
            start_target_id = id(real)
    lines.append(f"  start((Start)) --> {mermaid_id_by_obj_id[start_target_id]}")

    def _node_def(obj_id: int) -> str:
        """Generate Mermaid node definition."""
        obj = obj_by_id[obj_id]
        label = _escape(_label_for(obj))
        return f'{mermaid_id_by_obj_id[obj_id]}["{label}"]'

    def _edge_line(src_id: int, action: str, tgt_id: int) -> str:
        """Generate Mermaid edge line."""
        src_mermaid = mermaid_id_by_obj_id[src_id]
        tgt_mermaid = mermaid_id_by_obj_id[tgt_id]

        if action == "default" and not show_default:
            return f"{src_mermaid} --> {tgt_mermaid}"
        return f"{src_mermaid} -->|{_escape(action, is_edge=True)}| {tgt_mermaid}"

    rendered_flows, rendering_stack = set(), set()

    def _render_flow(flow_id: int, indent: str):
        """Recursively render a flow and its nested flows."""
        if flow_id in rendering_stack:
            return

        rendering_stack.add(flow_id)
        flow_obj = obj_by_id[flow_id]

        subgraph_id = f"subflow_{mermaid_id_by_obj_id[flow_id]}"
        lines.append(f"{indent}subgraph {subgraph_id}[{_escape(_label_for(flow_obj))}]")
        inner_indent = indent + "  "

        body = body_by_flow_id.get(flow_id, set())

        # Find child flows that should be expanded
        child_flow_ids = sorted(
            [
                node_id for node_id in body
                if (
                    isinstance(obj_by_id.get(node_id), Flow)
                    and node_id in expanded_flow_ids
                    and container_flow_by_node_id.get(node_id) == flow_id
                )
            ],
            key=lambda oid: order_index_by_obj_id[oid],
        )

        # Render non-flow nodes directly contained in this flow
        non_flow_nodes = [
            node_id for node_id in body
            if (
                not _is_expanded_flow(obj_by_id.get(node_id))
                and container_flow_by_node_id.get(node_id) == flow_id
            )
        ]
        for node_id in sorted(non_flow_nodes, key=lambda oid: order_index_by_obj_id[oid]):
            lines.append(f"{inner_indent}{_node_def(node_id)}")

        # Recursively render child flows
        for child_flow_id in child_flow_ids:
            _render_flow(child_flow_id, inner_indent)

        # Render edges within this flow
        for src_id, action, tgt_id in edges_by_container.get(flow_id, []):
            lines.append(f"{inner_indent}{_edge_line(src_id, action, tgt_id)}")

        lines.append(f"{indent}end")
        rendered_flows.add(flow_id)
        rendering_stack.remove(flow_id)

    # Render flows
    root_flow_id = id(flow)
    if root_flow_id in expanded_flow_ids:
        _render_flow(root_flow_id, "  ")

    for flow_id in flow_ids:
        if (
            flow_id != root_flow_id
            and flow_id in expanded_flow_ids
            and container_flow_by_node_id.get(flow_id) is None
            and flow_id not in rendered_flows
        ):
            _render_flow(flow_id, "  ")

    # Render orphan nodes (not in any flow)
    for obj_id in visit_order:
        if (
            not _is_expanded_flow(obj_by_id.get(obj_id))
            and container_flow_by_node_id.get(obj_id) is None
        ):
            lines.append(f"  {_node_def(obj_id)}")

    # Render orphan edges
    for src_id, action, tgt_id in edges_by_container.get(None, []):
        lines.append(f"  {_edge_line(src_id, action, tgt_id)}")

    # Add start highlighting
    if highlight_starts:
        highlight_ids = set()
        for flow_id in flow_ids:
            flow_obj = obj_by_id[flow_id]
            real = _real_start(flow_obj)
            if real is not None and id(real) in mermaid_id_by_obj_id:
                highlight_ids.add(id(real))
            else:
                warnings.warn("Flow has no resolvable start_node")

        if highlight_ids:
            lines.append("  classDef pf_true_start stroke:#d33,stroke-width:3px,fill:#fff5f5;")
            for highlight_id in sorted(highlight_ids, key=lambda oid: order_index_by_obj_id[oid]):
                lines.append(f"  class {mermaid_id_by_obj_id[highlight_id]} pf_true_start")

    lines.append("```")
    return "\n".join(lines)
