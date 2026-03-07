# tests/test_visualize_api.py
import re
import sys
import unittest
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from pocketflow import Flow, Node


class _N(Node):
    pass


class TestFlowVisualize(unittest.TestCase):
    @staticmethod
    def _parse_labels(mermaid: str) -> dict:
        labels = {}
        for line in mermaid.splitlines():
            m = re.match(r'^\s*(n\d+)\["((?:\\"|[^"])*)"\]$', line)
            if m:
                labels[m.group(2).replace('\\"', '"')] = m.group(1)
        return labels

    @staticmethod
    def _parse_edges(mermaid: str) -> set:
        edges = set()
        for line in mermaid.splitlines():
            m = re.match(r'^\s*(n\d+)\s*-->\|([^|]+)\|\s*(n\d+)\s*$', line)
            if m:
                edges.add((m.group(1), m.group(2), m.group(3)))
                continue
            m = re.match(r'^\s*(n\d+)\s*-->\s*(n\d+)\s*$', line)
            if m:
                edges.add((m.group(1), None, m.group(2)))
        return edges

    def test_output_is_fenced_mermaid_with_start_edge(self):
        a, b = _N(), _N()
        a >> b
        flow = Flow(start=a)

        mermaid = flow.visualize(namespace=locals())

        self.assertTrue(mermaid.startswith("```mermaid\nflowchart LR\n"))
        self.assertTrue(mermaid.endswith("\n```"))
        self.assertIn("start((Start)) -->", mermaid)

    def test_show_default_controls_default_edge_label(self):
        a, b = _N(), _N()
        a >> b
        flow = Flow(start=a)

        m_default_hidden = flow.visualize(namespace=locals(), show_default=False)
        m_default_visible = flow.visualize(namespace=locals(), show_default=True)

        self.assertNotIn("|default|", m_default_hidden)
        self.assertIn("|default|", m_default_visible)

    def test_branch_action_labels_are_rendered(self):
        check, yes_node, no_node = _N(), _N(), _N()
        check - "yes" >> yes_node
        check - "no" >> no_node
        flow = Flow(start=check)

        mermaid = flow.visualize(namespace=locals())

        self.assertIn("|yes|", mermaid)
        self.assertIn("|no|", mermaid)

    def test_invalid_direction_raises(self):
        flow = Flow(start=_N())
        with self.assertRaises(ValueError):
            flow.visualize(namespace=locals(), direction="XX")

    def test_invalid_max_nodes_raises(self):
        flow = Flow(start=_N())
        with self.assertRaises(ValueError):
            flow.visualize(namespace=locals(), max_nodes=0)
        with self.assertRaises(ValueError):
            flow.visualize(namespace=locals(), max_nodes=-1)
        with self.assertRaises(ValueError):
            flow.visualize(namespace=locals(), max_nodes=1.5)

    def test_max_nodes_exceeded_raises_runtime_error(self):
        a, b = _N(), _N()
        a >> b
        flow = Flow(start=a)

        with self.assertRaises(RuntimeError):
            flow.visualize(namespace=locals(), max_nodes=1)

    def test_nested_flow_subgraph_and_successor_rewrite(self):
        inner_a, inner_b, tail = _N(), _N(), _N()
        inner_a >> inner_b
        inner = Flow(start=inner_a)
        inner >> tail
        outer = Flow(start=inner)

        mermaid = outer.visualize(namespace=locals(), highlight_starts=False)
        labels = self._parse_labels(mermaid)
        edges = self._parse_edges(mermaid)

        self.assertIn("subgraph", mermaid)
        self.assertIn("[inner]", mermaid)

        inner_b_id = labels["inner_b"]
        tail_id = labels["tail"]
        self.assertIn((inner_b_id, None, tail_id), edges)

    def test_cycle_is_stable_and_deduplicated(self):
        a, b = _N(), _N()
        a >> b
        b >> a
        flow = Flow(start=a)

        mermaid = flow.visualize(namespace=locals(), highlight_starts=False)
        labels = self._parse_labels(mermaid)
        edges = self._parse_edges(mermaid)

        a_id = labels["a"]
        b_id = labels["b"]
        self.assertIn((a_id, None, b_id), edges)
        self.assertIn((b_id, None, a_id), edges)

    def test_missing_namespace_warns_and_falls_back_to_class_labels(self):
        class Alpha(Node):
            pass

        node = Alpha()
        flow = Flow(start=node)

        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            mermaid = flow.visualize(namespace=None)

        self.assertTrue(any("Missing or invalid namespace" in str(w.message) for w in ws))
        self.assertIn('"Alpha"', mermaid)

    def test_multiple_variable_names_warning_and_sorted_choice(self):
        class Alpha(Node):
            pass

        x = y = Alpha()
        flow = Flow(start=x)

        with warnings.catch_warnings(record=True) as ws:
            warnings.simplefilter("always")
            mermaid = flow.visualize(namespace=locals())

        self.assertTrue(any("Multiple variable names" in str(w.message) for w in ws))
        self.assertIn('"x"', mermaid)
        self.assertNotIn('"y"', mermaid)


if __name__ == "__main__":
    unittest.main()
