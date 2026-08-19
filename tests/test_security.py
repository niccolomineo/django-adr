"""Markdown rendering security tests."""

from http import HTTPStatus

from django.test import TestCase, override_settings
from django.urls import reverse

from django_adr.models import ADR
from django_adr.utils import render_markdown

XSS = "<script>alert(1)</script>"


class TestMarkdownEscaping(TestCase):
    """Test that raw HTML in Markdown source is escaped by default."""

    def test_raw_html_is_escaped(self) -> None:
        """Test that a script tag is rendered as text, not markup."""
        self.assertIn("&lt;script&gt;", render_markdown(XSS))
        self.assertNotIn("<script>", render_markdown(XSS))

    def test_event_handler_attributes_are_escaped(self) -> None:
        """Test that an inline event handler cannot reach the output as markup."""
        self.assertNotIn("<img", render_markdown("<img src=x onerror=alert(1)>"))

    def test_javascript_links_are_neutralised(self) -> None:
        """Test that a javascript: URL is not emitted as an href."""
        self.assertNotIn("javascript:", render_markdown("[click](javascript:alert(1))"))

    def test_data_uri_links_are_neutralised(self) -> None:
        """Test that a data: URL is not emitted as an href."""
        self.assertNotIn("data:text/html", render_markdown("[click](data:text/html,<b>x</b>)"))

    def test_legitimate_markdown_still_renders(self) -> None:
        """Test that escaping does not break ordinary Markdown."""
        self.assertIn("<strong>bold</strong>", render_markdown("**bold**"))

    @override_settings(DJANGO_ADR_MARKDOWN_ESCAPE=False)
    def test_escaping_can_be_disabled_explicitly(self) -> None:
        """Test that the opt-out setting restores raw HTML passthrough."""
        self.assertIn("<script>", render_markdown(XSS))

    @override_settings(USE_I18N=True)
    def test_unrelated_setting_changes_leave_the_renderer_alone(self) -> None:
        """Test that overriding another setting does not disturb rendering."""
        self.assertIn("&lt;script&gt;", render_markdown(XSS))


class TestRenderedOutputIsSafe(TestCase):
    """Test that stored Markdown cannot inject script into responses."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        super().setUpTestData()
        cls.adr = ADR.objects.create(title="Hostile", context=XSS, decision=XSS, consequences=XSS)

    def test_model_properties_escape(self) -> None:
        """Test that the rendered HTML properties contain no live script tag."""
        self.assertNotIn("<script>", self.adr.context_html)
        self.assertNotIn("<script>", self.adr.decision_html)
        self.assertNotIn("<script>", self.adr.consequences_html)

    def test_detail_view_escapes(self) -> None:
        """Test that the detail template does not emit a live script tag."""
        url = reverse("django_adr:adr-detail", args=[self.adr.number])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertNotIn("<script>alert(1)</script>", response.content.decode())

    def test_api_escapes(self) -> None:
        """Test that the API's pre-rendered HTML contains no live script tag."""
        url = reverse("django_adr:adr-api-detail", kwargs={"number": self.adr.number})
        self.assertNotIn("<script>", self.client.get(url).json()["context_html"])
