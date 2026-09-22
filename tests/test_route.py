import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "jev_route", ROOT / "skills/jev-subagent-router/scripts/route.py"
)
route = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(route)


def task(platform="codex", nested=False):
    return {
        "platform": platform,
        "nested_delegation": nested,
        "task": {"objective": "Trace a cancellation race.", "acceptance": "Return a reproducible proof."},
        "available": {model: spec["efforts"][:] for model, spec in route.CATALOG[platform].items()},
    }


def answer(payload):
    candidates = list(payload["questions"]["route"]["criteria"])
    winner = candidates[-1]
    return {
        "model": "jev-1.13.0",
        "usage": {"input_tokens": 100, "output_tokens": 20},
        "answers": {"route": {
            "type": "choice", "choice": winner, "confidence": 0.9,
            "probabilities": {candidate: float(candidate == winner) for candidate in candidates},
        }},
    }


class RouterTests(unittest.TestCase):
    def test_jev_selects_one_complete_model_effort_pair(self):
        for platform, count in [("codex", 23), ("claude-code", 19)]:
            payload = route.build_request(task(platform, True))
            self.assertEqual(set(payload["questions"]), {"route"})
            question = payload["questions"]["route"]
            self.assertEqual(question["type"], "choice")
            self.assertEqual(len(question["criteria"]), count)
            for key, value in question["criteria"].items():
                self.assertEqual(key, value["model"] + "@" + value["effort"])
            if platform == "claude-code":
                self.assertIn("claude-opus-5@low", question["criteria"])
                self.assertIn("claude-opus-5@high", question["criteria"])
                self.assertIn("claude-opus-4-6@high", question["criteria"])
                self.assertNotIn("claude-opus-4-6@xhigh", question["criteria"])

    def test_every_candidate_carries_price_and_platform_effort_semantics(self):
        for platform in route.CATALOG:
            criteria = route.build_request(task(platform, True))["questions"]["route"]["criteria"]
            for key, value in criteria.items():
                with self.subTest(candidate=key):
                    self.assertRegex(value["list_price"], r"\$\d")
                    self.assertEqual(value["effort_profile"], route.EFFORTS[platform][value["effort"]])
                    self.assertTrue(value["model_profile"].strip())
        self.assertNotEqual(route.EFFORTS["codex"]["medium"], route.EFFORTS["claude-code"]["medium"])
        self.assertNotIn("xhigh", route.CATALOG["claude-code"]["claude-opus-4-6"]["efforts"])

    def test_nested_delegation_filters_ultra(self):
        plain = route.build_request(task())["questions"]["route"]["criteria"]
        nested = route.build_request(task(nested=True))["questions"]["route"]["criteria"]
        self.assertFalse(any(key.endswith("@ultra") for key in plain))
        self.assertEqual(set(nested) - set(plain), {
            "gpt-5.6-sol@ultra", "gpt-5.6-terra@ultra", "gpt-6-astra@ultra",
        })

    def test_every_pair_maps_to_native_fields(self):
        for platform, models in route.CATALOG.items():
            for model, spec in models.items():
                for effort in spec["efforts"]:
                    with self.subTest(model=model, effort=effort):
                        data = task(platform, True)
                        data["available"] = {model: [effort]}
                        payload = route.build_request(data)
                        result = route.parse_response(answer(payload), payload)
                        self.assertEqual((result["model"], result["effort"]), (model, effort))
                        if platform == "codex":
                            self.assertEqual(result["spawn_parameters"], {
                                "model": model, "reasoning_effort": effort, "fork_turns": "none",
                            })
                        else:
                            self.assertEqual(result["agent_frontmatter"], {"model": model, "effort": effort})
                            parameters = result["agent_parameters"]
                            self.assertEqual(set(parameters), {"subagent_type"})
                            definition = ROOT / "skills/jev-subagent-router/assets/claude-agents" / (parameters["subagent_type"] + ".md")
                            frontmatter = dict(
                                line.split(": ", 1) for line in definition.read_text().split("---", 2)[1].strip().splitlines()
                            )
                            self.assertEqual(frontmatter["name"], parameters["subagent_type"])
                            self.assertEqual(frontmatter["model"], model)
                            self.assertEqual(frontmatter["effort"], effort)

    def test_catalog_uses_exact_model_ids(self):
        self.assertEqual(set(route.CATALOG["codex"]), {
            "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna", "gpt-6-astra",
        })
        self.assertEqual(set(route.CATALOG["claude-code"]), {
            "claude-opus-5", "claude-opus-4-6", "claude-sonnet-5", "claude-fable-5-1",
        })
        for platform, alias in [("codex", "gpt-5.6"), ("claude-code", "opus"), ("claude-code", "opus-5")]:
            data = task(platform)
            data["available"] = {alias: ["high"]}
            with self.assertRaises(ValueError):
                route.build_request(data)

    def test_all_claude_templates_are_reachable(self):
        expected = {
            f"jev-{model}-{effort}.md"
            for model, spec in route.CATALOG["claude-code"].items()
            for effort in spec["efforts"]
        }
        directory = ROOT / "skills/jev-subagent-router/assets/claude-agents"
        self.assertEqual({p.name for p in directory.glob("*.md")}, expected)

    def test_invalid_task_or_capabilities(self):
        cases = [
            {"platform": []}, {"available": {}}, {"task": {}},
            {"available": {"gpt-5.6-luna": ["ultra"]}},
            {"available": {"claude-opus-5": ["high"]}},
            {"available": {"gpt-5.6-sol": ["high", "high"]}},
            {"nested_delegation": "true"},
            {"task": {"objective": "x", "value": float("nan")}},
        ]
        for change in cases:
            with self.subTest(change=change), self.assertRaises(ValueError):
                route.build_request({**task(), **change})
        data = task("claude-code")
        data["available"] = {"claude-opus-4-6": ["xhigh"]}
        with self.assertRaises(ValueError):
            route.build_request(data)

    def test_invalid_provider_answers(self):
        payload = route.build_request(task())
        valid = answer(payload)
        winner = valid["answers"]["route"]["choice"]
        cases = [
            {"choice": "unlisted@high"}, {"type": "score"},
            {"confidence": float("nan")}, {"confidence": True},
            {"probabilities": {winner: 1.0}},
            {"probabilities": {key: 0 for key in payload["questions"]["route"]["criteria"]}},
            {"choice": next(iter(payload["questions"]["route"]["criteria"]))},
        ]
        for change in cases:
            bad = copy.deepcopy(valid)
            bad["answers"]["route"].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                route.parse_response(bad, payload)

    def test_rounded_probabilities_are_accepted_but_wrong_totals_are_not(self):
        payload = route.build_request(task("codex", True))
        keys = list(payload["questions"]["route"]["criteria"])
        rounded = answer(payload)
        # 20 个候选各四舍五入到两位小数，总和 0.99 是 Jev 的真实返回形态。
        rounded["answers"]["route"]["probabilities"] = {k: 0.01 for k in keys}
        rounded["answers"]["route"]["probabilities"][keys[-1]] = 0.99 - 0.01 * (len(keys) - 1)
        rounded["answers"]["route"]["choice"] = keys[-1]
        self.assertEqual(route.parse_response(rounded, payload)["model"], route.CATALOG["codex"][keys[-1].split("@")[0]] and keys[-1].split("@")[0])
        broken = answer(payload)
        broken["answers"]["route"]["probabilities"] = {k: 0.0 for k in keys}
        broken["answers"]["route"]["probabilities"][keys[-1]] = 0.8
        with self.assertRaises(ValueError):
            route.parse_response(broken, payload)

    def test_request_through_cli_to_native_configuration(self):
        for platform in route.CATALOG:
            payload = route.build_request(task(platform))
            conn = MagicMock()
            conn.getresponse.return_value.status = 200
            conn.getresponse.return_value.read.return_value = json.dumps(answer(payload)).encode()
            out = io.StringIO()
            with patch.object(route.http.client, "HTTPSConnection", return_value=conn) as factory:
                with patch.dict(os.environ, {"JEV_API_KEY": "synthetic-test-key"}):
                    with patch.object(route.sys, "argv", ["route.py"]):
                        with patch.object(route.sys, "stdin", io.StringIO(json.dumps(task(platform)))):
                            with redirect_stdout(out):
                                self.assertEqual(route.main(), 0)
            factory.assert_called_once_with("api.typesafe.ai", timeout=30)
            args = conn.request.call_args.args
            self.assertEqual(args[:2], ("POST", "/v1/systemone"))
            self.assertEqual(json.loads(args[2]), payload)
            self.assertEqual(args[3]["Authorization"], "Bearer synthetic-test-key")
            self.assertNotIn("synthetic-test-key", out.getvalue())
            self.assertEqual(json.loads(out.getvalue())["platform"], platform)
            conn.close.assert_called_once()

    def test_missing_key_never_connects(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(route.sys, "argv", ["route.py"]):
            with patch.object(route.http.client, "HTTPSConnection") as factory, redirect_stderr(io.StringIO()):
                self.assertEqual(route.main(), 2)
                factory.assert_not_called()

    def test_http_errors_never_follow_redirect_or_read_error_body(self):
        for status in [302, 401, 422, 429, 529]:
            conn = MagicMock()
            conn.getresponse.return_value.status = status
            with patch.object(route.http.client, "HTTPSConnection", return_value=conn):
                with self.assertRaisesRegex(ValueError, "HTTP " + str(status)):
                    route.evaluate(route.build_request(task()), "synthetic-test-key")
            conn.request.assert_called_once()
            conn.getresponse.return_value.read.assert_not_called()
            conn.close.assert_called_once()

    def test_dry_run_needs_no_key_or_network(self):
        out = io.StringIO()
        with patch.dict(os.environ, {}, clear=True), patch.object(route.sys, "argv", ["route.py", "--dry-run"]):
            with patch.object(route.sys, "stdin", io.StringIO(json.dumps(task()))):
                with patch.object(route.http.client, "HTTPSConnection") as factory, redirect_stdout(out):
                    self.assertEqual(route.main(), 0)
                    factory.assert_not_called()
        self.assertEqual(json.loads(out.getvalue())["model"], "jev-latest")


if __name__ == "__main__":
    unittest.main()
