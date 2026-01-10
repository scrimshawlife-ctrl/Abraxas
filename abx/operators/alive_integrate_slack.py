"""
ABX Operator: alive_integrate_slack

Sends ALIVE field signature updates to Slack (enterprise tier only).
"""

from __future__ import annotations

import json
from typing import Any, Dict

# ALIVEFieldSignature replaced by alive.parse_field_signature capability
from abraxas.runes.invoke import invoke_capability
from abraxas.runes.ctx import RuneInvocationContext


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
    ) -> Dict[str, Any]:
        """
        Send ALIVE update to Slack.

        Args:
            field_signature: ALIVE field signature data
            channel: Slack channel to post to

        Returns:
            Response status
        """
        # Parse and validate signature via capability
        ctx = RuneInvocationContext(
            run_id="ALIVE_SLACK",
            subsystem_id="abx.operators.alive_integrate_slack",
            git_hash="unknown"
        )

        parse_result = invoke_capability(
            "alive.parse_field_signature",
            {"field_signature": field_signature},
            ctx=ctx,
            strict_execution=True
        )

        parsed_signature = parse_result["parsed_signature"]
        if parsed_signature is None:
            raise ValueError(f"Invalid field signature: {parse_result['parse_error']}")

        # Format message
        message = self._format_slack_message(parsed_signature, channel)

        # TODO: Actually send to Slack webhook
        # For now, just return the formatted message
        return {
            "status": "stub",
            "message": "Slack integration not yet fully implemented",
            "formatted_message": message,
        }

    def _format_slack_message(
        self, signature: Dict[str, Any], channel: str
    ) -> Dict[str, Any]:
        """
        Format field signature as Slack message.

        Returns Slack Block Kit formatted message.
        """
        composite = signature.get("compositeScore", {})

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
                            "text": f"*Subject:*\n{signature.get('subjectId', 'Unknown')}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Timestamp:*\n{signature.get('timestamp', 'Unknown')}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Overall Score:*\n{composite.get('overall', 0.0):.2f}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Analysis ID:*\n`{signature.get('analysisId', 'Unknown')}`",
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
                        f"• Influence: {len(signature.get('influence', []))} metrics\n"
                        f"• Vitality: {len(signature.get('vitality', []))} metrics\n"
                        f"• Life-Logistics: {len(signature.get('lifeLogistics', []))} metrics",
                    },
                },
            ],
        }

    def __call__(
        self,
        field_signature: Dict[str, Any],
        channel: str = "#alive-updates",
    ) -> Dict[str, Any]:
        """Allow operator to be called as function."""
        return self.execute(field_signature, channel)
