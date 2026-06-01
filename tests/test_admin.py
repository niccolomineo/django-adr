"""ADR Django admin tests."""

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from django_adr.models import ADR

User = get_user_model()


class TestADRAdminViews(TestCase):
    """Test ADR admin changelist and change views."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        super().setUpTestData()
        cls.superuser = User.objects.create_superuser(
            username="admin",
            password="password",
            email="admin@example.com",
        )
        cls.adr = ADR.objects.create(
            title="Admin Test ADR",
            context="## Background\n\nWe needed something.",
            decision="We chose this.",
            consequences="It works.",
        )

    def setUp(self) -> None:
        """Log in as superuser before each test."""
        self.client.force_login(self.superuser)

    def test_changelist_returns_200(self) -> None:
        """Test that the ADR admin changelist view returns HTTP 200."""
        url = reverse("admin:django_adr_adr_changelist")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_change_view_returns_200(self) -> None:
        """Test that the ADR admin change view returns HTTP 200."""
        url = reverse("admin:django_adr_adr_change", args=[self.adr.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
