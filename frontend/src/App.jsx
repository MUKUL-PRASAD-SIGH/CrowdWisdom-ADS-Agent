import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [status, setStatus] = useState({ is_running: false, status_message: 'Idle' })
  const [results, setResults] = useState(null)
  const [niche, setNiche] = useState("trading education stock market signals")

  // Poll for status
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/status')
        const data = await res.json()
        setStatus(data)
        
        if (!data.is_running && data.status_message === "Pipeline completed successfully!") {
          fetchResults()
        }
      } catch (err) {
        console.error("API offline or error:", err)
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 3000)
    return () => clearInterval(interval)
  }, [])

  // Fetch results when done or on load
  const fetchResults = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/results')
      const data = await res.json()
      setResults(data)
    } catch (err) {
      console.error(err)
    }
  }

  useEffect(() => {
    fetchResults()
  }, [])

  const startPipeline = async () => {
    try {
      await fetch('http://localhost:8000/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ niche })
      })
      setStatus({ ...status, is_running: true, status_message: "Starting..." })
    } catch (err) {
      alert("Failed to start pipeline. Is the backend running?")
    }
  }

  return (
    <div className="app-container">
      <div className="glass-panel main-panel">
        <header className="hero">
          <div className="badge">AI Agent Pipeline</div>
          <h1>CrowdWisdomTrading <span className="highlight">Ads Studio</span></h1>
          <p>Generate high-converting, 60-second video ads entirely with AI.</p>
        </header>

        <div className="controls">
          <input 
            type="text" 
            value={niche} 
            onChange={(e) => setNiche(e.target.value)}
            disabled={status.is_running}
            className="niche-input"
            placeholder="Enter niche/keywords..."
          />
          <button 
            className={`generate-btn ${status.is_running ? 'running' : ''}`}
            onClick={startPipeline}
            disabled={status.is_running}
          >
            {status.is_running ? (
              <><span className="spinner"></span> Generating Ad...</>
            ) : (
              "Generate AI Ad Pipeline"
            )}
          </button>
        </div>

        <div className="status-board">
          <h3>Status: <span className={status.is_running ? 'status-active' : 'status-idle'}>{status.status_message}</span></h3>
          
          {status.is_running && (
            <div className="progress-container">
              <div className="progress-bar-animated"></div>
            </div>
          )}
        </div>
      </div>

      {results && (
        <div className="results-grid">
          {/* Media Player */}
          <div className="glass-panel media-panel">
            <h2>Final Media</h2>
            {results.media?.has_video ? (
              <video controls className="preview-video" src={`http://localhost:8000${results.media.video_url}`} />
            ) : (
              <div className="video-placeholder">
                <div className="icon">🎥</div>
                <p>Video rendering requires Remotion setup.</p>
                {results.media?.has_audio && (
                  <div className="audio-player">
                    <p>Listen to generated Voiceover:</p>
                    <audio controls src={`http://localhost:8000${results.media.audio_url}`} />
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Script Viewer */}
          <div className="glass-panel script-panel">
            <h2>Generated Ad Script</h2>
            {results.ad_script ? (
              <div className="script-content">
                {results.ad_script.scenes?.map((scene, i) => (
                  <div key={i} className="scene-card">
                    <div className="scene-header">Scene {i + 1}</div>
                    <p><strong>Voiceover:</strong> {scene.voiceover}</p>
                    <p><strong>Visual:</strong> {scene.visual}</p>
                  </div>
                )) || <p>Script format not found.</p>}
              </div>
            ) : (
              <p className="empty-state">No script generated yet.</p>
            )}
          </div>

          {/* Market Insights */}
          <div className="glass-panel insights-panel">
            <h2>Market Insights DNA</h2>
            {results.pain_concepts ? (
              <div className="insights-content">
                <div className="insight-section">
                  <h4>Top Pain Points</h4>
                  <ul>
                    {results.pain_concepts.top_pain_points?.map((p, i) => <li key={i}>{p}</li>)}
                  </ul>
                </div>
                <div className="insight-section">
                  <h4>Winning Hooks</h4>
                  <ul>
                    {results.pain_concepts.winning_hooks?.map((h, i) => <li key={i}>{h}</li>)}
                  </ul>
                </div>
              </div>
            ) : (
              <p className="empty-state">No insights generated yet.</p>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
