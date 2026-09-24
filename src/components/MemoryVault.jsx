// WithMe Memory Vault & Privacy Control Component

import React, { useState, useEffect } from 'react';
import { memoryStore } from '../engine/memoryStore';
import { Brain, ShieldCheck, Trash2, Plus, Search, Tag, AlertTriangle, Calendar, Lock } from 'lucide-react';

export default function MemoryVault({ userProfile }) {
  const [memories, setMemories] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [newContent, setNewContent] = useState('');
  const [newCategory, setNewCategory] = useState('Preferences');
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    setMemories(memoryStore.getMemories());
  }, []);

  const categories = ['All', 'Events', 'Preferences', 'Communication', 'Personal', 'Academic'];

  const filteredMemories = memories.filter((mem) => {
    const matchesSearch = mem.content.toLowerCase().includes(searchQuery.toLowerCase()) || mem.tag.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCat = selectedCategory === 'All' || mem.category === selectedCategory;
    return matchesSearch && matchesCat;
  });

  const handleAddMemory = (e) => {
    e.preventDefault();
    if (!newContent.trim()) return;
    const added = memoryStore.addMemory(newContent, newCategory, 'User Added');
    setMemories([added, ...memories]);
    setNewContent('');
    setShowAddModal(false);
  };

  const handleDeleteMemory = (id) => {
    const updated = memoryStore.deleteMemory(id);
    setMemories(updated);
  };

  const handleClearAll = () => {
    if (window.confirm("Are you sure you want to clear all remembered context? This action cannot be undone.")) {
      const empty = memoryStore.clearAllMemories();
      setMemories(empty);
    }
  };

  return (
    <div className="max-w-5xl mx-auto w-full p-4 sm:p-6 space-y-6">
      {/* Header Banner */}
      <div className="glass-card p-6 border border-purple-500/20 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-purple-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <div className="p-3 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 text-white shadow-lg shadow-purple-500/20">
              <Brain className="w-7 h-7" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                Memory Vault
              </h2>
              <p className="text-xs text-gray-400">Context & preferences WithMe remembers over time for {userProfile.name}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowAddModal(true)}
              className="btn-primary py-2.5 px-4 text-xs"
            >
              <Plus className="w-4 h-4" />
              <span>Add Memory</span>
            </button>
            {memories.length > 0 && (
              <button
                onClick={handleClearAll}
                className="btn-secondary py-2.5 px-3 text-xs text-red-400 border-red-500/30 hover:bg-red-500/10"
                title="Wipe memory vault"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Privacy Guarantee Note */}
      <div className="p-4 rounded-2xl bg-emerald-950/40 border border-emerald-500/30 flex items-center gap-3 text-xs text-emerald-200">
        <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
        <span>
          <strong>100% Privacy Control:</strong> All memories are stored locally on your device in encrypted local storage. They are never sold or shared with external third-party advertisers.
        </span>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-col sm:flex-row gap-3 items-center justify-between">
        {/* Category Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 no-scrollbar">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all ${
                selectedCategory === cat
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-500/20'
                  : 'bg-slate-900/60 text-gray-400 hover:text-white border border-white/5'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Search Bar */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search memories..."
            className="glass-input pl-9 py-2 text-xs w-full"
          />
        </div>
      </div>

      {/* Memories Grid */}
      {filteredMemories.length === 0 ? (
        <div className="glass-card p-12 text-center text-gray-400 flex flex-col items-center space-y-3">
          <Lock className="w-10 h-10 text-gray-500 opacity-60" />
          <p className="text-base font-semibold text-gray-300">No memories found</p>
          <p className="text-xs text-gray-500 max-w-sm">
            {searchQuery
              ? 'Try changing your search term or category filter.'
              : 'As you talk to WithMe in chat, useful non-sensitive context will be automatically remembered here!'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredMemories.map((mem) => (
            <div
              key={mem.id}
              className="glass-card p-5 relative group border border-white/10 hover:border-purple-500/40 transition-all flex flex-col justify-between space-y-3"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    {mem.category}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-gray-500 flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {mem.createdAt}
                    </span>
                    <button
                      onClick={() => handleDeleteMemory(mem.id)}
                      className="p-1 rounded text-gray-500 hover:text-red-400 hover:bg-white/10 transition-colors opacity-0 group-hover:opacity-100"
                      title="Forget this memory"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                <p className="text-sm font-medium text-gray-100 leading-relaxed">{mem.content}</p>
              </div>

              <div className="flex items-center gap-1.5 text-[11px] text-gray-400 pt-2 border-t border-white/5">
                <Tag className="w-3 h-3 text-purple-400" />
                <span>{mem.tag}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Memory Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
          <div className="glass-card w-full max-w-md p-6 border border-purple-500/30 space-y-4">
            <h3 className="text-lg font-bold text-white">Add Custom Memory</h3>
            <form onSubmit={handleAddMemory} className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Memory Content</label>
                <textarea
                  value={newContent}
                  onChange={(e) => setNewContent(e.target.value)}
                  placeholder="e.g. Loves playing cozy puzzle games on weekends..."
                  className="glass-input w-full h-24 text-sm resize-none"
                  required
                />
              </div>

              <div>
                <label className="text-xs text-gray-400 block mb-1">Category</label>
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="glass-input w-full text-sm"
                >
                  {categories.filter(c => c !== 'All').map(c => (
                    <option key={c} value={c} className="bg-slate-900 text-white">{c}</option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="btn-secondary py-2 px-4 text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary py-2 px-4 text-xs"
                >
                  Save Memory
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
