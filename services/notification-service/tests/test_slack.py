"""Tests for Slack channel: Block Kit formatting, webhook validation."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.channels.slack import build_block_kit_message, _get_webhook_url


class TestBlockKitMessage:
    def test_builds_valid_blocks(self):
        msg = build_block_kit_message(
            title="Regulatory Alert",
            document_title="EU AI Act Update",
            summary="New compliance requirements for AI systems.",
            urgency_level="high",
            rule_name="EU Privacy Watch",
        )
        assert "blocks" in msg
        assert len(msg["blocks"]) >= 4

    def test_header_block(self):
        msg = build_block_kit_message(
            title="Alert", document_title="Doc",
            summary="Sum", urgency_level="critical", rule_name="Rule",
        )
        header = msg["blocks"][0]
        assert header["type"] == "header"
        assert "Alert" in header["text"]["text"]

    def test_urgency_emoji_critical(self):
        msg = build_block_kit_message(
            title="Alert", document_title="Doc",
            summary="Sum", urgency_level="critical", rule_name="Rule",
        )
        assert ":rotating_light:" in msg["blocks"][0]["text"]["text"]

    def test_urgency_emoji_high(self):
        msg = build_block_kit_message(
            title="Alert", document_title="Doc",
            summary="Sum", urgency_level="high", rule_name="Rule",
        )
        assert ":warning:" in msg["blocks"][0]["text"]["text"]

    def test_includes_detail_url_button(self):
        msg = build_block_kit_message(
            title="Alert", document_title="Doc",
            summary="Sum", urgency_level="normal", rule_name="Rule",
            detail_url="https://example.com",
        )
        action_blocks = [b for b in msg["blocks"] if b["type"] == "actions"]
        assert len(action_blocks) == 1

    def test_no_button_without_url(self):
        msg = build_block_kit_message(
            title="Alert", document_title="Doc",
            summary="Sum", urgency_level="normal", rule_name="Rule",
        )
        action_blocks = [b for b in msg["blocks"] if b["type"] == "actions"]
        assert len(action_blocks) == 0

    def test_summary_truncated(self):
        long_summary = "x" * 1000
        msg = build_block_kit_message(
            title="Alert", document_title="Doc",
            summary=long_summary, urgency_level="normal", rule_name="Rule",
        )
        summary_block = msg["blocks"][2]
        assert len(summary_block["text"]["text"]) < 600


class TestWebhookUrl:
    def test_raises_when_not_configured(self):
        from shared.config.settings import get_settings
        settings = get_settings()
        original = settings.slack_webhook_url
        try:
            settings.slack_webhook_url = ""
            with pytest.raises(RuntimeError, match="not configured"):
                _get_webhook_url()
        finally:
            settings.slack_webhook_url = original

    def test_returns_url_when_configured(self):
        from shared.config.settings import get_settings
        settings = get_settings()
        original = settings.slack_webhook_url
        try:
            settings.slack_webhook_url = "https://hooks.slack.com/services/xxx"
            url = _get_webhook_url()
            assert url == "https://hooks.slack.com/services/xxx"
        finally:
            settings.slack_webhook_url = original
