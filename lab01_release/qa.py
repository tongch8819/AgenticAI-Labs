"""Offline Lab 1 checks. Run: python lab01_release/qa.py

Uses a recording stand-in for AutoGen: no dependencies, keys, or API calls.
Configuration checks do NOT simulate conversations or verify LLM accuracy.
"""

import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent


class RecordingAgent:
    """Record setup only; deliberately do not pretend to execute chats."""

    agents = {}
    chats = []

    def __init__(self, name, **kwargs):
        self.name = name
        self.options = kwargs
        self.llm_tools = {}
        self.execution_tools = {}
        self.agents[name] = self

    def register_for_llm(self, name, **kwargs):
        def register(function):
            self.llm_tools[name] = function
            return function
        return register

    def register_for_execution(self, name, **kwargs):
        def register(function):
            self.execution_tools[name] = function
            return function
        return register

    def initiate_chats(self, chats):
        self.chats.extend(chats)
        return []


def load_lab():
    fake_autogen = types.ModuleType("autogen")
    fake_autogen.ConversableAgent = RecordingAgent
    spec = importlib.util.spec_from_file_location("lab_under_test", ROOT / "main.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"autogen": fake_autogen}):
        spec.loader.exec_module(module)
    return module


lab = load_lab()


class FetchChecks(unittest.TestCase):
    def test_exact_reviews_case_whitespace_and_periods(self):
        """A controlled file detects missing, changed, or unrelated reviews."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "restaurant-data.txt").write_text(
                "Subway. Food was good. Service was amazing.\n"
                "Other. Food was awful.\n\n"
                "Subway. Food was average. Service was bad.\n",
                encoding="utf-8",
            )
            expected = [
                "Food was good. Service was amazing.",
                "Food was average. Service was bad.",
            ]
            with patch.object(lab, "__file__", str(path / "main.py")):
                for query in ["Subway", "subway", "  SUBWAY  "]:
                    with self.subTest(query=query):
                        self.assertEqual(lab.fetch_restaurant_data(query), {query: expected})

    def test_real_dataset_all_restaurants(self):
        expected = {}
        for line in (ROOT / "restaurant-data.txt").read_text(encoding="utf-8").splitlines():
            if line.strip():
                name, separator, review = line.strip().partition(". ")
                self.assertTrue(separator, "Dataset line has no restaurant separator")
                expected.setdefault(name, []).append(review.strip())
        self.assertTrue(expected, "Dataset is empty")
        for name, reviews in expected.items():
            with self.subTest(restaurant=name):
                self.assertEqual(lab.fetch_restaurant_data(name), {name: reviews})


class ScoreChecks(unittest.TestCase):
    def score(self, food, service):
        with contextlib.redirect_stdout(io.StringIO()):
            result = lab.calculate_overall_score("Example", food, service)
        self.assertEqual(set(result), {"Example"})
        self.assertIsInstance(result["Example"], (int, float))
        return result["Example"]

    def test_known_answers(self):
        for food, service, expected in [
            ([5], [5], 10.0),
            ([1], [1], 0.894),
            ([4], [4], 7.155),
            # The starter comment says 5.048, but its formula gives 5.045.
            ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5], 5.045),
        ]:
            with self.subTest(food=food, service=service):
                self.assertAlmostEqual(self.score(food, service), expected, delta=0.001)

    def test_food_has_greater_weight(self):
        self.assertGreater(self.score([5], [1]), self.score([1], [5]))

    def test_duplicating_reviews_preserves_average(self):
        self.assertEqual(self.score([2, 5], [4, 1]), self.score([2, 5] * 3, [4, 1] * 3))

    def test_printed_score_has_three_decimal_places(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            lab.calculate_overall_score("Example", [5], [5])
        self.assertRegex(
            output.getvalue(), r"\b10\.000\b",
            "The public tests need 10.000; round(..., 3) alone prints 10.0. Use :.3f.",
        )


class WorkflowConfigurationChecks(unittest.TestCase):
    def setUp(self):
        RecordingAgent.agents.clear()
        RecordingAgent.chats.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            lab.main("How good is Subway?")

    def test_stage_order_and_query(self):
        self.assertEqual(
            [chat["recipient"].name for chat in RecordingAgent.chats],
            ["data_fetch_agent", "review_analyzer_agent", "scoring_agent"],
        )
        self.assertEqual(RecordingAgent.chats[0]["message"], "How good is Subway?")

    def test_tools_have_requester_and_executor(self):
        agents = RecordingAgent.agents
        for agent, tool in [
            ("data_fetch_agent", "fetch_restaurant_data"),
            ("scoring_agent", "calculate_overall_score"),
        ]:
            with self.subTest(tool=tool):
                self.assertIs(agents[agent].llm_tools.get(tool), getattr(lab, tool))
                self.assertIs(agents["entrypoint_agent"].execution_tools.get(tool), getattr(lab, tool))

    def test_tool_chats_allow_execution_turn(self):
        for chat in RecordingAgent.chats:
            if chat["recipient"].name in ("data_fetch_agent", "scoring_agent"):
                with self.subTest(agent=chat["recipient"].name):
                    limit = chat.get("max_turns")
                    self.assertTrue(
                        limit is None or limit >= 2,
                        "This sequential chat needs another turn after the tool suggestion.",
                    )


if __name__ == "__main__":
    print("Offline QA: real Python functions + recorded configuration; no LLM calls.", flush=True)
    unittest.main(verbosity=2)
