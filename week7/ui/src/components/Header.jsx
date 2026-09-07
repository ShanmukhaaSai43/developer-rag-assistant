import React from 'react'

export default function Header({ backendConnected }) {
  return (
    <header className="app-header">
      <div className="logo-area">
        <div className="logo-badge">⚡</div>
        <div className="title-area">
          <h1>Recipe Agent vs Fixed Workflow</h1>
          <p>Week 7 · M4 Agent Loops & The Decision Rule</p>
        </div>
      </div>
      <div className="status-badge">
        <span 
          className="status-dot" 
          style={{ backgroundColor: backendConnected ? '#10b981' : '#f43f5e' }}
        />
        {backendConnected ? 'FastAPI Connected' : 'Connecting to Backend...'}
      </div>
    </header>
  )
}
