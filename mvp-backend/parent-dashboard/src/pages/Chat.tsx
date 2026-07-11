import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { streamCosChat } from '../api';
import type { ChatMessage, VerticalDoor } from '../types';
import { cachedDoors, fetchDoors } from '../lib/doors';
import { capture } from '../analytics';

export default function Chat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [doors, setDoors] = useState<VerticalDoor[]>(cachedDoors());
  const threadId = useRef('cos-web-' + Math.random().toString(36).slice(2));
  const location = useLocation();
  const startedFromDoor = useRef(false);

  useEffect(() => {
    void fetchDoors().then(setDoors);
  }, []);

  // Arriving through a door on the Plan page ("Plan something" → door tap):
  // send that door's starter prompt as the first turn, exactly once.
  useEffect(() => {
    const state = location.state as { starter?: string; door?: string } | null;
    if (state?.starter && !startedFromDoor.current) {
      startedFromDoor.current = true;
      if (state.door) capture('door_converted', { door: state.door });
      void send(state.starter);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function send(textArg?: string) {
    const text = (textArg ?? input).trim();
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

  function startFromDoor(d: VerticalDoor) {
    capture('door_opened', { door: d.key });
    capture('door_converted', { door: d.key });
    void send(d.starter_prompt);
  }

  return (
    <div className="flex flex-col h-screen">
      <div className="p-700 pb-400 border-b border-hairline">
        <div className="text-ink-muted text-xs uppercase tracking-wide">Chief of Staff</div>
        <h1 className="font-display text-2xl text-ink-primary">Plan with your assistant</h1>
      </div>

      <div className="flex-1 overflow-auto p-700 flex flex-col gap-500 max-w-3xl w-full">
        {messages.length === 0 && (
          <div>
            <p className="text-ink-secondary mb-500">
              Ask me what to do this weekend, track an activity, sort out coverage gaps, or help
              decide between camps.
            </p>
            {/* The entry doors, as starter cards (server-driven copy). */}
            {doors.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-400">
                {doors.map((d) => (
                  <button
                    key={d.key}
                    onClick={() => startFromDoor(d)}
                    disabled={busy}
                    className="text-left bg-elevated border border-hairline rounded-xl p-500 hover:border-accent disabled:opacity-60"
                  >
                    <div className="text-ink-primary font-medium">{d.title}</div>
                    <div className="text-ink-muted text-sm mt-100">{d.subtitle}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'self-end max-w-[80%]' : 'max-w-[90%]'}>
            {m.role === 'user' ? (
              <div className="bg-accent text-ink-on-photo-light rounded-xl px-500 py-300">
                {m.content}
              </div>
            ) : (
              <div className="text-ink-primary chat-markdown">
                {m.content ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: (p) => <p className="mb-300 leading-relaxed" {...p} />,
                      ul: (p) => <ul className="list-disc pl-500 mb-300 space-y-100" {...p} />,
                      ol: (p) => <ol className="list-decimal pl-500 mb-300 space-y-100" {...p} />,
                      a: (p) => (
                        <a
                          className="text-accent underline"
                          target="_blank"
                          rel="noopener noreferrer"
                          {...p}
                        />
                      ),
                      strong: (p) => <strong className="font-semibold" {...p} />,
                      table: (p) => (
                        <div className="overflow-x-auto mb-300">
                          <table className="text-sm border-collapse" {...p} />
                        </div>
                      ),
                      th: (p) => (
                        <th className="text-left font-semibold border-b border-strong px-300 py-100" {...p} />
                      ),
                      td: (p) => <td className="border-b border-hairline px-300 py-100" {...p} />,
                      code: (p) => <code className="bg-canvas rounded px-100 text-sm" {...p} />,
                    }}
                  >
                    {m.content}
                  </ReactMarkdown>
                ) : busy ? (
                  '…'
                ) : (
                  ''
                )}
              </div>
            )}
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
          onClick={() => send()}
          disabled={busy || !input.trim()}
          className="bg-accent text-ink-on-photo-light rounded-lg px-500 py-300 font-medium disabled:opacity-60"
        >
          Send
        </button>
      </div>
    </div>
  );
}
