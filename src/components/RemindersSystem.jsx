// WithMe Gentle Companion Reminders Component

import React, { useState } from 'react';
import { memoryStore } from '../engine/memoryStore';
import { Bell, CheckCircle2, Circle, Plus, Trash2, Calendar, HeartHandshake } from 'lucide-react';

export default function RemindersSystem() {
  const [reminders, setReminders] = useState(() => memoryStore.getReminders());
  const [showAddModal, setShowAddModal] = useState(false);
  const [title, setTitle] = useState('');
  const [due, setDue] = useState('');
  const [note, setNote] = useState('');

  const handleToggle = (id) => {
    const updated = memoryStore.toggleReminder(id);
    setReminders(updated);
  };

  const handleDelete = (id) => {
    const updated = memoryStore.deleteReminder(id);
    setReminders(updated);
  };

  const handleAdd = (e) => {
    e.preventDefault();
    if (!title.trim() || !due.trim()) return;

    const updated = memoryStore.addReminder(title, due, note);
    setReminders(updated);
    setTitle('');
    setDue('');
    setNote('');
    setShowAddModal(false);
  };

  return (
    <div className="max-w-5xl mx-auto w-full p-4 sm:p-6 space-y-6">
      {/* Header */}
      <div className="glass-card p-6 border border-purple-500/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="p-3 rounded-2xl bg-gradient-to-tr from-amber-500 to-purple-600 text-white shadow-lg shadow-amber-500/20">
            <Bell className="w-7 h-7" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Gentle Companion Reminders</h2>
            <p className="text-xs text-gray-400">Optional friendly check-ins that feel like a companion, not a push notification</p>
          </div>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary py-2.5 px-4 text-xs"
        >
          <Plus className="w-4 h-4" />
          <span>New Reminder</span>
        </button>
      </div>

      {/* Reminders List */}
      {reminders.length === 0 ? (
        <div className="glass-card p-12 text-center text-gray-400 space-y-3">
          <HeartHandshake className="w-10 h-10 text-purple-400 mx-auto opacity-70" />
          <p className="text-base font-semibold text-gray-200">No reminders scheduled</p>
          <p className="text-xs text-gray-500">Add a gentle reminder for upcoming events, game nights, or self-care breaks!</p>
        </div>
      ) : (
        <div className="space-y-3">
          {reminders.map((rem) => (
            <div
              key={rem.id}
              className={`glass-card p-4 sm:p-5 border transition-all flex items-start justify-between gap-4 ${
                rem.completed
                  ? 'bg-slate-950/40 border-white/5 opacity-60'
                  : 'border-white/10 hover:border-purple-500/30'
              }`}
            >
              <div className="flex items-start gap-3.5 flex-1">
                <button
                  onClick={() => handleToggle(rem.id)}
                  className="mt-0.5 text-gray-400 hover:text-purple-400 transition-colors"
                >
                  {rem.completed ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  ) : (
                    <Circle className="w-5 h-5 text-gray-500" />
                  )}
                </button>
                <div className="space-y-1">
                  <h4 className={`text-base font-semibold ${rem.completed ? 'line-through text-gray-500' : 'text-white'}`}>
                    {rem.title}
                  </h4>
                  <p className="text-xs text-purple-300 font-medium">{rem.note}</p>
                  <div className="flex items-center gap-1.5 text-[11px] text-gray-500 pt-1">
                    <Calendar className="w-3 h-3 text-purple-400" />
                    <span>{rem.due}</span>
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleDelete(rem.id)}
                className="p-1.5 rounded-lg text-gray-500 hover:text-red-400 hover:bg-white/10 transition-colors"
                title="Delete reminder"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
          <div className="glass-card w-full max-w-md p-6 border border-purple-500/30 space-y-4">
            <h3 className="text-lg font-bold text-white">Create Companion Reminder</h3>
            <form onSubmit={handleAdd} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Reminder Title</label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Review presentation slides"
                  className="glass-input w-full text-sm"
                  required
                />
              </div>

              <div>
                <label className="text-xs text-gray-400 block mb-1">When is it due?</label>
                <input
                  type="text"
                  value={due}
                  onChange={(e) => setDue(e.target.value)}
                  placeholder="e.g. Tomorrow, 10:00 AM"
                  className="glass-input w-full text-sm"
                  required
                />
              </div>

              <div>
                <label className="text-xs text-gray-400 block mb-1">Companion Note (Optional)</label>
                <input
                  type="text"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="e.g. You've got this! 🚀"
                  className="glass-input w-full text-sm"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary py-2 px-4 text-xs"
                >
                  Cancel
                </button>
                <button type="submit" className="btn-primary py-2 px-4 text-xs">
                  Save Reminder
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
