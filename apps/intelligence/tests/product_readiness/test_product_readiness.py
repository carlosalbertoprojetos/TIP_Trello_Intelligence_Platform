from django.test import TestCase
from django.urls import reverse

from apps.integrations.core.exceptions import ProviderNotReadyError
from apps.integrations.core.registry import registry
from apps.integrations.models import IntegrationConnection
from core.models import Tenant
from integrations.trello.models import Board
from apps.intelligence.services.product_readiness.connectors import connector_readiness
from apps.intelligence.services.product_readiness.demo import executive_demo_payload
from apps.intelligence.services.product_readiness.licensing import is_feature_enabled, plan_catalog
from apps.intelligence.services.product_readiness.onboarding import onboarding_blueprint
from apps.intelligence.services.product_readiness.usage import usage_analytics
from apps.intelligence.services.product_readiness.workspace import validate_workspace


class WorkspaceValidationTests(TestCase):
    def test_workspace_validation_identifies_tip(self):
        payload = validate_workspace()

        self.assertEqual(payload["workspace"], "TIP_Trello_Intelligence_Platform")
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["model_version"], "1.1")


class ProductReadinessCatalogTests(TestCase):
    def test_connector_catalog_registers_required_providers(self):
        payload = connector_readiness()
        registered = set(payload["registered_providers"])

        self.assertIn("trello", registered)
        self.assertIn("jira", registered)
        self.assertIn("clickup", registered)
        self.assertIn("asana", registered)
        self.assertIn("monday", registered)
        self.assertIn("github_projects", registered)

    def test_future_provider_is_registered_but_not_ready(self):
        connection = IntegrationConnection.objects.create(provider="asana", project_id="workspace-1")
        adapter = registry.get("asana")

        with self.assertRaises(ProviderNotReadyError):
            adapter.sync(connection)

    def test_licensing_and_onboarding_catalogs_are_explicit(self):
        plans = plan_catalog()
        onboarding = onboarding_blueprint()

        self.assertEqual([plan["name"] for plan in plans["plans"]], ["starter", "professional", "business", "enterprise"])
        self.assertTrue(is_feature_enabled("enterprise", "custom_connectors"))
        self.assertEqual(onboarding["success_event"], "first_executive_report_generated")
        self.assertEqual(len(onboarding["steps"]), 10)

    def test_demo_mode_never_requires_real_token(self):
        payload = executive_demo_payload()

        self.assertEqual(payload["mode"], "demo")
        self.assertFalse(payload["requires_real_token"])


class ProductReadinessApiTests(TestCase):
    def setUp(self):
        self.tenant_a = Tenant.objects.create(name="Tenant A", slug="tenant-a", plan="starter")
        self.tenant_b = Tenant.objects.create(name="Tenant B", slug="tenant-b", plan="enterprise")
        Board.objects.create(tenant=self.tenant_a, trello_id="board-a", name="Board A")
        Board.objects.create(tenant=self.tenant_b, trello_id="board-b", name="Board B")

    def test_workspace_endpoint(self):
        response = self.client.get(reverse("workspace-validation"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["workspace"], "TIP_Trello_Intelligence_Platform")

    def test_demo_endpoint(self):
        response = self.client.get(reverse("executive-demo-mode"))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["requires_real_token"])

    def test_paid_usage_requires_tenant_scope(self):
        response = self.client.get(reverse("usage-analytics"))

        self.assertEqual(response.status_code, 403)

    def test_usage_does_not_cross_tenants(self):
        payload = usage_analytics(tenant=self.tenant_a)

        self.assertEqual(payload["boards_synced"], 0)
        self.assertEqual(payload["board_id"], "all")

    def test_starter_blocks_marketplace_runtime(self):
        response = self.client.get(reverse("operational-marketplace"), HTTP_X_TENANT_ID=str(self.tenant_a.pk))

        self.assertEqual(response.status_code, 403)

    def test_enterprise_allows_marketplace_runtime(self):
        response = self.client.get(reverse("operational-marketplace"), HTTP_X_TENANT_ID=str(self.tenant_b.pk))

        self.assertEqual(response.status_code, 200)

    def test_onboarding_state_persists_and_rejects_cross_tenant_board(self):
        headers = {"HTTP_X_TENANT_ID": str(self.tenant_a.pk)}
        state = self.client.get(reverse("customer-onboarding-state"), **headers)
        self.assertEqual(state.status_code, 200)
        self.assertEqual(state.json()["current_step"], "account")

        selected = self.client.post(
            reverse("customer-onboarding-select-boards"),
            {"board_ids": ["board-b"]},
            content_type="application/json",
            **headers,
        )
        self.assertEqual(selected.status_code, 403)

    def test_starter_board_limit_is_enforced(self):
        Board.objects.create(tenant=self.tenant_a, trello_id="board-a2", name="Board A2")
        Board.objects.create(tenant=self.tenant_a, trello_id="board-a3", name="Board A3")
        response = self.client.post(
            reverse("customer-onboarding-select-boards"),
            {"board_ids": ["board-a", "board-a2", "board-a3"]},
            content_type="application/json",
            HTTP_X_TENANT_ID=str(self.tenant_a.pk),
        )

        self.assertEqual(response.status_code, 402)
