---
layout: default
title: "Viz and Debug"
parent: "Utility Function"
nav_order: 3
---

# Visualization and Debugging

PocketFlow now includes built-in Mermaid export via `Flow.visualize(...)`.

- For the built-in API guide, see [Flow Visualize](./flow_visualize).
- This page keeps complementary debugging and extended visualization references.

## 1. Extended Visualization (D3.js)

The built-in API is ideal for quick graph inspection in markdown docs. If you need interactive visualization (dragging, group boundaries, custom layout), use the D3 cookbook implementation:

- [pocketflow-visualization cookbook](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-visualization)

## 2. Call Stack Debugging

To inspect runtime call stacks during execution, you can inspect Python frames:

```python
import inspect

def get_node_call_stack():
    stack = inspect.stack()
    node_names = []
    seen_ids = set()
    for frame_info in stack[1:]:
        local_vars = frame_info.frame.f_locals
        if 'self' in local_vars:
            caller_self = local_vars['self']
            if isinstance(caller_self, BaseNode) and id(caller_self) not in seen_ids:
                seen_ids.add(id(caller_self))
                node_names.append(type(caller_self).__name__)
    return node_names
```

Example usage:

```python
class EvaluateModelNode(Node):
    def prep(self, shared):
        stack = get_node_call_stack()
        print("Call stack:", stack)
```

For a more complete tracing workflow, see:

- [pocketflow-tracing cookbook](https://github.com/The-Pocket/PocketFlow/tree/main/cookbook/pocketflow-tracing)
