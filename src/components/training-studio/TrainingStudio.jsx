// WithMe AI Training Studio - Master Studio Platform
// Dedicated interface for training, dataset curation, evaluation, and robot integration.

import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Database,
  Cpu,
  Flame,
  CheckCircle2,
  FolderGit2,
  Sliders,
  Brain,
  MessageSquare,
  Bot,
  Settings,
  RefreshCw,
  Play,
  Square,
  Upload,
  Info,
  Layers,
  Sparkles,
  Send
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { aiCoreClient } from '../../engine/aiCoreClient';
import TrainingLossChart from './TrainingLossChart';
import CompanionAvatar from '../CompanionAvatar';

export default function TrainingStudio({ userProfile: _userProfile }) {
  // Navigation section
  const [activeSection, setActiveSection] = useState('overview');

  // Backend state
  const [health, setHealth] = useState({ status: 'checking' });
  const [hardware, setHardware] = useState(null);
  const [models, setModels] = useState([]);
  const [activeModel, setActiveModel] = useState(null);
  const [datasets, setDatasets] = useState([]);
  const [activeJobId, setActiveJobId] = useState(null);
  const [activeJobData, setActiveJobData] = useState(null);

  // Form states
  const [modelForm, setModelForm] = useState({
    model_name: 'WithMe-Experimental-v2',
    d_model: 64,
    n_layers: 3,
    n_heads: 2,
    ffn_dim: 128,
    max_seq_len: 64,
    dropout: 0.05
  });

  const [trainingForm, setTrainingForm] = useState({
    model_name: 'WithMe-Experimental-v2',
    dataset_id: '',
    epochs: 5,
    batch_size: 2,
    learning_rate: 0.0005
  });

  // Playground state
  const [playgroundMsgs, setPlaygroundMsgs] = useState([
    { role: 'assistant', content: 'Hello! I am ready to converse. Send a message to test this loaded model.' }
  ]);
  const [playgroundInput, setPlaygroundInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [latestInferenceMeta, setLatestInferenceMeta] = useState(null);
  const [temperature, setTemperature] = useState(0.7);

  // Memory & Personality state
  const [memories, setMemories] = useState([]);
  const [newMemoryText, setNewMemoryText] = useState('');
  const [personalityData, setPersonalityData] = useState(null);

  // Robot simulation state
  const [robotStatus, setRobotStatus] = useState(null);
  const [simulatedLog, setSimulatedLog] = useState([]);

  // Evaluation state
  const [evalResults, setEvalResults] = useState(null);
  const [isEvaluating, setIsEvaluating] = useState(false);

  // Notification / Toast
  const [notification, setNotification] = useState(null);

  const showToast = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 3500);
  };

  // Initial Data Fetch
  const refreshAll = async () => {
    try {
      const h = await aiCoreClient.getHealth();
      setHealth(h);

      if (h.status !== 'offline') {
        const [hw, mList, aMod, dList, jList, mems, pers, rStat] = await Promise.all([
          aiCoreClient.getHardware(),
          aiCoreClient.listModels(),
          aiCoreClient.getActiveModel(),
          aiCoreClient.listDatasets(),
          aiCoreClient.listTrainingJobs(),
          aiCoreClient.listMemories(),
          aiCoreClient.getPersonality(),
          aiCoreClient.getRobotStatus()
        ]);

        setHardware(hw);
        setModels(mList);
        setActiveModel(aMod?.details || mList[0]);
        setDatasets(dList);
        setTrainingJobs(jList);
        setMemories(mems);
        setPersonalityData(pers);
        setRobotStatus(rStat?.status);

        if (dList.length > 0 && !trainingForm.dataset_id) {
          const proc = dList.find(d => d.type === 'processed') || dList[0];
          setTrainingForm(prev => ({ ...prev, dataset_id: proc.id }));
        }

        if (jList.length > 0 && !activeJobId) {
          setActiveJobId(jList[0].job_id);
          setActiveJobData(jList[0]);
        }
      }
    } catch (err) {
      console.error('Error refreshing studio data:', err);
    }
  };

  useEffect(() => {
    refreshAll();
  }, []);

  // Poll active training job
  useEffect(() => {
    let interval = null;
    if (activeJobId && activeJobData?.status === 'running') {
      interval = setInterval(async () => {
        try {
          const updated = await aiCoreClient.getTrainingJobStatus(activeJobId);
          setActiveJobData(updated);
          if (updated.status !== 'running') {
            refreshAll();
          }
        } catch {
          // silent error on poll
        }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [activeJobId, activeJobData?.status]);

  // Handlers
  const handleLoadModel = async (modelId) => {
    try {
      await aiCoreClient.loadModel(modelId);
      showToast(`Model '${modelId}' loaded into memory!`);
      confetti({ particleCount: 30, spread: 50 });
      refreshAll();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleStartTraining = async (e) => {
    e.preventDefault();
    try {
      const params = {
        model_name: trainingForm.model_name,
        dataset_id: trainingForm.dataset_id || 'withme_synthetic_foundation',
        epochs: Number(trainingForm.epochs),
        batch_size: Number(trainingForm.batch_size),
        learning_rate: Number(trainingForm.learning_rate),
        d_model: Number(modelForm.d_model),
        n_layers: Number(modelForm.n_layers),
        n_heads: Number(modelForm.n_heads),
        ffn_dim: Number(modelForm.ffn_dim),
        max_seq_len: Number(modelForm.max_seq_len),
        dropout: Number(modelForm.dropout)
      };

      const res = await aiCoreClient.startTrainingJob(params);
      setActiveJobId(res.job_id);
      showToast(`PyTorch Training Job ${res.job_id} launched!`);
      setActiveSection('training');
      confetti({ particleCount: 40 });
      refreshAll();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleStopTraining = async (jobId) => {
    try {
      await aiCoreClient.stopTrainingJob(jobId);
      showToast(`Graceful cancellation sent for job ${jobId}`);
      refreshAll();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleSendPlayground = async (e) => {
    e.preventDefault();
    if (!playgroundInput.trim() || isGenerating) return;

    const userText = playgroundInput.trim();
    const updatedHistory = [...playgroundMsgs, { role: 'user', content: userText }];
    setPlaygroundMsgs(updatedHistory);
    setPlaygroundInput('');
    setIsGenerating(true);

    try {
      const result = await aiCoreClient.sendChat(updatedHistory, { temperature });
      setPlaygroundMsgs([...updatedHistory, { role: 'assistant', content: result.text }]);
      setLatestInferenceMeta(result);
    } catch (err) {
      setPlaygroundMsgs([
        ...updatedHistory,
        { role: 'assistant', content: `[Inference Error]: ${err.message}` }
      ]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSimulateSensor = async (eventType, details) => {
    try {
      const res = await aiCoreClient.simulateSensorEvent(eventType, details);
      setSimulatedLog(prev => [`[${new Date().toLocaleTimeString()}] ${res.resulting_action.toUpperCase()} triggered via ${eventType}`, ...prev.slice(0, 10)]);
      showToast(`Simulated: ${eventType} -> Robot Action: ${res.resulting_action}`);
      const stat = await aiCoreClient.getRobotStatus();
      setRobotStatus(stat?.status);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleRunEvaluation = async () => {
    setIsEvaluating(true);
    try {
      const res = await aiCoreClient.runEvaluation(activeModel?.model_id);
      setEvalResults(res);
      showToast('Evaluation suite completed successfully!');
      confetti({ particleCount: 40 });
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setIsEvaluating(false);
    }
  };

  const handleAddMemory = async (e) => {
    e.preventDefault();
    if (!newMemoryText.trim()) return;
    try {
      await aiCoreClient.createMemory(newMemoryText.trim());
      setNewMemoryText('');
      showToast('User memory stored in SQLite!');
      const mems = await aiCoreClient.listMemories();
      setMemories(mems);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleDeleteMemory = async (id) => {
    try {
      await aiCoreClient.deleteMemory(id);
      showToast('Memory deleted from SQLite');
      const mems = await aiCoreClient.listMemories();
      setMemories(mems);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleToggleMemoryApproval = async (id) => {
    try {
      await aiCoreClient.toggleMemoryApproval(id);
      const mems = await aiCoreClient.listMemories();
      setMemories(mems);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // Nav items definition
  const sidebarItems = [
    { id: 'overview', label: '1. Overview Dashboard', icon: LayoutDashboard },
    { id: 'datasets', label: '2. Dataset Studio', icon: Database },
    { id: 'models', label: '3. Model Lab (PyTorch)', icon: Cpu },
    { id: 'training', label: '4. Training Center', icon: Flame },
    { id: 'evaluation', label: '5. Evaluation Lab', icon: CheckCircle2 },
    { id: 'registry', label: '6. Model Registry', icon: FolderGit2 },
    { id: 'personality', label: '7. Personality Studio', icon: Sliders },
    { id: 'memory', label: '8. Memory Lab (SQLite)', icon: Brain },
    { id: 'playground', label: '9. Live Playground', icon: MessageSquare },
    { id: 'robot', label: '10. Robot Integration', icon: Bot },
    { id: 'system', label: '11. System & Hardware', icon: Settings }
  ];

  return (
    <div className="w-full max-w-7xl mx-auto space-y-4">
      {/* Toast Notification */}
      {notification && (
        <div
          className={`fixed bottom-6 right-6 z-50 p-4 rounded-2xl shadow-2xl border text-xs font-semibold flex items-center gap-2 animate-fadeIn ${
            notification.type === 'error'
              ? 'bg-red-950/90 border-red-500/50 text-red-200'
              : 'bg-slate-900/90 border-purple-500/50 text-purple-200'
          }`}
        >
          <Sparkles className="w-4 h-4 text-purple-400" />
          <span>{notification.msg}</span>
        </div>
      )}

      {/* Main Studio Shell */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Studio Left Sidebar */}
        <aside className="lg:col-span-3 space-y-4">
          <div className="glass-card p-4 border border-purple-500/20 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-white/10">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center">
                  <Flame className="w-4 h-4 text-white" />
                </div>
                <div>
                  <h3 className="text-xs font-bold text-white tracking-wide uppercase">WithMe AI Studio</h3>
                  <p className="text-[10px] text-purple-300">Neural R&D Platform</p>
                </div>
              </div>
              <button
                onClick={refreshAll}
                className="p-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-all"
                title="Refresh studio state"
              >
                <RefreshCw className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Backend Connection Status Badge */}
            <div className="p-2.5 rounded-xl bg-slate-950/80 border border-white/5 flex items-center justify-between text-[11px]">
              <span className="text-gray-400">Backend Server:</span>
              {health.status === 'healthy' ? (
                <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                  FastAPI Online
                </span>
              ) : (
                <span className="text-amber-400 font-semibold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                  Local Engine Active
                </span>
              )}
            </div>

            {/* Navigation Menu */}
            <nav className="space-y-1">
              {sidebarItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeSection === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveSection(item.id)}
                    className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-all text-left ${
                      isActive
                        ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold shadow-md shadow-purple-500/20'
                        : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5 shrink-0" />
                    <span className="truncate">{item.label}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Quick Active Model Status Widget */}
          <div className="glass-card p-4 border border-white/10 space-y-2 text-xs">
            <h4 className="font-bold text-gray-300 text-[11px] uppercase tracking-wider flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-purple-400" /> Active Model
            </h4>
            <div className="p-3 rounded-xl bg-slate-950/70 border border-white/5 space-y-1.5 font-mono text-[11px]">
              <div className="text-purple-300 font-bold truncate">
                {activeModel?.name || 'WithMe Hybrid Engine'}
              </div>
              <div className="text-gray-400 text-[10px]">
                Type: <span className="text-gray-200">{activeModel?.development_type || 'hybrid_local'}</span>
              </div>
              <div className="text-gray-400 text-[10px]">
                Params: <span className="text-emerald-400">{activeModel?.param_count ? `${activeModel.param_count.toLocaleString()}` : '0 (Rule-Based)'}</span>
              </div>
              <div className="text-gray-400 text-[10px]">
                Device: <span className="text-cyan-300">{hardware?.compute_device || 'CPU'}</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Studio Main Workspace Viewport */}
        <main className="lg:col-span-9 space-y-5">
          {/* SECTION 1: OVERVIEW DASHBOARD */}
          {activeSection === 'overview' && (
            <div className="space-y-5">
              <div className="glass-card p-6 border border-purple-500/30 flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    WithMe AI Training Studio 🧠
                  </h2>
                  <p className="text-xs text-gray-400 mt-1">
                    Transparent machine learning platform for training, evaluating, and connecting WithMe's proprietary companion models.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    PyTorch Causal LM
                  </span>
                </div>
              </div>

              {/* Status Metric Cards Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="glass-card p-4 border border-white/10 space-y-1">
                  <span className="text-[10px] text-gray-400 uppercase font-bold tracking-wider">Active Model</span>
                  <div className="text-sm font-bold text-white truncate">{activeModel?.name || 'Hybrid Engine'}</div>
                  <div className="text-[11px] text-purple-300 font-mono">{activeModel?.development_type || 'local'}</div>
                </div>

                <div className="glass-card p-4 border border-white/10 space-y-1">
                  <span className="text-[10px] text-gray-400 uppercase font-bold tracking-wider">Parameters</span>
                  <div className="text-sm font-bold text-emerald-400 font-mono">
                    {activeModel?.param_count ? activeModel.param_count.toLocaleString() : 'Heuristic'}
                  </div>
                  <div className="text-[11px] text-gray-400">Random Init Trained</div>
                </div>

                <div className="glass-card p-4 border border-white/10 space-y-1">
                  <span className="text-[10px] text-gray-400 uppercase font-bold tracking-wider">Compute Hardware</span>
                  <div className="text-sm font-bold text-cyan-300 font-mono">
                    {hardware?.compute_device || 'CPU'} ({hardware?.cpu_count_physical || 4} Physical Cores)
                  </div>
                  <div className="text-[11px] text-gray-400">{hardware?.ram_available_gb} GB RAM Free</div>
                </div>

                <div className="glass-card p-4 border border-white/10 space-y-1">
                  <span className="text-[10px] text-gray-400 uppercase font-bold tracking-wider">Registered Datasets</span>
                  <div className="text-sm font-bold text-amber-300 font-mono">{datasets.length} Datasets</div>
                  <div className="text-[11px] text-gray-400">JSONL / JSON / CSV</div>
                </div>
              </div>

              {/* Latest Real Training Loss Curve */}
              {activeJobData?.loss_history && activeJobData.loss_history.length > 0 && (
                <div className="glass-card p-6 border border-white/10 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-white flex items-center gap-2">
                      <Flame className="w-4 h-4 text-purple-400" />
                      <span>Latest PyTorch Training Job ({activeJobData.model_name})</span>
                    </h3>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-950 text-purple-300 border border-purple-500/30">
                      Status: {activeJobData.status.toUpperCase()}
                    </span>
                  </div>
                  <TrainingLossChart
                    lossHistory={activeJobData.loss_history}
                    valHistory={activeJobData.val_history || []}
                  />
                </div>
              )}
            </div>
          )}

          {/* SECTION 2: DATASET STUDIO */}
          {activeSection === 'datasets' && (
            <div className="glass-card p-6 border border-white/10 space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-white/10">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Database className="w-5 h-5 text-purple-400" />
                    <span>Dataset Studio & Preprocessing Pipeline</span>
                  </h3>
                  <p className="text-xs text-gray-400">
                    Import, validate conversational turns, prevent data leakage, and split into train/validation sets.
                  </p>
                </div>
              </div>

              {/* Upload Card */}
              <div className="p-5 rounded-2xl bg-slate-950/70 border border-dashed border-purple-500/40 text-center space-y-3">
                <Upload className="w-8 h-8 text-purple-400 mx-auto" />
                <div>
                  <h4 className="text-sm font-bold text-white">Import Conversational Dataset</h4>
                  <p className="text-xs text-gray-400">Supports JSONL, JSON, CSV, and plain TXT format</p>
                </div>
                <input
                  type="file"
                  accept=".jsonl,.json,.csv,.txt"
                  id="dataset-upload"
                  className="hidden"
                  onChange={async (e) => {
                    const f = e.target.files?.[0];
                    if (f) {
                      try {
                        const res = await aiCoreClient.uploadDataset(f);
                        showToast(`Uploaded ${res.filename}! Preparing dataset...`);
                        await aiCoreClient.prepareDataset(f.name.replace(/\.[^/.]+$/, ""), f.name);
                        refreshAll();
                      } catch (err) {
                        showToast(err.message, 'error');
                      }
                    }
                  }}
                />
                <label
                  htmlFor="dataset-upload"
                  className="btn-primary py-2 px-5 text-xs inline-flex items-center gap-1.5 cursor-pointer"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>Choose File to Upload</span>
                </label>
              </div>

              {/* Datasets Table */}
              <div className="space-y-3">
                <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider">Available Datasets</h4>
                <div className="divide-y divide-white/5 rounded-2xl bg-slate-950/80 border border-white/10 overflow-hidden">
                  {datasets.map((d) => (
                    <div key={d.id} className="p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-white">{d.name}</span>
                          <span className="text-[10px] px-2 py-0.5 rounded bg-white/5 text-purple-300 font-mono">
                            {d.format.toUpperCase()}
                          </span>
                          {d.is_demo && (
                            <span className="text-[10px] px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                              Synthetic Demo
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-400 mt-0.5 font-mono">
                          {d.conversation_count || d.example_count} Conversations • {d.total_messages || 0} Messages
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {d.type === 'raw' ? (
                          <button
                            onClick={async () => {
                              try {
                                await aiCoreClient.prepareDataset(d.id, d.name);
                                showToast(`Dataset '${d.name}' normalized and split!`);
                                refreshAll();
                              } catch (err) {
                                showToast(err.message, 'error');
                              }
                            }}
                            className="btn-secondary py-1.5 px-3 text-xs"
                          >
                            Normalize & Split
                          </button>
                        ) : (
                          <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Ready for Training
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* SECTION 3: MODEL LAB */}
          {activeSection === 'models' && (
            <div className="glass-card p-6 border border-white/10 space-y-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Cpu className="w-5 h-5 text-purple-400" />
                  <span>Model Lab: Architecture & Hyperparameter Studio</span>
                </h3>
                <p className="text-xs text-gray-400">
                  Configure small Transformer architecture dimensions from scratch.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-2xl bg-slate-950/70 border border-white/10 space-y-3">
                  <label className="text-xs text-gray-400 block">Model Name</label>
                  <input
                    type="text"
                    value={modelForm.model_name}
                    onChange={(e) => setModelForm({ ...modelForm, model_name: e.target.value })}
                    className="glass-input w-full text-xs"
                  />

                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <div>
                      <label className="text-[11px] text-gray-400 block mb-1">Embedding Dim (d_model)</label>
                      <select
                        value={modelForm.d_model}
                        onChange={(e) => setModelForm({ ...modelForm, d_model: Number(e.target.value) })}
                        className="glass-input w-full text-xs"
                      >
                        <option value={32}>32 (Tiny Experimental)</option>
                        <option value={64}>64 (Recommended Small)</option>
                        <option value={128}>128 (Standard Small)</option>
                        <option value={256}>256 (Heavy)</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-[11px] text-gray-400 block mb-1">Transformer Layers</label>
                      <select
                        value={modelForm.n_layers}
                        onChange={(e) => setModelForm({ ...modelForm, n_layers: Number(e.target.value) })}
                        className="glass-input w-full text-xs"
                      >
                        <option value={2}>2 Layers</option>
                        <option value={3}>3 Layers</option>
                        <option value={4}>4 Layers</option>
                        <option value={6}>6 Layers</option>
                      </select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-2">
                    <div>
                      <label className="text-[11px] text-gray-400 block mb-1">Attention Heads</label>
                      <select
                        value={modelForm.n_heads}
                        onChange={(e) => setModelForm({ ...modelForm, n_heads: Number(e.target.value) })}
                        className="glass-input w-full text-xs"
                      >
                        <option value={2}>2 Heads</option>
                        <option value={4}>4 Heads</option>
                      </select>
                    </div>

                    <div>
                      <label className="text-[11px] text-gray-400 block mb-1">Feed-Forward Dim</label>
                      <select
                        value={modelForm.ffn_dim}
                        onChange={(e) => setModelForm({ ...modelForm, ffn_dim: Number(e.target.value) })}
                        className="glass-input w-full text-xs"
                      >
                        <option value={64}>64</option>
                        <option value={128}>128</option>
                        <option value={256}>256</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Architecture Estimate Card */}
                <div className="p-4 rounded-2xl bg-purple-950/20 border border-purple-500/30 space-y-3 flex flex-col justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-purple-300 uppercase tracking-wider flex items-center gap-1.5">
                      <Layers className="w-4 h-4" /> Architecture Parameter Budget
                    </h4>
                    <p className="text-[11px] text-gray-400 mt-1">
                      Calculated parameter footprint for CPU training:
                    </p>
                    <div className="mt-4 p-4 rounded-xl bg-slate-950/80 border border-white/5 space-y-1 font-mono text-xs">
                      <div>Estimated Trainable Weights: <strong className="text-emerald-400">~120,000 - 150,000</strong></div>
                      <div>Target Hardware: <strong className="text-cyan-300">Intel Core CPU (16 GB RAM)</strong></div>
                      <div>Expected VRAM Required: <strong className="text-gray-300">&lt; 200 MB RAM</strong></div>
                      <div>Causal Mask: <strong className="text-purple-300">Lower-Triangular</strong></div>
                    </div>
                  </div>
                  <button
                    onClick={() => {
                      setTrainingForm(prev => ({ ...prev, model_name: modelForm.model_name }));
                      setActiveSection('training');
                    }}
                    className="w-full btn-primary py-2.5 text-xs flex items-center justify-center gap-1.5"
                  >
                    <span>Proceed to Training Center</span>
                    <Play className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 4: TRAINING CENTER */}
          {activeSection === 'training' && (
            <div className="glass-card p-6 border border-white/10 space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-white/10">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Flame className="w-5 h-5 text-purple-400" />
                    <span>Training Center: PyTorch Execution Engine</span>
                  </h3>
                  <p className="text-xs text-gray-400">
                    Real asynchronous model training with live telemetry, AdamW optimizer, and checkpoint saving.
                  </p>
                </div>
              </div>

              {/* Start Training Form */}
              <form onSubmit={handleStartTraining} className="p-4 rounded-2xl bg-slate-950/70 border border-white/10 grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Model Name</label>
                  <input
                    type="text"
                    value={trainingForm.model_name}
                    onChange={(e) => setTrainingForm({ ...trainingForm, model_name: e.target.value })}
                    className="glass-input w-full text-xs"
                    required
                  />
                </div>

                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Dataset</label>
                  <select
                    value={trainingForm.dataset_id}
                    onChange={(e) => setTrainingForm({ ...trainingForm, dataset_id: e.target.value })}
                    className="glass-input w-full text-xs"
                  >
                    {datasets.map(d => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-[11px] text-gray-400 block mb-1">Epochs</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={trainingForm.epochs}
                    onChange={(e) => setTrainingForm({ ...trainingForm, epochs: Number(e.target.value) })}
                    className="glass-input w-full text-xs"
                  />
                </div>

                <div>
                  <button
                    type="submit"
                    disabled={activeJobData?.status === 'running'}
                    className="w-full btn-primary py-2.5 text-xs flex items-center justify-center gap-1.5 disabled:opacity-50"
                  >
                    <Play className="w-3.5 h-3.5" />
                    <span>Launch Training Job</span>
                  </button>
                </div>
              </form>

              {/* Active Training Job Telemetry Card */}
              {activeJobData && (
                <div className="p-5 rounded-2xl bg-slate-950/90 border border-purple-500/30 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-bold text-white flex items-center gap-2">
                        <span>Job ID: {activeJobData.job_id}</span>
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                          activeJobData.status === 'running'
                            ? 'bg-purple-600/30 text-purple-300 border border-purple-400/50 animate-pulse'
                            : 'bg-emerald-950/50 text-emerald-400 border border-emerald-500/30'
                        }`}>
                          {activeJobData.status}
                        </span>
                      </h4>
                      <p className="text-xs text-gray-400 font-mono mt-0.5">
                        Model: {activeJobData.model_name} • Epoch {activeJobData.current_epoch}/{activeJobData.total_epochs} • Step {activeJobData.current_step}/{activeJobData.total_steps}
                      </p>
                    </div>

                    {activeJobData.status === 'running' && (
                      <button
                        onClick={() => handleStopTraining(activeJobData.job_id)}
                        className="btn-secondary py-1.5 px-3 text-xs text-red-300 border-red-500/30 hover:bg-red-950/50 flex items-center gap-1"
                      >
                        <Square className="w-3.5 h-3.5" />
                        <span>Stop Job</span>
                      </button>
                    )}
                  </div>

                  {/* Real Loss Curves Chart */}
                  <TrainingLossChart
                    lossHistory={activeJobData.loss_history}
                    valHistory={activeJobData.val_history || []}
                  />

                  {/* Live Console Output */}
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Live Training Logs</span>
                    <div className="p-3 rounded-xl bg-black font-mono text-[11px] text-gray-300 space-y-1 h-32 overflow-y-auto border border-white/5">
                      {activeJobData.logs?.map((l, i) => (
                        <div key={i} className="leading-tight">{l}</div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* SECTION 5: EVALUATION LAB */}
          {activeSection === 'evaluation' && (
            <div className="glass-card p-6 border border-white/10 space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-white/10">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-purple-400" />
                    <span>Evaluation Lab: Benchmark Suite</span>
                  </h3>
                  <p className="text-xs text-gray-400">
                    Run transparent test cases across Emotional Support, Academic Stress, Casual Play, and Safety.
                  </p>
                </div>
                <button
                  onClick={handleRunEvaluation}
                  disabled={isEvaluating}
                  className="btn-primary py-2 px-4 text-xs flex items-center gap-1.5"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>{isEvaluating ? 'Evaluating...' : 'Run Benchmark Suite'}</span>
                </button>
              </div>

              {evalResults ? (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3 font-mono text-xs">
                    <div className="p-3 rounded-xl bg-slate-950/80 border border-white/5">
                      <span className="text-gray-400 text-[10px] block">Average Latency</span>
                      <strong className="text-cyan-300">{evalResults.average_latency_ms} ms</strong>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950/80 border border-white/5">
                      <span className="text-gray-400 text-[10px] block">Test Cases Run</span>
                      <strong className="text-purple-300">{evalResults.test_count} Prompts</strong>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950/80 border border-white/5">
                      <span className="text-gray-400 text-[10px] block">Model Evaluated</span>
                      <strong className="text-emerald-400 truncate block">{evalResults.model_id}</strong>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {evalResults.results.map((r, i) => (
                      <div key={i} className="p-4 rounded-xl bg-slate-950/80 border border-white/10 space-y-2 text-xs">
                        <div className="flex items-center justify-between font-semibold">
                          <span className="text-purple-300 uppercase tracking-wider text-[10px] font-mono">[{r.category}]</span>
                          <span className="text-gray-400 font-mono text-[11px]">{r.latency_ms} ms</span>
                        </div>
                        <div className="text-gray-300 font-mono">Prompt: "{r.prompt}"</div>
                        <div className="p-2.5 rounded-lg bg-white/5 text-gray-200">
                          <strong>Model Output:</strong> {r.actual_output}
                        </div>
                        <div className="text-[11px] text-gray-500 italic">
                          Expected: {r.expected_behavior}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="p-8 rounded-2xl bg-slate-950/60 border border-white/5 text-center text-xs text-gray-500">
                  Click "Run Benchmark Suite" above to test the active model against standardized prompts.
                </div>
              )}
            </div>
          )}

          {/* SECTION 6: MODEL REGISTRY */}
          {activeSection === 'registry' && (
            <div className="glass-card p-6 border border-white/10 space-y-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <FolderGit2 className="w-5 h-5 text-purple-400" />
                  <span>Model Registry & Checkpoint Catalog</span>
                </h3>
                <p className="text-xs text-gray-400">
                  Manage trained model checkpoints, load active models, and compare versions.
                </p>
              </div>

              <div className="space-y-3">
                {models.map((m) => {
                  const isActive = activeModel?.model_id === m.model_id;
                  return (
                    <div
                      key={m.model_id}
                      className={`p-4 rounded-2xl border transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
                        isActive
                          ? 'bg-purple-950/40 border-purple-500/50 shadow-lg shadow-purple-500/20'
                          : 'bg-slate-950/70 border-white/5 hover:border-white/20'
                      }`}
                    >
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-bold text-white">{m.name}</h4>
                          {isActive && (
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">
                              ACTIVE FOR INFERENCE
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-400 font-mono">
                          ID: {m.model_id} • Arch: {m.architecture} • Weights: {m.param_count ? m.param_count.toLocaleString() : 'N/A'} • Size: {m.size_mb} MB
                        </p>
                      </div>

                      <div className="flex items-center gap-2">
                        {!isActive ? (
                          <button
                            onClick={() => handleLoadModel(m.model_id)}
                            className="btn-primary py-1.5 px-4 text-xs"
                          >
                            Load into Engine
                          </button>
                        ) : (
                          <span className="text-xs text-emerald-400 font-semibold flex items-center gap-1">
                            <CheckCircle2 className="w-4 h-4" /> Loaded
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* SECTION 7: PERSONALITY STUDIO */}
          {activeSection === 'personality' && (
            <div className="glass-card p-6 border border-white/10 space-y-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Sliders className="w-5 h-5 text-purple-400" />
                  <span>Personality Studio & Behavioral Steering</span>
                </h3>
                <p className="text-xs text-gray-400">
                  Configure warmth, playfulness, energy, and style.
                </p>
              </div>

              {/* Transparent Disclosure */}
              <div className="p-3.5 rounded-xl bg-purple-950/40 border border-purple-500/30 text-xs text-purple-200 flex items-start gap-2">
                <Info className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-white">Inference-Time Context Steering: </strong>
                  Personality sliders configure runtime prompt directives and sampling temperature. They do not alter the saved neural weights of the underlying checkpoint.
                </div>
              </div>

              {/* Presets Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                {['friendly', 'playful', 'calm', 'energetic', 'quiet'].map((pKey) => {
                  const isCur = personalityData?.active?.active_preset === pKey;
                  return (
                    <button
                      key={pKey}
                      onClick={async () => {
                        const res = await aiCoreClient.updatePersonality(pKey);
                        setPersonalityData(res);
                        showToast(`Switched personality to ${pKey.toUpperCase()}`);
                      }}
                      className={`p-3 rounded-xl border text-center transition-all text-xs font-semibold capitalize ${
                        isCur
                          ? 'bg-purple-600/30 border-purple-400 text-white shadow-md'
                          : 'bg-slate-900/60 border-white/5 text-gray-400 hover:text-white'
                      }`}
                    >
                      {pKey}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* SECTION 8: MEMORY LAB */}
          {activeSection === 'memory' && (
            <div className="glass-card p-6 border border-white/10 space-y-6">
              <div className="flex items-center justify-between pb-4 border-b border-white/10">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Brain className="w-5 h-5 text-purple-400" />
                    <span>Memory Lab: SQLite Persistent Storage</span>
                  </h3>
                  <p className="text-xs text-gray-400">
                    Explicit, user-controlled memory vault separate from neural weights.
                  </p>
                </div>
              </div>

              {/* Add Memory Form */}
              <form onSubmit={handleAddMemory} className="flex gap-2">
                <input
                  type="text"
                  value={newMemoryText}
                  onChange={(e) => setNewMemoryText(e.target.value)}
                  placeholder="Record an approved memory (e.g. 'Prefers calm check-ins before exams')..."
                  className="glass-input flex-1 text-xs"
                />
                <button type="submit" className="btn-primary py-2 px-4 text-xs">
                  Save to SQLite
                </button>
              </form>

              {/* Memories List */}
              <div className="space-y-2">
                {memories.map((m) => (
                  <div key={m.id} className="p-3.5 rounded-xl bg-slate-950/80 border border-white/5 flex items-center justify-between text-xs">
                    <div className="space-y-0.5">
                      <div className="text-white font-medium">{m.content}</div>
                      <div className="text-[10px] text-gray-500 font-mono">
                        Category: {m.category} • Tag: {m.tag} • ID: {m.id}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleToggleMemoryApproval(m.id)}
                        className={`px-2 py-1 rounded text-[10px] font-mono font-bold ${
                          m.user_approved ? 'bg-emerald-950 text-emerald-300' : 'bg-red-950 text-red-300'
                        }`}
                      >
                        {m.user_approved ? 'Approved' : 'Disabled'}
                      </button>
                      <button
                        onClick={() => handleDeleteMemory(m.id)}
                        className="text-gray-500 hover:text-red-400 p-1"
                        title="Delete memory"
                      >
                        ✕
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* SECTION 9: LIVE PLAYGROUND */}
          {activeSection === 'playground' && (
            <div className="glass-card p-6 border border-white/10 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-white/10">
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-purple-400" />
                    <span>Inference Playground</span>
                  </h3>
                  <p className="text-xs text-gray-400">
                    Chat directly with the active model. Output is produced by genuine autoregressive generation.
                  </p>
                </div>
                <div className="flex items-center gap-4 text-right">
                  <div className="flex items-center gap-2 bg-slate-900/80 px-3 py-1.5 rounded-xl border border-white/5">
                    <span className="text-[11px] text-gray-400">Temp:</span>
                    <input
                      type="range"
                      min="0.1"
                      max="1.5"
                      step="0.1"
                      value={temperature}
                      onChange={(e) => setTemperature(parseFloat(e.target.value))}
                      className="w-20 accent-purple-500 cursor-pointer"
                    />
                    <span className="text-purple-300 font-mono text-[11px] w-6">{temperature.toFixed(1)}</span>
                  </div>
                  <div>
                    <span className="text-[10px] text-purple-300 font-mono block">
                      Source: {activeModel?.development_type === 'from_scratch' ? 'Local Checkpoint' : 'Hybrid Engine'}
                    </span>
                    <span className="text-[10px] text-gray-500 font-mono">
                      Model: {activeModel?.name}
                    </span>
                  </div>
                </div>
              </div>

              {/* Chat Viewport */}
              <div className="p-4 rounded-2xl bg-slate-950/90 border border-white/10 h-72 overflow-y-auto space-y-3">
                {playgroundMsgs.map((m, idx) => (
                  <div
                    key={idx}
                    className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    <span className="text-[10px] text-gray-500 font-mono mb-0.5">
                      {m.role === 'user' ? 'You' : 'WithMe AI'}
                    </span>
                    <div
                      className={`p-3 rounded-2xl text-xs max-w-[80%] ${
                        m.role === 'user'
                          ? 'bg-purple-600 text-white'
                          : 'bg-slate-900 border border-white/10 text-gray-200'
                      }`}
                    >
                      {m.content}
                    </div>
                  </div>
                ))}
                {isGenerating && (
                  <div className="text-xs text-purple-400 font-mono animate-pulse">
                    WithMe is generating next tokens...
                  </div>
                )}
              </div>

              {/* Telemetry info */}
              {latestInferenceMeta && (
                <div className="p-2.5 rounded-xl bg-purple-950/20 border border-purple-500/20 text-[10px] font-mono text-gray-400 flex items-center justify-between">
                  <span>Latency: <strong className="text-cyan-300">{latestInferenceMeta.latency_ms} ms</strong></span>
                  <span>Tokens/sec: <strong className="text-emerald-400">{latestInferenceMeta.tokens_per_second}</strong></span>
                  <span>Emotion: <strong className="text-purple-300">{latestInferenceMeta.emotion}</strong></span>
                  <span>Robot Action: <strong className="text-amber-300">{latestInferenceMeta.robot_action}</strong></span>
                </div>
              )}

              {/* Chat input form */}
              <form onSubmit={handleSendPlayground} className="flex gap-2">
                <input
                  type="text"
                  value={playgroundInput}
                  onChange={(e) => setPlaygroundInput(e.target.value)}
                  placeholder="Send a test prompt..."
                  className="glass-input flex-1 text-xs"
                />
                <button type="submit" disabled={isGenerating} className="btn-primary py-2 px-5 text-xs">
                  <Send className="w-3.5 h-3.5" />
                </button>
              </form>
            </div>
          )}

          {/* SECTION 10: ROBOT INTEGRATION */}
          {activeSection === 'robot' && (
            <div className="glass-card p-6 border border-white/10 space-y-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Bot className="w-5 h-5 text-purple-400" />
                  <span>Robot Integration & Sensory Simulation Layer</span>
                </h3>
                <p className="text-xs text-gray-400">
                  Hardware-agnostic action execution layer. Sensor events are explicitly simulated in software.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Robot Avatar Viewport */}
                <div className="p-6 rounded-2xl bg-slate-950/80 border border-white/10 flex flex-col items-center justify-center space-y-4">
                  <CompanionAvatar
                    emotionState={robotStatus?.emotion || 'happy'}
                    isSpeaking={robotStatus?.interaction_state === 'speaking'}
                    size="lg"
                  />
                  <div className="text-center font-mono text-xs">
                    <div className="text-purple-300 font-bold">Action: {robotStatus?.active_action || 'idle'}</div>
                    <div className="text-gray-500 text-[10px]">State: {robotStatus?.interaction_state || 'idle'}</div>
                  </div>
                </div>

                {/* Simulated Sensor Event Triggers */}
                <div className="p-5 rounded-2xl bg-slate-950/80 border border-white/10 space-y-3">
                  <h4 className="text-xs font-bold text-gray-300 uppercase tracking-wider">
                    Simulate Sensory Events
                  </h4>
                  <p className="text-[11px] text-gray-400">
                    Trigger simulated hardware events to test action allowlist validation:
                  </p>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <button
                      onClick={() => handleSimulateSensor('person_detected', { position: 'left' })}
                      className="btn-secondary py-2 px-3 text-[11px] text-left"
                    >
                      👤 Person on Left
                    </button>
                    <button
                      onClick={() => handleSimulateSensor('person_detected', { position: 'right' })}
                      className="btn-secondary py-2 px-3 text-[11px] text-left"
                    >
                      👤 Person on Right
                    </button>
                    <button
                      onClick={() => handleSimulateSensor('petting_gesture', { intensity: 'high' })}
                      className="btn-secondary py-2 px-3 text-[11px] text-left"
                    >
                      🖐️ Petting Gesture
                    </button>
                    <button
                      onClick={() => handleSimulateSensor('sleep_timer', { duration_min: 30 })}
                      className="btn-secondary py-2 px-3 text-[11px] text-left"
                    >
                      💤 Sleep Command
                    </button>
                  </div>

                  {/* Simulated Telemetry Log */}
                  <div className="pt-2">
                    <span className="text-[10px] text-gray-500 font-mono block mb-1">Simulated Sensor Log:</span>
                    <div className="p-2.5 rounded-xl bg-black font-mono text-[10px] text-gray-400 space-y-1 h-20 overflow-y-auto">
                      {simulatedLog.map((log, idx) => (
                        <div key={idx}>{log}</div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* SECTION 11: SYSTEM & HARDWARE */}
          {activeSection === 'system' && (
            <div className="glass-card p-6 border border-white/10 space-y-6">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Settings className="w-5 h-5 text-purple-400" />
                  <span>Host Compute & Hardware Telemetry</span>
                </h3>
                <p className="text-xs text-gray-400">
                  Real physical specifications of the current machine.
                </p>
              </div>

              {hardware && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 font-mono text-xs">
                  <div className="p-4 rounded-xl bg-slate-950/80 border border-white/5 space-y-1">
                    <span className="text-[10px] text-gray-500 uppercase">Operating System</span>
                    <div className="text-white font-bold">{hardware.platform} {hardware.platform_release}</div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950/80 border border-white/5 space-y-1">
                    <span className="text-[10px] text-gray-500 uppercase">Processor</span>
                    <div className="text-white font-bold truncate">{hardware.processor}</div>
                    <div className="text-gray-400 text-[10px]">{hardware.cpu_count_physical} Cores / {hardware.cpu_count_logical} Threads</div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950/80 border border-white/5 space-y-1">
                    <span className="text-[10px] text-gray-500 uppercase">Memory (RAM)</span>
                    <div className="text-emerald-400 font-bold">{hardware.ram_available_gb} GB Free / {hardware.ram_total_gb} GB Total</div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950/80 border border-white/5 space-y-1">
                    <span className="text-[10px] text-gray-500 uppercase">Storage (Disk)</span>
                    <div className="text-cyan-300 font-bold">{hardware.disk_free_gb} GB Free / {hardware.disk_total_gb} GB Total</div>
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
