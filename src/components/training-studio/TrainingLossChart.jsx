// WithMe AI Training Studio - Interactive SVG Loss Curve Chart

import React, { useState } from 'react';
import { Activity, Info } from 'lucide-react';

export default function TrainingLossChart({ lossHistory = [], valHistory = [], height = 240 }) {
  const [hoveredPoint, setHoveredPoint] = useState(null);

  if (!lossHistory || lossHistory.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 rounded-2xl bg-slate-950/60 border border-white/5 text-gray-500 text-xs">
        <Activity className="w-8 h-8 mb-2 opacity-40 text-purple-400" />
        <span>No training loss telemetry recorded yet. Start a training job to visualize real loss curves.</span>
      </div>
    );
  }

  const padding = { top: 20, right: 30, bottom: 35, left: 50 };
  const chartWidth = 700;
  const chartHeight = height;

  const innerWidth = chartWidth - padding.left - padding.right;
  const innerHeight = chartHeight - padding.top - padding.bottom;

  const losses = lossHistory.map(d => d.loss);
  const minLoss = Math.max(0, Math.min(...losses) * 0.9);
  const maxLoss = Math.max(...losses) * 1.05;
  const lossRange = Math.max(0.1, maxLoss - minLoss);

  const getX = (index) => {
    if (lossHistory.length <= 1) return padding.left + innerWidth / 2;
    return padding.left + (index / (lossHistory.length - 1)) * innerWidth;
  };

  const getY = (val) => {
    return padding.top + innerHeight - ((val - minLoss) / lossRange) * innerHeight;
  };

  // Generate SVG path for training loss
  const pathD = lossHistory.reduce((acc, curr, idx) => {
    const x = getX(idx);
    const y = getY(curr.loss);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  // Fill area under curve
  const firstX = getX(0);
  const lastX = getX(lossHistory.length - 1);
  const bottomY = padding.top + innerHeight;
  const areaD = `${pathD} L ${lastX} ${bottomY} L ${firstX} ${bottomY} Z`;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 font-semibold text-purple-300">
            <span className="w-2.5 h-2.5 rounded-full bg-purple-400 inline-block"></span>
            Training Loss
          </span>
          {valHistory.length > 0 && (
            <span className="flex items-center gap-1.5 font-semibold text-emerald-300">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 inline-block"></span>
              Validation Loss ({valHistory[valHistory.length - 1]?.val_loss.toFixed(4)})
            </span>
          )}
        </div>
        <span className="text-gray-400 font-mono text-[11px]">
          Latest Loss: <strong className="text-purple-300 font-bold">{lossHistory[lossHistory.length - 1]?.loss.toFixed(4)}</strong>
        </span>
      </div>

      <div className="relative rounded-2xl bg-slate-950/80 p-2 border border-white/10 overflow-hidden shadow-inner">
        <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className="w-full h-auto overflow-visible">
          <defs>
            <linearGradient id="lossGrad" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#a855f7" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#a855f7" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1.0].map((ratio) => {
            const y = padding.top + innerHeight * ratio;
            const lossVal = maxLoss - ratio * lossRange;
            return (
              <g key={ratio}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={padding.left + innerWidth}
                  y2={y}
                  stroke="#334155"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                  opacity="0.4"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  fill="#94a3b8"
                  fontSize="10"
                  textAnchor="end"
                  fontFamily="monospace"
                >
                  {lossVal.toFixed(2)}
                </text>
              </g>
            );
          })}

          {/* Area fill */}
          <path d={areaD} fill="url(#lossGrad)" />

          {/* Training Loss Line */}
          <path d={pathD} fill="none" stroke="#c084fc" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

          {/* Data Points on hover */}
          {lossHistory.map((d, i) => {
            const cx = getX(i);
            const cy = getY(d.loss);
            const isHovered = hoveredPoint && hoveredPoint.index === i;
            return (
              <circle
                key={i}
                cx={cx}
                cy={cy}
                r={isHovered ? 5 : 2}
                fill={isHovered ? "#ffffff" : "#a855f7"}
                stroke="#6b21a8"
                strokeWidth="1.5"
                className="cursor-pointer transition-all"
                onMouseEnter={() => setHoveredPoint({ ...d, index: i, cx, cy })}
                onMouseLeave={() => setHoveredPoint(null)}
              />
            );
          })}

          {/* Validation Markers */}
          {valHistory.map((v, idx) => {
            const vy = getY(v.val_loss);
            // approximate x position across total progress
            const vx = padding.left + (idx / Math.max(1, valHistory.length - 1)) * innerWidth;
            return (
              <g key={`val-${idx}`}>
                <circle cx={vx} cy={vy} r="5" fill="#34d399" stroke="#065f46" strokeWidth="2" />
                <text x={vx} y={vy - 8} fill="#34d399" fontSize="9" textAnchor="middle" fontWeight="bold">
                  {v.val_loss.toFixed(2)}
                </text>
              </g>
            );
          })}

          {/* X-Axis Step Labels */}
          <text x={padding.left} y={chartHeight - 10} fill="#64748b" fontSize="10" fontFamily="monospace">
            Step 1
          </text>
          <text x={padding.left + innerWidth / 2} y={chartHeight - 10} fill="#64748b" fontSize="10" textAnchor="middle" fontFamily="monospace">
            Training Progress (Teacher Forced)
          </text>
          <text x={padding.left + innerWidth} y={chartHeight - 10} fill="#64748b" fontSize="10" textAnchor="end" fontFamily="monospace">
            Step {lossHistory.length}
          </text>
        </svg>

        {/* Hover Tooltip Card */}
        {hoveredPoint && (
          <div
            className="absolute z-20 pointer-events-none p-2 rounded-xl bg-slate-900/95 border border-purple-500/50 shadow-xl text-[11px] space-y-0.5"
            style={{
              left: `${Math.min(85, Math.max(10, (hoveredPoint.cx / chartWidth) * 100))}%`,
              top: '15%'
            }}
          >
            <div className="font-bold text-white flex items-center justify-between gap-2">
              <span>Step {hoveredPoint.step}</span>
              <span className="text-purple-300 font-mono">Epoch {hoveredPoint.epoch}</span>
            </div>
            <div className="text-purple-200">
              Loss: <strong className="font-mono text-white">{hoveredPoint.loss.toFixed(4)}</strong>
            </div>
          </div>
        )}
      </div>

      {/* Transparent Educational Disclosure */}
      <div className="p-3 rounded-xl bg-purple-950/30 border border-purple-500/20 text-[11px] text-gray-300 flex items-start gap-2">
        <Info className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-purple-300">Understanding Loss vs Quality: </span>
          Training loss reflects the model's next-token cross-entropy error on training data. A decreasing curve demonstrates that backpropagation is working. However, lower loss alone does not guarantee human-level conversation.
        </div>
      </div>
    </div>
  );
}
