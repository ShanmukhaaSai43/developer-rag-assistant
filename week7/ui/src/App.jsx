import React, { useState, useEffect } from 'react'
import Header from './components/Header'
import QueryInput from './components/QueryInput'
import RaceComparison from './components/RaceComparison'

export default function App() {
  const [prompt, setPrompt] = useState('')
  const [presets, setPresets] = useState([])
  const [selectedPreset, setSelectedPreset] = useState(null)
  const [loading, setLoading] = useState(false)
  const [backendConnected, setBackendConnected] = useState(false)
  const [agentData, setAgentData] = useState(null)
  const [workflowData, setWorkflowData] = useState(null)
  const [comparison, setComparison] = useState(null)
  const [errorMsg, setErrorMsg] = useState(null)

  // Check health and load benchmark presets
  useEffect(() => {
    async function init() {
      try {
        const healthRes = await fetch('/api/health')
        if (healthRes.ok) setBackendConnected(true)

        const presetsRes = await fetch('/api/presets')
        if (presetsRes.ok) {
          const data = await presetsRes.json()
          setPresets(data.presets || [])
          if (data.presets && data.presets.length > 0) {
            handleSelectPreset(data.presets[0])
          }
        }
      } catch (err) {
        console.warn('Backend not detected on /api, trying direct port 8000...', err)
        try {
          const directRes = await fetch('http://127.0.0.1:8000/api/presets')
          if (directRes.ok) {
            setBackendConnected(true)
            const data = await directRes.json()
            setPresets(data.presets || [])
            if (data.presets?.length > 0) {
              handleSelectPreset(data.presets[0])
            }
          }
        } catch (e) {
          setBackendConnected(false)
        }
      }
    }
    init()
  }, [])

  const handleSelectPreset = (preset) => {
    setSelectedPreset(preset)
    setPrompt(preset.query)
    setErrorMsg(null)
  }

  const getApiUrl = (endpoint) => {
    return `/api/${endpoint}`
  }

  const handleRunRace = async () => {
    setLoading(true)
    setErrorMsg(null)
    setAgentData(null)
    setWorkflowData(null)
    setComparison(null)

    try {
      const res = await fetch(getApiUrl('race'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompt,
          preset_id: selectedPreset?.id,
          target_servings: selectedPreset?.target_servings || 4,
          avoid_allergens: selectedPreset?.avoid_allergens || [],
          request_type: selectedPreset?.type || 'standard',
          intermediate_allergen_sub: selectedPreset?.intermediate_allergen_sub || '',
          terminal_safe_sub: selectedPreset?.terminal_safe_sub || ''
        })
      })

      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Failed to race systems')
      }

      const data = await res.json()
      setAgentData(data.agent)
      setWorkflowData(data.workflow)
      setComparison(data.comparison)
    } catch (err) {
      setErrorMsg(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRunAgent = async () => {
    setLoading(true)
    setErrorMsg(null)
    setWorkflowData(null)
    setComparison(null)

    try {
      const res = await fetch(getApiUrl('run-agent'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompt,
          preset_id: selectedPreset?.id,
          target_servings: selectedPreset?.target_servings || 4,
          avoid_allergens: selectedPreset?.avoid_allergens || [],
          request_type: selectedPreset?.type || 'standard'
        })
      })

      if (!res.ok) throw new Error('Agent run failed')
      const data = await res.json()
      setAgentData(data)
    } catch (err) {
      setErrorMsg(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRunWorkflow = async () => {
    setLoading(true)
    setErrorMsg(null)
    setAgentData(null)
    setComparison(null)

    try {
      const res = await fetch(getApiUrl('run-workflow'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: prompt,
          preset_id: selectedPreset?.id,
          target_servings: selectedPreset?.target_servings || 4,
          avoid_allergens: selectedPreset?.avoid_allergens || [],
          request_type: selectedPreset?.type || 'standard'
        })
      })

      if (!res.ok) throw new Error('Workflow run failed')
      const data = await res.json()
      setWorkflowData(data)
    } catch (err) {
      setErrorMsg(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header backendConnected={backendConnected} />

      <main className="main-container">
        {/* The Decision Rule Summary Banner */}
        <div className="glass-panel" style={{ padding: '1rem 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderLeft: '4px solid #6366f1' }}>
          <div>
            <div style={{ fontSize: '0.78rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#818cf8', fontWeight: '700' }}>
              The Week 7 Decision Rule
            </div>
            <div style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              <strong>Does the execution path vary based on tool observation?</strong> If <em>Yes</em> (e.g. cascading allergen traps), an <strong>Agent Loop</strong> is mandatory. If <em>No</em> (linear scaling), the <strong>Fixed Workflow</strong> is ~1.7x faster and ~2.2x cheaper.
            </div>
          </div>
        </div>

        {/* Input & Preset Section */}
        <QueryInput
          prompt={prompt}
          setPrompt={setPrompt}
          presets={presets}
          selectedPreset={selectedPreset}
          onSelectPreset={handleSelectPreset}
          onRunRace={handleRunRace}
          onRunAgent={handleRunAgent}
          onRunWorkflow={handleRunWorkflow}
          loading={loading}
        />

        {/* Error Alert */}
        {errorMsg && (
          <div className="glass-panel" style={{ padding: '1rem', color: 'var(--danger-color)', borderLeft: '4px solid var(--danger-color)', background: 'rgba(244, 63, 94, 0.1)' }}>
            <strong>Error: </strong> {errorMsg}
          </div>
        )}

        {/* Comparison Results */}
        <RaceComparison
          agentData={agentData}
          workflowData={workflowData}
          comparison={comparison}
        />
      </main>
    </div>
  )
}
