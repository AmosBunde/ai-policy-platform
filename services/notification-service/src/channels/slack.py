"""Slack webhook delivery with Block Kit formatting."""
import html
import logging

import httpx

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _get_webhook_url() -> str:
    """Get Slack webhook URL from environment only — never from user input."""
    url = settings.slack_webhook_url
    if not url:
        raise RuntimeError("SLACK_WEBHOOK_URL not configured")
    return url


def build_block_kit_message(
    title: str,
    document_title: str,
    summary: str,
    urgency_level: str,
    rule_name: str,
    detail_url: str = "",
) -> dict:
    """Build a Slack Block Kit formatted message."""
    urgency_emoji = {
        "critical": ":rotating_light:",
        "high": ":warning:",
        "normal": ":information_source:",
        "low": ":white_check_mark:",
    }.get(urgency_level, ":bell:")

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{urgency_emoji} {title}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Rule:* {rule_name}\n*Document:* {document_title}",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Summary:*\n{summary[:500]}",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*Urgency:* {urgency_level.upper()} | RegulatorAI",
                },
            ],
        },
    ]

    if detail_url:
        blocks.append({
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View Details"},
                    "url": detail_url,
                    "action_id": "view_details",
                },
            ],
        })

    blocks.append({"type": "divider"})

    return {"blocks": blocks}


async def send_slack(
    title: str,
    document_title: str,
    summary: str,
    urgency_level: str,
    rule_name: str,
    detail_url: str = "",
) -> bool:
    """Send notification to Slack via webhook."""
    try:
        webhook_url = _get_webhook_url()
    except RuntimeError:
        logger.warning("Slack not configured, skipping notification")
        return False

    payload = build_block_kit_message(
        title=title,
        document_title=document_title,
        summary=summary,
        urgency_level=urgency_level,
        rule_name=rule_name,
        detail_url=detail_url,
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook_url, json=payload)
            if resp.status_code == 200:
                logger.info("Slack notification sent: %s", title)
                return True
            else:
                logger.error("Slack webhook returned %d: %s", resp.status_code, resp.text[:200])
                return False
    except Exception as exc:
        logger.error("Failed to send Slack notification: %s", exc)
        return False
