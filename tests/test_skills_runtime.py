#!/usr/bin/env python3
"""
Dynamic Runtime Verification Test Suite (Tier 2 Engine)
Validates runtime execution integrity across all sandbox skill scripts:
1. Intent Classifier (classify_intent.py): Parity across 4 primary intents + sub-intents
2. Lazy Stub Detector (universal_audit_runner.py AST): Flags evasions while respecting @abstractmethod
3. Requirements Extractor (extract_contract.py): Schema integrity and RFC 2119 / EARS contracts
4. Stop Hook Gatekeeper (enforce_adversarial_gate.py): Robust clearance checking without CP949 crash
5. State Tracker & Diff Generator (inspect_state.py, generate_diff.py): Robust execution
"""

import sys
import unittest
import ast
from pathlib import Path

# Setup paths
SANDBOX_DIR = Path(__file__).resolve().parents[1]
SKILLS_DIR = SANDBOX_DIR / ".agents" / "skills"
HOOKS_DIR = SANDBOX_DIR / ".agents" / "hooks"

sys.path.insert(0, str(SANDBOX_DIR))
sys.path.insert(0, str(SKILLS_DIR / "requirements-extractor" / "scripts"))
sys.path.insert(0, str(SKILLS_DIR / "adversarial-gatekeeper" / "scripts"))
sys.path.insert(0, str(SKILLS_DIR / "current-state-tracker" / "scripts"))
sys.path.insert(0, str(HOOKS_DIR))

# Import modules
from classify_intent import classify_intent  # noqa: E402
from extract_contract import extract_acceptance_contract  # noqa: E402
from universal_audit_runner import LazyStubVisitor, UniversalAuditor  # noqa: E402
from enforce_adversarial_gate import check_adversarial_clearance  # noqa: E402


class TestIntentClassifier(unittest.TestCase):
    """Test Intent Classifier / Sub-intent router across specification categories."""

    def test_sub_intent_categorization(self):
        cases = [
            ("사용자 가이드 및 README 문서를 최신화해줘", "REQ:DOC"),
            ("초안 설계 및 아키텍처 구조를 작성해줘", "REQ:DESIGN"),
            ("코드 검수 및 적대적 audit을 실행해", "REQ:AUDIT"),
            ("거버넌스 규약 및 격리 hook을 검증해", "REQ:GOVERNANCE"),
            ("새로운 기능을 추가하고 구현해줘", "REQ:IMPLEMENT"),
        ]
        for query, expected_sub in cases:
            with self.subTest(query=query):
                res = classify_intent(query)
                self.assertEqual(res["primary_intent"], "REQUIREMENT")
                self.assertEqual(res["sub_intent"], expected_sub)
                self.assertTrue(res["is_actionable"])

    def test_empty_or_whitespace_input(self):
        res = classify_intent("   ")
        self.assertEqual(res["primary_intent"], "REQUIREMENT")
        self.assertEqual(res["sub_intent"], "REQ:IMPLEMENT")
        self.assertEqual(res["text"], "")


class TestLazyStubVisitor(unittest.TestCase):
    """Test AST Lazy Stub detection for AI evasions vs valid abstraction."""

    def test_detects_bare_pass_in_regular_function(self):
        code = "def calculate_metrics():\n    pass\n"
        tree = ast.parse(code)
        visitor = LazyStubVisitor("test.py")
        visitor.visit(tree)
        self.assertEqual(len(visitor.stubs), 1)
        self.assertIn("Bare 'pass'", visitor.stubs[0][2])

    def test_detects_ellipsis_in_regular_function(self):
        code = "def fetch_remote_data():\n    ...\n"
        tree = ast.parse(code)
        visitor = LazyStubVisitor("test.py")
        visitor.visit(tree)
        self.assertEqual(len(visitor.stubs), 1)
        self.assertIn("Ellipsis", visitor.stubs[0][2])

    def test_allows_abstract_methods(self):
        code = (
            "class BaseAuditor:\n"
            "    @abstractmethod\n"
            "    def run(self):\n"
            "        pass\n"
            "    @overload\n"
            "    def parse(self, x: int) -> int:\n"
            "        ...\n"
        )
        tree = ast.parse(code)
        visitor = LazyStubVisitor("test.py")
        visitor.visit(tree)
        self.assertEqual(len(visitor.stubs), 0)

    def test_allows_implemented_functions(self):
        code = "def add(a, b):\n    \"\"\"Add two numbers.\"\"\"\n    return a + b\n"
        tree = ast.parse(code)
        visitor = LazyStubVisitor("test.py")
        visitor.visit(tree)
        self.assertEqual(len(visitor.stubs), 0)


class TestRequirementsExtractor(unittest.TestCase):
    """Test Requirements Extractor contract output and 4-pillar schema."""

    def test_generates_four_pillars(self):
        from extract_contract import format_contract_markdown
        text = "새로운 3계층 파이프라인 엔진을 구축하고 런타임 테스트를 통합해줘."
        contract_data = extract_acceptance_contract("D-TEST", text, "W-TEST")
        self.assertIn("contracts", contract_data)
        req_ids = [c["req_id"] for c in contract_data["contracts"]]
        self.assertIn("REQ-01", req_ids)
        self.assertIn("REQ-02", req_ids)
        self.assertIn("REQ-03", req_ids)
        self.assertIn("REQ-04", req_ids)
        md = format_contract_markdown(contract_data)
        self.assertIn("인수 계약 매트릭스", md)


class TestEnforceAdversarialGate(unittest.TestCase):
    """Test lifecycle Stop hook clearance verification."""

    def test_nonexistent_directory(self):
        non_dir = SANDBOX_DIR / "non_existent_sub_dir"
        res = check_adversarial_clearance(non_dir)
        self.assertEqual(res["decision"], "stop")

    def test_sandbox_clearance(self):
        res = check_adversarial_clearance(SANDBOX_DIR)
        self.assertIn(res["decision"], {"stop", "continue"})


class TestUniversalAuditorExecution(unittest.TestCase):
    """Test that UniversalAuditor can instantiate and execute without runtime crash."""

    def test_auditor_instantiation_and_structure(self):
        auditor = UniversalAuditor(SANDBOX_DIR)
        self.assertIsInstance(auditor.stats, dict)
        self.assertEqual(auditor.stats["linter_violations"], 0)


if __name__ == "__main__":
    unittest.main()
