"""DRF API tests for ADRs."""

from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from django_adr.models import ADR


class TestADRAPIList(TestCase):
    """Test ADR API list endpoint."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        super().setUpTestData()
        cls.adr1 = ADR.objects.create(
            title="API ADR 1", context="c", decision="d", consequences="c"
        )
        cls.adr2 = ADR.objects.create(
            title="API ADR 2", context="c", decision="d", consequences="c"
        )

    def test_list_returns_200(self) -> None:
        """Test that the ADR API list endpoint returns HTTP 200."""
        url = reverse("django_adr:adr-api-list")
        self.assertEqual(self.client.get(url).status_code, HTTPStatus.OK)

    def test_list_returns_all_adrs(self) -> None:
        """Test that the API list endpoint returns all created ADRs."""
        url = reverse("django_adr:adr-api-list")
        self.assertEqual(len(self.client.get(url).json()), 2)

    def test_list_includes_rendered_html_fields(self) -> None:
        """Test that the API response includes rendered HTML fields alongside Markdown."""
        url = reverse("django_adr:adr-api-list")
        first = self.client.get(url).json()[0]
        self.assertIn("context_html", first)
        self.assertIn("decision_html", first)
        self.assertIn("consequences_html", first)


class TestADRAPIDetail(TestCase):
    """Test ADR API detail endpoint."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        super().setUpTestData()
        cls.adr = ADR.objects.create(
            title="Detail API ADR", context="c", decision="d", consequences="c"
        )
        cls.other = ADR.objects.create(
            title="Other ADR", context="c", decision="d", consequences="c"
        )

    def test_detail_returns_200(self) -> None:
        """Test that the ADR API detail endpoint returns HTTP 200."""
        url = reverse("django_adr:adr-api-detail", kwargs={"number": self.adr.number})
        self.assertEqual(self.client.get(url).status_code, HTTPStatus.OK)

    def test_detail_returns_correct_number(self) -> None:
        """Test that the API detail endpoint returns the ADR's correct number."""
        url = reverse("django_adr:adr-api-detail", kwargs={"number": self.adr.number})
        self.assertEqual(self.client.get(url).json()["number"], self.adr.number)

    def test_detail_returns_404_for_missing_number(self) -> None:
        """Test that the API detail endpoint returns HTTP 404 for a non-existent number."""
        url = reverse("django_adr:adr-api-detail", kwargs={"number": 9999})
        self.assertEqual(self.client.get(url).status_code, HTTPStatus.NOT_FOUND)

    def test_detail_superseded_by_is_null_when_not_set(self) -> None:
        """Test that superseded_by is null in the API response when not set."""
        url = reverse("django_adr:adr-api-detail", kwargs={"number": self.adr.number})
        self.assertIsNone(self.client.get(url).json()["superseded_by"])

    def test_detail_superseded_by_contains_adr_number(self) -> None:
        """Test that superseded_by in the API response contains the superseding ADR number."""
        self.adr.superseded_by = self.other
        self.adr.status = ADR.Status.SUPERSEDED
        self.adr.save()
        url = reverse("django_adr:adr-api-detail", kwargs={"number": self.adr.number})
        self.assertEqual(self.client.get(url).json()["superseded_by"], self.other.number)

    def test_api_is_read_only(self) -> None:
        """Test that the ADR API rejects all write methods with 405."""
        list_url = reverse("django_adr:adr-api-list")
        detail_url = reverse("django_adr:adr-api-detail", kwargs={"number": self.adr.number})
        kw = {"content_type": "application/json", "data": {}}
        self.assertEqual(
            self.client.post(list_url, **kw).status_code, HTTPStatus.METHOD_NOT_ALLOWED
        )
        self.assertEqual(
            self.client.put(detail_url, **kw).status_code, HTTPStatus.METHOD_NOT_ALLOWED
        )
        self.assertEqual(
            self.client.patch(detail_url, **kw).status_code, HTTPStatus.METHOD_NOT_ALLOWED
        )
        self.assertEqual(self.client.delete(detail_url).status_code, HTTPStatus.METHOD_NOT_ALLOWED)
