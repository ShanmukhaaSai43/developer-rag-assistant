import React from 'react'
import RecipeCard from './RecipeCard'

export default function RaceComparison({ agentData, workflowData, comparison }) {
  if (!agentData && !workflowData) return null

  return (
    <div className="race-grid">
      {/* 1. AGENT COLUMN */}
      {agentData && (
        <div className="glass-panel system-card agent-card">
          <div className="card-header">
            <div className="card-title">
              <div className="system-icon">🤖</div>
              <div>
                <h2>Autonomous ReAct Agent</h2>
                <span>Dynamic Loop · 4 Budgets Active</span>
              </div>
            </div>
            {agentData.passed ? (
              <div className="verdict-banner verdict-pass">
                PASS {comparison?.pass_winner === 'agent' && '🏆'}
              </div>
            ) : (
              <div className="verdict-banner verdict-fail">
                FAIL {agentData.budget_fired ? `(Budget: ${agentData.budget_fired})` : ''}
              </div>
            )}
          </div>

          {/* 4 Numbers for Agent */}
          <div className="metrics-row">
            <div className="metric-box">
              <div className="metric-label">Latency</div>
              <div className="metric-value">{agentData.latency_seconds}s</div>
              {comparison?.latency_winner === 'agent' && <span className="winner-pill">Faster</span>}
            </div>

            <div className="metric-box">
              <div className="metric-label">Total Tokens</div>
              <div className="metric-value">{agentData.total_tokens?.toLocaleString()}</div>
              {comparison?.tokens_winner === 'agent' && <span className="winner-pill">Fewer</span>}
            </div>

            <div className="metric-box">
              <div className="metric-label">Cost</div>
              <div className="metric-value">${agentData.total_cost_usd?.toFixed(5)}</div>
              {comparison?.cost_winner === 'agent' && <span className="winner-pill">Cheaper</span>}
            </div>

            <div className="metric-box">
              <div className="metric-label">Laps Run</div>
              <div className="metric-value">{agentData.laps_completed}</div>
            </div>
          </div>

          {/* Errors if any */}
          {agentData.grade_errors?.length > 0 && (
            <div style={{ color: 'var(--danger-color)', fontSize: '0.8rem', background: 'rgba(244,63,94,0.1)', padding: '0.5rem', borderRadius: '6px' }}>
              {agentData.grade_errors.join('; ')}
            </div>
          )}

          {/* Recipe Card */}
          <RecipeCard recipe={agentData.final_recipe} />
        </div>
      )}

      {/* 2. WORKFLOW COLUMN */}
      {workflowData && (
        <div className="glass-panel system-card workflow-card">
          <div className="card-header">
            <div className="card-title">
              <div className="system-icon">⚙️</div>
              <div>
                <h2>Deterministic Fixed Workflow</h2>
                <span>3 Hardcoded Steps · Zero Loops</span>
              </div>
            </div>
            {workflowData.passed ? (
              <div className="verdict-banner verdict-pass">
                PASS {comparison?.pass_winner === 'workflow' && '🏆'}
              </div>
            ) : (
              <div className="verdict-banner verdict-fail">
                FAIL (Linear Trap)
              </div>
            )}
          </div>

          {/* 4 Numbers for Workflow */}
          <div className="metrics-row">
            <div className="metric-box">
              <div className="metric-label">Latency</div>
              <div className="metric-value">{workflowData.latency_seconds}s</div>
              {comparison?.latency_winner === 'workflow' && <span className="winner-pill">Faster</span>}
            </div>

            <div className="metric-box">
              <div className="metric-label">Total Tokens</div>
              <div className="metric-value">{workflowData.total_tokens?.toLocaleString()}</div>
              {comparison?.tokens_winner === 'workflow' && <span className="winner-pill">Fewer</span>}
            </div>

            <div className="metric-box">
              <div className="metric-label">Cost</div>
              <div className="metric-value">${workflowData.total_cost_usd?.toFixed(5)}</div>
              {comparison?.cost_winner === 'workflow' && <span className="winner-pill">Cheaper</span>}
            </div>

            <div className="metric-box">
              <div className="metric-label">Steps Run</div>
              <div className="metric-value">{workflowData.steps_completed || 3}</div>
            </div>
          </div>

          {/* Errors if any */}
          {workflowData.grade_errors?.length > 0 && (
            <div style={{ color: 'var(--danger-color)', fontSize: '0.8rem', background: 'rgba(244,63,94,0.1)', padding: '0.5rem', borderRadius: '6px' }}>
              {workflowData.grade_errors.join('; ')}
            </div>
          )}

          {/* Recipe Card */}
          <RecipeCard recipe={workflowData.final_recipe} />
        </div>
      )}
    </div>
  )
}
