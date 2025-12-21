export async function postToSlackWebhook(
  webhookUrl: string,
  payload: { text: string }
): Promise<void> {
  const res = await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`Slack webhook failed: ${res.status} ${txt}`);
  }
}
