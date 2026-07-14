import { createSlice, createAsyncThunk, nanoid } from '@reduxjs/toolkit';
import * as api from '../api/api';

const SESSION_ID = nanoid();

const emptyForm = {
  id: null,
  hcp_name: '',
  interaction_type: 'Meeting',
  interaction_date: '',
  interaction_time: '',
  attendees: '',
  topics: '',
  materials_shared: [],
  samples_distributed: [],
  sentiment: '',
  outcomes: '',
  follow_up_actions: '',
};

const initialState = {
  form: { ...emptyForm },
  chatMessages: [
    {
      role: 'assistant',
      text: 'Log interaction details here (e.g. "Met Dr. Smith, discussed Prodo-X efficacy, positive sentiment, shared brochure") or ask for help. You can also say "clear the outcomes" or "delete this interaction".',
    },
  ],
  status: 'idle',
  lastUpdatedFields: [],
};

// ---- Structured-form thunks (talk to REST endpoints directly) ----
export const saveInteractionForm = createAsyncThunk(
  'interaction/saveForm',
  async (_, { getState }) => {
    const { form } = getState().interaction;
    if (form.id) {
      return api.updateInteraction(form.id, form);
    }
    return api.createInteraction(form);
  }
);

export const removeInteraction = createAsyncThunk(
  'interaction/remove',
  async (_, { getState }) => {
    const { form } = getState().interaction;
    if (form.id) await api.deleteInteraction(form.id);
    return true;
  }
);

// ---- Chat thunk (talks to the LangGraph agent via /api/chat) ----
export const sendChatMessage = createAsyncThunk(
  'interaction/sendChatMessage',
  async (message) => {
    const data = await api.sendChatMessage(SESSION_ID, message);
    return data;
  }
);

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    fieldChanged(state, action) {
      const { field, value } = action.payload;
      state.form[field] = value;
    },
    chipAdded(state, action) {
      const { field, value } = action.payload;
      if (value) state.form[field].push(value);
    },
    chipRemoved(state, action) {
      const { field, index } = action.payload;
      state.form[field].splice(index, 1);
    },
    formCleared(state) {
      state.form = { ...emptyForm };
    },
    userMessageAdded(state, action) {
      state.chatMessages.push({ role: 'user', text: action.payload });
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(saveInteractionForm.fulfilled, (state, action) => {
        state.form.id = action.payload.id;
      })
      .addCase(removeInteraction.fulfilled, (state) => {
        state.form = { ...emptyForm };
      })
      .addCase(sendChatMessage.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.status = 'idle';
        const data = action.payload;

        if (data.interaction_id) state.form.id = data.interaction_id;

        if (data.clear_all) {
          state.form = { ...emptyForm, id: state.form.id };
        } else if (data.clear_fields && data.clear_fields.length) {
          data.clear_fields.forEach((f) => {
            state.form[f] = Array.isArray(state.form[f]) ? [] : '';
          });
        }

        const updates = data.updates || {};
        Object.keys(updates).forEach((key) => {
          if (key in state.form && updates[key] !== null && updates[key] !== undefined) {
            state.form[key] = updates[key];
          }
        });

        state.lastUpdatedFields = [
          ...Object.keys(updates),
          ...(data.clear_fields || []),
        ];

        state.chatMessages.push({
          role: (Object.keys(updates).length || (data.clear_fields || []).length || data.clear_all) ? 'success' : 'assistant',
          text: data.reply,
        });
      })
      .addCase(sendChatMessage.rejected, (state) => {
        state.status = 'idle';
        state.chatMessages.push({
          role: 'error',
          text: 'Something went wrong reaching the assistant. Please try again.',
        });
      });
  },
});

export const {
  fieldChanged, chipAdded, chipRemoved, formCleared, userMessageAdded,
} = interactionSlice.actions;

export default interactionSlice.reducer;
