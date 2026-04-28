export function getWidgetBaseUrl(): string {
  const runtimeWidgetUrl = window.__APP_CONFIG__?.WIDGET_BASE_URL;
  const envWidgetUrl = process.env.REACT_APP_WIDGET_URL;
  return (runtimeWidgetUrl || envWidgetUrl || 'http://localhost:5174').replace(/\/+$/, '');
}

export function buildWidgetUrl(agentId: string): string {
  return `${getWidgetBaseUrl()}/?agent_id=${encodeURIComponent(agentId)}&open=1`;
}

export function buildEmbedCode(widgetBaseUrl: string, agentId: string): string {
  return `<script src="${widgetBaseUrl}/embed.js" data-agent-id="${agentId}" async></script>`;
}
