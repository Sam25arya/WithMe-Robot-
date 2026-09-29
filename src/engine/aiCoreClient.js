// WithMe AI Core API Client - Direct communication with FastAPI Backend

const API_BASE_URL = 'http://127.0.0.1:8000/api';

export const aiCoreClient = {
  baseUrl: API_BASE_URL,

  async getHealth() {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      if (!res.ok) throw new Error('Health check failed');
      return await res.json();
    } catch (err) {
      return { status: 'offline', error: err.message };
    }
  },

  async getHardware() {
    const res = await fetch(`${API_BASE_URL}/hardware`);
    if (!res.ok) throw new Error('Hardware fetch failed');
    return await res.json();
  },

  // Datasets
  async listDatasets() {
    const res = await fetch(`${API_BASE_URL}/datasets`);
    return await res.json();
  },

  async uploadDataset(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE_URL}/datasets/upload`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }
    return await res.json();
  },

  async prepareDataset(datasetId, datasetName, valRatio = 0.2, seed = 42) {
    const formData = new FormData();
    formData.append('dataset_name', datasetName);
    formData.append('val_ratio', String(valRatio));
    formData.append('seed', String(seed));

    const res = await fetch(`${API_BASE_URL}/datasets/${datasetId}/prepare`, {
      method: 'POST',
      body: formData
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Prepare failed');
    }
    return await res.json();
  },

  // Models & Registry
  async listModels() {
    const res = await fetch(`${API_BASE_URL}/models`);
    return await res.json();
  },

  async getActiveModel() {
    const res = await fetch(`${API_BASE_URL}/models/active`);
    return await res.json();
  },

  async loadModel(modelId) {
    const res = await fetch(`${API_BASE_URL}/models/load`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model_id: modelId })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to load model');
    }
    return await res.json();
  },

  // Training
  async startTrainingJob(params) {
    const res = await fetch(`${API_BASE_URL}/training/jobs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to start job');
    }
    return await res.json();
  },

  async listTrainingJobs() {
    const res = await fetch(`${API_BASE_URL}/training/jobs`);
    return await res.json();
  },

  async getTrainingJobStatus(jobId) {
    const res = await fetch(`${API_BASE_URL}/training/jobs/${jobId}`);
    if (!res.ok) throw new Error('Job not found');
    return await res.json();
  },

  async stopTrainingJob(jobId) {
    const res = await fetch(`${API_BASE_URL}/training/jobs/${jobId}/stop`, { method: 'POST' });
    return await res.json();
  },

  // Chat / Playground
  async sendChat(messages, options = {}) {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        messages,
        temperature: options.temperature ?? 0.7,
        top_k: options.top_k ?? 40,
        top_p: options.top_p ?? 0.9,
        max_new_tokens: options.max_new_tokens ?? 45,
        include_memories: options.include_memories ?? true
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Inference error');
    }
    return await res.json();
  },

  // Memories
  async listMemories(category) {
    const url = category ? `${API_BASE_URL}/memories?category=${encodeURIComponent(category)}` : `${API_BASE_URL}/memories`;
    const res = await fetch(url);
    return await res.json();
  },

  async createMemory(content, category = 'General', tag = 'Custom') {
    const res = await fetch(`${API_BASE_URL}/memories`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, category, tag, user_approved: true })
    });
    return await res.json();
  },

  async deleteMemory(memoryId) {
    const res = await fetch(`${API_BASE_URL}/memories/${memoryId}`, { method: 'DELETE' });
    return await res.json();
  },

  async toggleMemoryApproval(memoryId) {
    const res = await fetch(`${API_BASE_URL}/memories/${memoryId}/toggle-approval`, { method: 'POST' });
    return await res.json();
  },

  // Personality
  async getPersonality() {
    const res = await fetch(`${API_BASE_URL}/personality`);
    return await res.json();
  },

  async updatePersonality(presetId, customOverrides) {
    const res = await fetch(`${API_BASE_URL}/personality`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ preset_id: presetId, custom_overrides: customOverrides })
    });
    return await res.json();
  },

  // Robot State & Simulation
  async getRobotStatus() {
    const res = await fetch(`${API_BASE_URL}/robot/status`);
    return await res.json();
  },

  async triggerRobotAction(action, emotion = 'happy', interactionState = 'idle') {
    const res = await fetch(`${API_BASE_URL}/robot/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ robot_action: action, emotion, interaction_state: interactionState })
    });
    return await res.json();
  },

  async simulateSensorEvent(eventType, details = {}) {
    const res = await fetch(`${API_BASE_URL}/robot/simulate-sensor`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ event_type: eventType, details })
    });
    return await res.json();
  },

  // Evaluation
  async runEvaluation(modelId) {
    const url = modelId ? `${API_BASE_URL}/evaluation/run?model_id=${encodeURIComponent(modelId)}` : `${API_BASE_URL}/evaluation/run`;
    const res = await fetch(url, { method: 'POST' });
    return await res.json();
  },

  async listEvaluations() {
    const res = await fetch(`${API_BASE_URL}/evaluation/results`);
    return await res.json();
  }
};
