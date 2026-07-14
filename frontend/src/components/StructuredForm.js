import React, { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  fieldChanged, chipAdded, chipRemoved, formCleared,
  saveInteractionForm, removeInteraction,
} from '../store/interactionSlice';

const TEXT_FIELDS = ['hcp_name', 'attendees'];
const TEXTAREA_FIELDS = ['topics', 'outcomes', 'follow_up_actions'];

export default function StructuredForm() {
  const dispatch = useDispatch();
  const form = useSelector((s) => s.interaction.form);
  const lastUpdatedFields = useSelector((s) => s.interaction.lastUpdatedFields);
  const [materialsInput, setMaterialsInput] = useState('');
  const [samplesInput, setSamplesInput] = useState('');
  const highlightRefs = useRef({});

  // Briefly glow any field the AI just updated via chat.
  useEffect(() => {
    lastUpdatedFields.forEach((field) => {
      const el = highlightRefs.current[field];
      if (!el) return;
      el.classList.remove('highlight');
      // eslint-disable-next-line no-unused-expressions
      void el.offsetWidth;
      el.classList.add('highlight');
      setTimeout(() => el.classList.remove('highlight'), 1600);
    });
  }, [lastUpdatedFields]);

  const setField = (field) => (e) => dispatch(fieldChanged({ field, value: e.target.value }));

  const addChip = (field, value, resetFn) => {
    if (!value.trim()) return;
    dispatch(chipAdded({ field, value: value.trim() }));
    resetFn('');
  };

  return (
    <>
      <div className="form-title">Log HCP Interaction</div>
      <p className="form-sub">Fill this in directly, or describe the visit in the chat panel and it fills in for you.</p>

      <div className="field-row">
        <div className="field-group">
          <div className="field-wrap" ref={(el) => (highlightRefs.current.hcp_name = el)}>
            <label>HCP Name</label>
            <input type="text" value={form.hcp_name} onChange={setField('hcp_name')} placeholder="Search or select HCP..." />
          </div>
        </div>
        <div className="field-group">
          <div className="field-wrap" ref={(el) => (highlightRefs.current.interaction_type = el)}>
            <label>Interaction Type</label>
            <select value={form.interaction_type} onChange={setField('interaction_type')}>
              {['Meeting', 'Call', 'Email', 'Conference', 'Sample Drop', 'Other'].map((t) => (
                <option key={t}>{t}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="field-row">
        <div className="field-group">
          <div className="field-wrap" ref={(el) => (highlightRefs.current.interaction_date = el)}>
            <label>Date</label>
            <input type="date" value={form.interaction_date || ''} onChange={setField('interaction_date')} />
          </div>
        </div>
        <div className="field-group">
          <div className="field-wrap" ref={(el) => (highlightRefs.current.interaction_time = el)}>
            <label>Time</label>
            <input type="time" value={form.interaction_time || ''} onChange={setField('interaction_time')} />
          </div>
        </div>
      </div>

      {TEXT_FIELDS.slice(1).map((field) => (
        <div className="field-group" key={field}>
          <div className="field-wrap" ref={(el) => (highlightRefs.current[field] = el)}>
            <label>Attendees</label>
            <input type="text" value={form[field]} onChange={setField(field)} placeholder="Enter names or search..." />
          </div>
        </div>
      ))}

      <div className="field-group">
        <div className="field-wrap" ref={(el) => (highlightRefs.current.topics = el)}>
          <label>Topics Discussed</label>
          <textarea value={form.topics} onChange={setField('topics')} placeholder="Enter key discussion points..." />
        </div>
      </div>

      <div className="divider" />

      <div className="field-group">
        <div className="field-wrap" ref={(el) => (highlightRefs.current.materials_shared = el)}>
          <label>Materials Shared</label>
          <div className={`chip-box ${form.materials_shared.length ? '' : 'empty'}`} data-empty="No materials added.">
            {form.materials_shared.map((m, i) => (
              <div className="chip" key={`${m}-${i}`}>
                <span>{m}</span>
                <button onClick={() => dispatch(chipRemoved({ field: 'materials_shared', index: i }))}>×</button>
              </div>
            ))}
          </div>
          <div className="chip-add">
            <input
              type="text" value={materialsInput}
              onChange={(e) => setMaterialsInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addChip('materials_shared', materialsInput, setMaterialsInput))}
              placeholder="Add a material and press Enter..."
            />
            <button className="add-btn" onClick={() => addChip('materials_shared', materialsInput, setMaterialsInput)}>Add</button>
          </div>
        </div>
      </div>

      <div className="field-group">
        <div className="field-wrap" ref={(el) => (highlightRefs.current.samples_distributed = el)}>
          <label>Samples Distributed</label>
          <div className={`chip-box ${form.samples_distributed.length ? '' : 'empty'}`} data-empty="No samples added.">
            {form.samples_distributed.map((s, i) => (
              <div className="chip" key={`${s}-${i}`}>
                <span>{s}</span>
                <button onClick={() => dispatch(chipRemoved({ field: 'samples_distributed', index: i }))}>×</button>
              </div>
            ))}
          </div>
          <div className="chip-add">
            <input
              type="text" value={samplesInput}
              onChange={(e) => setSamplesInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addChip('samples_distributed', samplesInput, setSamplesInput))}
              placeholder="Add a sample and press Enter..."
            />
            <button className="add-btn" onClick={() => addChip('samples_distributed', samplesInput, setSamplesInput)}>Add</button>
          </div>
        </div>
      </div>

      <div className="divider" />

      <div className="field-group">
        <div className="field-wrap" ref={(el) => (highlightRefs.current.sentiment = el)}>
          <label>Observed / Inferred HCP Sentiment</label>
          <div className="sentiment-row">
            {['Positive', 'Neutral', 'Negative'].map((val) => (
              <div
                key={val}
                className={`sentiment-opt ${form.sentiment === val ? `sel-${val}` : ''}`}
                onClick={() => dispatch(fieldChanged({ field: 'sentiment', value: form.sentiment === val ? '' : val }))}
              >
                <span className="emoji">{val === 'Positive' ? '🙂' : val === 'Neutral' ? '😐' : '🙁'}</span>
                {val}
              </div>
            ))}
          </div>
        </div>
      </div>

      {TEXTAREA_FIELDS.slice(1).map((field) => (
        <div className="field-group" key={field}>
          <div className="field-wrap" ref={(el) => (highlightRefs.current[field] = el)}>
            <label>{field === 'outcomes' ? 'Outcomes' : 'Follow-up Actions'}</label>
            <textarea
              value={form[field]}
              onChange={setField(field)}
              placeholder={field === 'outcomes' ? 'Key outcomes or agreements...' : 'e.g. Schedule next meeting, send samples...'}
            />
          </div>
        </div>
      ))}

      <div className="form-actions">
        <button className="btn-primary" onClick={() => dispatch(saveInteractionForm())}>Save Interaction</button>
        {form.id && (
          <button className="btn-danger" onClick={() => dispatch(removeInteraction())}>Delete this interaction</button>
        )}
      </div>
      <div style={{ marginTop: 10 }}>
        <button className="btn-danger" onClick={() => dispatch(formCleared())}>Clear entire form</button>
      </div>
    </>
  );
}
