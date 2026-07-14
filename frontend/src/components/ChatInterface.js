import React, { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { sendChatMessage, userMessageAdded } from '../store/interactionSlice';

export default function ChatInterface() {
  const dispatch = useDispatch();
  const messages = useSelector((s) => s.interaction.chatMessages);
  const status = useSelector((s) => s.interaction.status);
  const [text, setText] = useState('');
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, status]);

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed) return;
    dispatch(userMessageAdded(trimmed));
    dispatch(sendChatMessage(trimmed));
    setText('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      <div className="chat-head">
        <div className="chat-head-row">
          <div className="ai-icon">✦</div>
          <div>
            <h2>AI Assistant</h2>
            <p>Log or edit the interaction here via chat</p>
          </div>
        </div>
      </div>

      <div className="chat-scroll" ref={scrollRef}>
        {messages.map((m, i) => (
          <div className={`bubble ${m.role}`} key={i}>{m.text}</div>
        ))}
        {status === 'loading' && (
          <div className="typing"><span /><span /><span /></div>
        )}
      </div>

      <div className="chat-input-wrap">
        <div className="chat-input-row">
          <textarea
            rows={1}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Describe interaction..."
          />
          <button className="send-btn" disabled={status === 'loading'} onClick={handleSend}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
              <path d="M4 12L20 4L14 20L11 13L4 12Z" stroke="white" strokeWidth="2" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
        <p className="hint">The assistant can fill in fields, look up HCP history, schedule follow-ups, and clear fields on request.</p>
      </div>
    </>
  );
}
