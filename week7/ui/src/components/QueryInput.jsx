import React from 'react'

export default function QueryInput({
  prompt,
  setPrompt,
  presets,
  selectedPreset,
  onSelectPreset,
  onRunRace,
  onRunAgent,
  onRunWorkflow,
  loading
}) {
  return (
    <div className="glass-panel query-section">
      <div className="section-title">
        <span>⚡ Benchmark Test Cases</span>
      </div>

      <div className="presets-container">
        {presets.map((preset) => (
          <button
            key={preset.id}
            type="button"
            className={`preset-chip ${selectedPreset?.id === preset.id ? 'active' : ''}`}
            onClick={() => onSelectPreset(preset)}
          >
            {preset.type === 'cascade' && (
              <span className="preset-tag-trap">CASCADE TRAP</span>
            )}
            <span>{preset.query.slice(0, 48)}...</span>
          </button>
        ))}
      </div>

      <div className="input-row">
        <input
          type="text"
          className="query-input"
          placeholder="Enter a recipe adaptation request (e.g. Find Classic Peanut Butter Cookies, scale to 4, make it nut-free)..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={loading}
        />
        <div className="button-group">
          <button
            type="button"
            className="btn btn-race"
            onClick={onRunRace}
            disabled={loading || !prompt.trim()}
          >
            {loading ? <span className="spinner" /> : '⚡'} Race Both
          </button>
          <button
            type="button"
            className="btn btn-agent"
            onClick={onRunAgent}
            disabled={loading || !prompt.trim()}
          >
            🤖 Agent
          </button>
          <button
            type="button"
            className="btn btn-workflow"
            onClick={onRunWorkflow}
            disabled={loading || !prompt.trim()}
          >
            ⚙️ Workflow
          </button>
        </div>
      </div>
    </div>
  )
}
