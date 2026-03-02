import type { Message, StreamingMessage, PageContext } from '../types';

export class WebSocketClient {
  private baseUrl: string;
  private ws: WebSocket | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private get wsUrl(): string {
    return this.baseUrl.replace(/^http/, 'ws') + '/api/v1/messages/ws';
  }

  private connect(): Promise<void> {
    if (this.ws?.readyState === WebSocket.OPEN) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(this.wsUrl);
      ws.onopen = () => { this.ws = ws; resolve(); };
      ws.onerror = (e) => reject(e);
    });
  }

  async sendMessage(
    request: { content: string; context?: PageContext; userId?: string },
    conversationId?: string,
    agentId?: string,
    onStream?: (chunk: StreamingMessage) => void,
  ): Promise<Message> {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      await this.connect();
    }
    const ws = this.ws!;

    return new Promise((resolve, reject) => {
      let fullMessage = '';
      const meta: Partial<Message> = {};

      ws.onmessage = (event: MessageEvent) => {
        let chunk: StreamingMessage;
        try { chunk = JSON.parse(event.data as string); } catch { return; }

        if (chunk.type === 'content') {
          fullMessage += chunk.content || '';
          onStream?.(chunk);
        } else if (chunk.type === 'status') {
          onStream?.(chunk);
        } else if (chunk.type === 'metadata') {
          if (chunk.citations) meta.citations = chunk.citations;
          if (chunk.products) meta.products = chunk.products;
          if (chunk.dealers) meta.dealers = chunk.dealers;
          resolve({
            id: Date.now().toString(),
            content: fullMessage,
            role: 'assistant',
            timestamp: new Date(),
            citations: meta.citations,
            products: meta.products ?? [],
            dealers: meta.dealers ?? [],
          });
        } else if (chunk.type === 'error') {
          reject(new Error(chunk.content || 'WebSocket stream error'));
        }
      };

      ws.onerror = (e) => reject(e);

      ws.send(JSON.stringify({
        message: request.content,
        user_id: request.userId || 'anonymous',
        conversation_id: conversationId,
        agent_id: agentId,
        page_context: request.context,
        stream: true,
      }));
    });
  }

  disconnect(): void {
    this.ws?.close();
    this.ws = null;
  }
}
