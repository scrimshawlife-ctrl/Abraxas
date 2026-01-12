"""
ABX Operator: alive_integrate_slack

Sends ALIVE field signature updates to Slack (enterprise tier only).
"""

from __future__ import annotations

import json
from typing import Any, Dict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from abraxas.runes.ctx import RuneInvocationContext
from abraxas.runes.invoke import invoke_capability


class ALIVESlackIntegrationOperator:
    """
    ALIVE Slack integration operator.

    Formats and sends ALIVE updates to Slack channels.
    """

    def __init__(self, webhook_url: str | None = None):
        """
        Initialize Slack integration operator.

        Args:
            webhook_url: Slack webhook URL
        """
        self.webhook_url = webhook_url

    def execute(
        self,
        field_signature: Dict[str, Any],
        channel: str = "#alive-updates",
        webhook_url: str | None = None,
    ) -> Dict[str, Any]:
        """
        Send ALIVE update to Slack.

        Args:
            field_signature: ALIVE field signature data
            channel: Slack channel to post to
            webhook_url: Optional Slack webhook URL override

        Returns:
            Response status
        """
        signature = self._normalize_signature(field_signature)

        # Format message
        message = self._format_slack_message(signature, channel)

        target_webhook = webhook_url or self.webhook_url

        if not target_webhook:
            return {
                "status": "error",
                "message": "Missing Slack webhook URL",
                "formatted_message": message,
            }

        payload = json.dumps(message).encode("utf-8")
        request = Request(
            target_webhook,
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=10) as response:
                response_body = response.read().decode("utf-8")
                status_code = response.getcode()
        except HTTPError as exc:
            return {
                "status": "error",
                "message": f"Slack webhook failed: {exc.code} {exc.reason}",
                "formatted_message": message,
            }
        except URLError as exc:
            return {
                "status": "error",
                "message": f"Slack webhook unreachable: {exc.reason}",
                "formatted_message": message,
            }

        if status_code != 200 or response_body.strip().lower() != "ok":
            return {
                "status": "error",
                "message": f"Slack webhook returned {status_code}: {response_body}",
                "formatted_message": message,
            }

        return {
            "status": "ok",
            "message": "Slack notification delivered",
            "formatted_message": message,
        }

    def _format_slack_message(
        self, signature: Dict[str, Any], channel: str
    ) -> Dict[str, Any]:
        """
        Format field signature as Slack message.

        Returns Slack Block Kit formatted message.
        """
        composite = signature.get("compositeScore", {}) or {}

        return {
            "channel": channel,
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🧬 ALIVE Analysis Complete",
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Subject:*\n{signature.get('subjectId')}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Timestamp:*\n{signature.get('timestamp')}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Overall Score:*\n{float(composite.get('overall') or 0.0):.2f}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Analysis ID:*\n`{signature.get('analysisId')}`",
                        },
                    ],
                },
                {
                    "type": "divider",
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Axis Scores:*\n"
                        f"• Influence: {len(signature.get('influence', []) or [])} metrics\n"
                        f"• Vitality: {len(signature.get('vitality', []) or [])} metrics\n"
                        f"• Life-Logistics: {len(signature.get('lifeLogistics', []) or [])} metrics",
                    },
                },
            ],
        }

    def _normalize_signature(self, field_signature: Dict[str, Any]) -> Dict[str, Any]:
        run_id = str(field_signature.get("analysisId") or field_signature.get("subjectId") or "alive_slack")
        ctx = RuneInvocationContext(
            run_id=run_id,
            subsystem_id="abx.operators.alive_integrate_slack",
            git_hash="unknown",
        )
        result = invoke_capability(
            "alive.models.serialize",
            {"field_signature": field_signature},
            ctx=ctx,
            strict_execution=True,
        )
        return result["field_signature"]

    def __call__(
        self,
        field_signature: Dict[str, Any],
        channel: str = "#alive-updates",
        webhook_url: str | None = None,
    ) -> Dict[str, Any]:
        """Allow operator to be called as function."""
        return self.execute(field_signature, channel, webhook_url)
