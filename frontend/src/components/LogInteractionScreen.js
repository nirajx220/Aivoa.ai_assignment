import React from 'react';
import './LogInteractionScreen.css';
import StructuredForm from './StructuredForm';
import ChatInterface from './ChatInterface';

/**
 * The "Log Interaction Screen" required by the spec:
 * users can log an HCP interaction via a structured form (left) OR a
 * conversational chat interface (right) - both write to the same
 * Redux state / backend record, so they always stay in sync.
 */
export default function LogInteractionScreen() {
  return (
    <div className="app-shell">
      <header className="top-bar">
        <div className="brand">
          <div className="brand-mark">Rx</div>
          <div>
            <h1>HCP Interaction Logger</h1>
            <p>AI-first CRM &middot; powered by LangGraph + Groq</p>
          </div>
        </div>
      </header>

      <div className="split">
        <div className="panel-left">
          <StructuredForm />
        </div>
        <div className="panel-right">
          <ChatInterface />
        </div>
      </div>
    </div>
  );
}
