"""ADR HTML view tests."""

from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from django_adr.models import ADR


class TestADRListView(TestCase):
    """Test ADR list view."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        super().setUpTestData()
        cls.adr1 = ADR.objects.create(
            title="First Decision", context="c", decision="d", consequences="c"
        )
        cls.adr2 = ADR.objects.create(
            title="Second Decision", context="c", decision="d", consequences="c"
        )

    def test_list_view_returns_200(self) -> None:
        """Test that the ADR list view returns HTTP 200."""
        response = self.client.get(reverse("django_adr:adr-list"))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_list_view_contains_all_adr_titles(self) -> None:
        """Test that the ADR list view renders all ADR titles."""
        response = self.client.get(reverse("django_adr:adr-list"))
        self.assertContains(response, "First Decision")
        self.assertContains(response, "Second Decision")

    def test_list_view_uses_correct_template(self) -> None:
        """Test that the ADR list view uses the django_adr/adr_list.html template."""
        response = self.client.get(reverse("django_adr:adr-list"))
        self.assertTemplateUsed(response, "django_adr/adr_list.html")

    def test_list_view_shows_no_adrs_message_when_empty(self) -> None:
        """Test that the ADR list view shows a placeholder when no ADRs exist."""
        ADR.objects.all().delete()
        response = self.client.get(reverse("django_adr:adr-list"))
        self.assertContains(response, "No ADRs yet.")

    def test_list_view_filters_by_status(self) -> None:
        """Test that the ADR list view returns only ADRs matching the status filter."""
        accepted = ADR.objects.create(
            title="Accepted ADR",
            status=ADR.Status.ACCEPTED,
            context="c",
            decision="d",
            consequences="c",
        )
        url = reverse("django_adr:adr-list")
        response = self.client.get(url, {"status": ADR.Status.ACCEPTED})
        self.assertContains(response, accepted.title)
        self.assertNotContains(response, "First Decision")

    def test_list_view_passes_statuses_to_context(self) -> None:
        """Test that the ADR list view passes all status choices to the template context."""
        response = self.client.get(reverse("django_adr:adr-list"))
        self.assertIn("statuses", response.context)
        self.assertEqual(response.context["statuses"], ADR.Status.choices)

    def test_list_view_passes_current_status_to_context(self) -> None:
        """Test that the ADR list view passes the active status filter to the template context."""
        url = reverse("django_adr:adr-list")
        response = self.client.get(url, {"status": ADR.Status.ACCEPTED})
        self.assertEqual(response.context["current_status"], ADR.Status.ACCEPTED)


class TestADRDetailView(TestCase):
    """Test ADR detail view."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        super().setUpTestData()
        cls.adr = ADR.objects.create(
            title="Detail ADR",
            context="## Context\n\nSomething important.",
            decision="We decided.",
            consequences="Stuff happens.",
        )

    def test_detail_view_returns_200(self) -> None:
        """Test that the ADR detail view returns HTTP 200 for a valid number."""
        url = reverse("django_adr:adr-detail", args=[self.adr.number])
        self.assertEqual(self.client.get(url).status_code, HTTPStatus.OK)

    def test_detail_view_renders_title(self) -> None:
        """Test that the ADR detail view renders the ADR title."""
        url = reverse("django_adr:adr-detail", args=[self.adr.number])
        self.assertContains(self.client.get(url), "Detail ADR")

    def test_detail_view_renders_context_markdown_as_html(self) -> None:
        """Test that the ADR detail view renders context Markdown as HTML."""
        url = reverse("django_adr:adr-detail", args=[self.adr.number])
        self.assertContains(self.client.get(url), "<h2>")

    def test_detail_view_uses_correct_template(self) -> None:
        """Test that the ADR detail view uses the django_adr/adr_detail.html template."""
        url = reverse("django_adr:adr-detail", args=[self.adr.number])
        self.assertTemplateUsed(self.client.get(url), "django_adr/adr_detail.html")

    def test_detail_view_returns_404_for_unknown_number(self) -> None:
        """Test that the ADR detail view returns HTTP 404 for a non-existent number."""
        url = reverse("django_adr:adr-detail", args=[9999])
        self.assertEqual(self.client.get(url).status_code, HTTPStatus.NOT_FOUND)

    def test_detail_view_shows_superseded_by_link(self) -> None:
        """Test that the ADR detail view renders a link to the superseding ADR."""
        old = ADR.objects.create(title="Old ADR", context="c", decision="d", consequences="c")
        new = ADR.objects.create(title="New ADR", context="c", decision="d", consequences="c")
        old.superseded_by = new
        old.status = ADR.Status.SUPERSEDED
        old.save()
        url = reverse("django_adr:adr-detail", args=[old.number])
        response = self.client.get(url)
        self.assertContains(response, "Superseded by")
        self.assertContains(response, reverse("django_adr:adr-detail", args=[new.number]))
