import { useRef, useState } from 'react';
import { streamCosChat } from '../api';
import type { ChatMessage } from '../types';

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const threadId = useRef('cos-web-' + Math.random().toString(36).slice(2));

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setInput('');
    setBusy(true);
    setMessages((m) => [...m, { role: 'user', content: text }, { role: 'assistant', content: '' }]);

    try {
      await streamCosChat(text, threadId.current, (tok) => {
        setMessages((m) => {
          const next = [...m];
          const last = next[next.length - 1];
          if (last && last.role === 'assistant') {
            next[next.length - 1] = { ...last, content: last.content + tok };
          }
          return next;
        });
      });
    } catch (e) {
      setMessages((m) => {
        const next = [...m];
        const last = next[next.length - 1];
        const msg = e instanceof Error ? e.message : 'Chat failed';
        if (last && last.role === 'assistant' && !last.content) {
          next[next.length - 1] = { ...last, content: `⚠️ ${msg}` };
        }
        return next;
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col h-screen">
      <div className="p-700 pb-400 border-b border-hairline">
        <div className="text-ink-muted text-xs uppercase tracking-wide">Chief of Staff</div>
        <h1 className="font-display text-2xl text-ink-primary">Plan with your assistant</h1>
      </div>

      <div className="flex-1 overflow-auto p-700 flex flex-col gap-500 max-w-3xl w-full">
        {messages.length === 0 && (
          <p className="text-ink-secondary">
            Ask me to track an activity, sort out coverage gaps, or help decide between camps.
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'self-end max-w-[80%]' : 'max-w-[90%]'}>
            <div
              className={
                m.role === 'user'
                  ? 'bg-accent text-ink-on-photo-light rounded-xl px-500 py-300'
                  : 'text-ink-primary whitespace-pre-wrap'
              }
            >
              {m.content || (busy ? '…' : '')}
            </div>
          </div>
        ))}
      </div>

      <div className="p-500 border-t border-hairline flex gap-400 max-w-3xl w-full">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') send();
          }}
          placeholder="Ask about your plan"
          disabled={busy}
          className="flex-1 border border-strong rounded-lg px-400 py-300 bg-elevated outline-none focus:border-accent"
        />
        <button
          onClick={send}
          disabled={busy || !input.trim()}
          className="bg-accent text-ink-on-photo-light rounded-lg px-500 py-300 font-medium disabled:opacity-60"
        >
          Send
        </button>
      </div>
    </div>
  );
}
