import unittest

from tradingagents.graph.analyst_execution import CRYPTO_DEFAULTS, build_analyst_execution_plan


class CryptoV1ArchitectureTests(unittest.TestCase):
    def test_crypto_default_team_contains_only_crypto_analysts(self):
        plan = build_analyst_execution_plan(CRYPTO_DEFAULTS)
        self.assertEqual([spec.key for spec in plan.specs], list(CRYPTO_DEFAULTS))
        self.assertNotIn("fundamentals", [spec.key for spec in plan.specs])

    def test_legacy_default_is_migrated_to_crypto_team(self):
        plan = build_analyst_execution_plan(("market", "social", "news", "fundamentals"))
        self.assertEqual([spec.key for spec in plan.specs], list(CRYPTO_DEFAULTS))

    def test_new_crypto_analysts_have_expected_nodes(self):
        plan = build_analyst_execution_plan(("onchain", "derivatives", "order_flow", "macro"))
        self.assertEqual(
            [spec.agent_node for spec in plan.specs],
            ["On-chain Analyst", "Derivatives Analyst", "Order Flow Analyst", "Macro Analyst"],
        )


if __name__ == "__main__":
    unittest.main()
