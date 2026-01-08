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

    def _sort_keys(d):
        try:
            return sorted(d)
        except Exception:
            return sorted(d, key=lambda x: str(x))

    def _escape(s: str, is_edge: bool = False) -> str:
        s = str(s).replace("\\", "\\\\")
        return s.replace("|", "\\|") if is_edge else s.replace('"', '\\"')

    direction_u = (direction or "LR").upper()
    if direction_u not in {"LR", "RL", "TB", "TD", "BT"}:
        raise ValueError("direction must be one of LR/RL/TB/TD/BT")
    if not isinstance(max_nodes, int) or max_nodes <= 0:
        raise ValueError("max_nodes must be a positive integer")

    if not namespace:
        warnings.warn("Missing namespace; falling back to class-name labels")
        namespace = {}
    if not isinstance(namespace, dict):
        warnings.warn("Invalid namespace type; falling back to class-name labels")
        namespace = {}

    names_by_obj_id = {id(v): [k] for k, v in namespace.items() if isinstance(k, str) and hasattr(v, "successors")}

    warned_multi_names, warned_missing_names = set(), set()
    unnamed_counter_by_class, label_cache = {}, {}

    def _label_for(obj) -> str:
        oid = id(obj)
        if oid in label_cache:
            return label_cache[oid]

        cls = obj.__class__.__name__
        names = names_by_obj_id.get(oid) or []
        if names:
            if len(names) > 1 and oid not in warned_multi_names:
                warned_multi_names.add(oid)
                warnings.warn(f"Multiple variable names for the same node/flow: {sorted(names)}")
            label = sorted(names)[0]
        else:
            if oid not in warned_missing_names:
                warned_missing_names.add(oid)
                warnings.warn(f"Missing variable name for object {cls}")
            n = unnamed_counter_by_class.get(cls, 0) + 1
            unnamed_counter_by_class[cls] = n
            label = cls if n == 1 else f"{cls}#{n}"

        label_cache[oid] = label
        return label

    # --- 1) Discover global nodes/edges ---
    obj_by_id, visit_order, visited = {}, [], set()
    edges = set()
    queue = collections.deque([flow])
    while queue:
        curr = queue.popleft()
        if curr is None:
            continue
        cid = id(curr)
        if cid in visited:
            continue
        visited.add(cid)
        obj_by_id[cid] = curr
        visit_order.append(cid)
        if len(visit_order) > max_nodes:
            raise RuntimeError(f"max_nodes exceeded: {max_nodes}")

        if isinstance(curr, Flow) and (sn := getattr(curr, "start_node", None)):
            queue.append(sn)

        succ = getattr(curr, "successors", None) or {}
        for act in _sort_keys(succ):
            if (nxt := succ.get(act)) is not None:
                edges.add((cid, str(act), id(nxt)))
                queue.append(nxt)

    order_index_by_obj_id = {oid: i for i, oid in enumerate(visit_order)}
    mermaid_id_by_obj_id = {oid: f"n{i}" for oid, i in order_index_by_obj_id.items()}

    # --- 2) Compute per-flow body nodes ---
    flow_ids = [oid for oid in visit_order if isinstance(obj_by_id.get(oid), Flow)]
    body_by_flow_id = {}
    for fid in flow_ids:
        f = obj_by_id[fid]
        if (start := getattr(f, "start_node", None)) is None:
            body_by_flow_id[fid] = set()
            continue

        body, q, seen = set(), collections.deque([start]), set()
        while q:
            n = q.popleft()
            if n is None or (nid := id(n)) in seen:
                continue
            seen.add(nid)
            body.add(nid)
            for act in _sort_keys(getattr(n, "successors", None) or {}):
                if (nxt := getattr(n, "successors", {}).get(act)) is not None:
                    q.append(nxt)
        body_by_flow_id[fid] = body

    # --- 3) Choose containment ---
    container_flow_by_node_id = {}
    for fid in flow_ids:
        for nid in body_by_flow_id.get(fid, set()):
            container_flow_by_node_id.setdefault(nid, fid)

    parent_flow_by_flow_id = {
        fid: container_flow_by_node_id[fid]
        for fid in flow_ids
        if (parent := container_flow_by_node_id.get(fid)) is not None
        and parent != fid
        and isinstance(obj_by_id.get(parent), Flow)
    }

    # --- 4) Rewrite edges for expanded flows ---
    real_start_cache = {}

    def _real_start(flow_obj):
        fid = id(flow_obj)
        if fid in real_start_cache:
            return real_start_cache[fid]

        x = getattr(flow_obj, "start_node", None)
        seen = set()
        while isinstance(x, Flow) and getattr(x, "start_node", None) is not None:
            xid = id(x)
            if xid in seen:
                real_start_cache[fid] = None
                return None
            seen.add(xid)
            x = x.start_node
        real_start_cache[fid] = x
        return x

    def _is_expanded_flow(obj) -> bool:
        return isinstance(obj, Flow) and getattr(obj, "start_node", None) is not None and _real_start(obj) is not None

    def _entry_oid(obj) -> int:
        if _is_expanded_flow(obj) and (rs := _real_start(obj)) is not None:
            return id(rs)
        return id(obj)

    exit_cache, exit_computing = {}, set()

    def _exit_source_oids(obj) -> set:
        oid = id(obj)
        if not _is_expanded_flow(obj):
            return {oid}
        if oid in exit_cache:
            return exit_cache[oid]
        if oid in exit_computing and (rs := _real_start(obj)) is not None:
            return {id(rs)}
        exit_computing.add(oid)

        start = getattr(obj, "start_node", None)
        leaves, seen = set(), set()
        q = collections.deque([start])
        while q:
            n = q.popleft()
            if n is None or (nid := id(n)) in seen:
                continue
            seen.add(nid)
            succ = getattr(n, "successors", None) or {}
            if succ:
                for act in _sort_keys(succ):
                    if (nxt := succ.get(act)) is not None:
                        q.append(nxt)
            else:
                leaves.add(nid)

        resolved = set()
        for lid in leaves:
            if (leaf_obj := obj_by_id.get(lid)) is None:
                continue
            if _is_expanded_flow(leaf_obj):
                resolved |= _exit_source_oids(leaf_obj)
            else:
                resolved.add(lid)

        if not resolved and (rs := _real_start(obj)) is not None:
            resolved.add(id(rs))

        exit_cache[oid] = resolved or {oid}
        exit_computing.remove(oid)
        return exit_cache[oid]

    render_edges = set()
    for src_oid, act, tgt_oid in edges:
        src_obj = obj_by_id.get(src_oid)
        tgt_obj = obj_by_id.get(tgt_oid)
        if src_obj is None or tgt_obj is None:
            continue
        tgt_entry = _entry_oid(tgt_obj)
        for s_oid in _exit_source_oids(src_obj):
            render_edges.add((s_oid, act, tgt_entry))

    expanded_flow_ids = {oid for oid in flow_ids if _is_expanded_flow(obj_by_id.get(oid))}

    def _edge_container(src_oid: int, tgt_oid: int):
        def _ancestors(container_fid):
            seen = set()
            while container_fid is not None and container_fid not in seen:
                seen.add(container_fid)
                yield container_fid
                container_fid = parent_flow_by_flow_id.get(container_fid)
            yield None

        src_container = container_flow_by_node_id.get(src_oid)
        tgt_container = container_flow_by_node_id.get(tgt_oid)
        tgt_anc = set(_ancestors(tgt_container))
        for c in _ancestors(src_container):
            if c in tgt_anc:
                return c
        return None

    edges_by_container = {}
    for src_oid, act, tgt_oid in render_edges:
        edges_by_container.setdefault(_edge_container(src_oid, tgt_oid), []).append((src_oid, act, tgt_oid))
    for c in list(edges_by_container):
        edges_by_container[c].sort(key=lambda e: (order_index_by_obj_id[e[0]], str(e[1]), order_index_by_obj_id[e[2]]))

    # --- 5) Render Mermaid ---
    lines = ["```mermaid", f"flowchart {direction_u}"]

    start_target_oid = id(flow)
    if _is_expanded_flow(flow) and (rs := _real_start(flow)) is not None:
        start_target_oid = id(rs)
    lines.append(f"  start((Start)) --> {mermaid_id_by_obj_id[start_target_oid]}")

    def _node_def(oid: int) -> str:
        return f'{mermaid_id_by_obj_id[oid]}["{_escape(_label_for(obj_by_id[oid]))}"]'

    def _edge_line(src_oid: int, act: str, tgt_oid: int) -> str:
        s, t = mermaid_id_by_obj_id[src_oid], mermaid_id_by_obj_id[tgt_oid]
        if act == "default" and not show_default:
            return f"{s} --> {t}"
        return f"{s} -->|{_escape(act, is_edge=True)}| {t}"

    rendered_flows, rendering_stack = set(), set()

    def _render_flow(fid: int, indent: str):
        if fid in rendering_stack:
            return
        rendering_stack.add(fid)

        f = obj_by_id[fid]
        sub_id = f"subflow_{mermaid_id_by_obj_id[fid]}"
        lines.append(f"{indent}subgraph {sub_id}[{_escape(_label_for(f))}]")
        inner_indent = indent + "  "

        body = body_by_flow_id.get(fid, set())
        child_flow_ids = sorted(
            [nid for nid in body if isinstance(obj_by_id.get(nid), Flow) and nid in expanded_flow_ids and container_flow_by_node_id.get(nid) == fid],
            key=lambda oid: order_index_by_obj_id[oid],
        )

        for nid in sorted([nid for nid in body if not _is_expanded_flow(obj_by_id.get(nid)) and container_flow_by_node_id.get(nid) == fid], key=lambda oid: order_index_by_obj_id[oid]):
            lines.append(f"{inner_indent}{_node_def(nid)}")

        for child_fid in child_flow_ids:
            _render_flow(child_fid, inner_indent)

        for src_oid, act, tgt_oid in edges_by_container.get(fid, []):
            lines.append(f"{inner_indent}{_edge_line(src_oid, act, tgt_oid)}")

        lines.append(f"{indent}end")
        rendered_flows.add(fid)
        rendering_stack.remove(fid)

    root_fid = id(flow)
    if root_fid in expanded_flow_ids:
        _render_flow(root_fid, "  ")
    for fid in flow_ids:
        if fid != root_fid and fid in expanded_flow_ids and container_flow_by_node_id.get(fid) is None and fid not in rendered_flows:
            _render_flow(fid, "  ")

    for oid in visit_order:
        if not _is_expanded_flow(obj_by_id.get(oid)) and container_flow_by_node_id.get(oid) is None:
            lines.append(f"  {_node_def(oid)}")

    for src_oid, act, tgt_oid in edges_by_container.get(None, []):
        lines.append(f"  {_edge_line(src_oid, act, tgt_oid)}")

    if highlight_starts:
        highlight_ids = set()
        for fid in flow_ids:
            f = obj_by_id[fid]
            if (rs := _real_start(f)) is not None and id(rs) in mermaid_id_by_obj_id:
                highlight_ids.add(id(rs))
            else:
                warnings.warn("Flow has no resolvable start_node")

        if highlight_ids:
            lines.append("  classDef pf_true_start stroke:#d33,stroke-width:3px,fill:#fff5f5;")
            for rid in sorted(highlight_ids, key=lambda oid: order_index_by_obj_id[oid]):
                lines.append(f"  class {mermaid_id_by_obj_id[rid]} pf_true_start")

    lines.append("```")
    return "\n".join(lines)
