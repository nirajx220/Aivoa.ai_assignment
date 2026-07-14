import axios from 'axios';

// No LLM/API keys live here. The Groq key stays in backend/.env and is only
// ever used server-side (see backend/app/agent/llm.py). This client just
// talks to our own FastAPI backend.
const api = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
});

export const createInteraction = (data) => api.post('/api/interactions', data).then(r => r.data);
export const updateInteraction = (id, data) => api.put(`/api/interactions/${id}`, data).then(r => r.data);
export const deleteInteraction = (id) => api.delete(`/api/interactions/${id}`).then(r => r.data);
export const searchHcps = (q) => api.get('/api/interactions/hcps/search', { params: { q } }).then(r => r.data);

export const sendChatMessage = (sessionId, message) =>
  api.post('/api/chat', { session_id: sessionId, message }).then(r => r.data);

export default api;
