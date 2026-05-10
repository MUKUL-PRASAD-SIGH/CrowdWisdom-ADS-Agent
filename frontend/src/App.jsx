import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [status, setStatus] = useState({ is_running: false, status_message: 'Idle' })
  const [results, setResults] = useState(null)
  const [niche, setNiche] = useState("trading education stock market signals")

  // Poll for status & results progressively
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/status')
        const data = await res.json()
        setStatus(data)
        
        // Fetch results continuously while running or immediately after
        fetchResults()
      } catch (err) {
        console.error("API offline or error:", err)
      }
    }

    fetchStatus()
    const interval = setInterval(fetchStatus, 2000)
    return () => clearInterval(interval)
  }, [])

  const fetchResults = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/results')
      const data = await res.json()
      setResults(data)
    } catch (err) {
      console.error(err)
    }
  }

  const startPipeline = async () => {
    try {
      // Optimistically clear local results so it resets visually instantly
      setResults(null)
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

  // Determine active stages
  const r = results || {}
  const isAgent1Active = status.is_running && !r.ads_raw
  const isAgent2Active = status.is_running && r.ads_raw && !r.pain_concepts
  const isAgent3Active = status.is_running && r.pain_concepts && !r.ad_script
  const isAgent4Active = status.is_running && r.ad_script && !r.media?.has_video

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
              <><span className="spinner"></span> Pipeline Running...</>
            ) : (
              "Start 4-Agent Pipeline"
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

      <div className="dashboard">
        <h2 className="dashboard-title">Live Pipeline Monitor</h2>
        
        <div className="results-grid">
          
          {/* Agent 1: Meta Ads Research */}
          <div className={`glass-panel agent-panel ${isAgent1Active ? 'panel-active' : ''}`}>
            <div className="agent-header">
              <span className="agent-icon">🕵️</span>
              <h2>Agent 1: Meta Ads Research</h2>
            </div>
            <p className="agent-desc">Scrapes successful ads from Meta Ad Library via Apify (Last 30 Days).</p>
            
            {isAgent1Active && (
              <div className="pulse-loading">
                <span className="pulse-dot"></span> Scraping Meta Ad Library...
              </div>
            )}

            {r.ads_raw && Array.isArray(r.ads_raw) && r.ads_raw.length > 0 ? (
              <div className="scrollable-content">
                {r.ads_raw.slice(0, 5).map((ad, i) => (
                  <div key={i} className="data-card pop-in">
                    <p><strong>Ad Content:</strong> {ad.text?.substring(0, 100)}...</p>
                    <p><strong>Format:</strong> {ad.format || 'Video/Image'}</p>
                  </div>
                ))}
                {r.ads_raw.length > 5 && <p className="text-muted">+ {r.ads_raw.length - 5} more ads analyzed</p>}
              </div>
            ) : !isAgent1Active && (
              <p className="empty-state">Waiting for execution...</p>
            )}
          </div>

          {/* Agent 2: Marketing Extraction */}
          <div className={`glass-panel agent-panel ${isAgent2Active ? 'panel-active' : ''}`}>
            <div className="agent-header">
              <span className="agent-icon">🧬</span>
              <h2>Agent 2: Pain & Concept Extraction</h2>
            </div>
            <p className="agent-desc">Extracts marketing DNA, pain points, and hooks from the winning ads.</p>

            {isAgent2Active && (
              <div className="pulse-loading">
                <span className="pulse-dot"></span> Analyzing psychology and DNA...
              </div>
            )}

            {r.pain_concepts ? (
              <div className="scrollable-content pop-in">
                <div className="insight-section">
                  <h4>🔥 Top Pain Points</h4>
                  <ul>
                    {r.pain_concepts.top_pain_points?.slice(0,3).map((p, i) => <li key={i}>{p}</li>)}
                  </ul>
                </div>
                <div className="insight-section">
                  <h4>🎣 Winning Hooks</h4>
                  <ul>
                    {r.pain_concepts.winning_hooks?.slice(0,3).map((h, i) => <li key={i}>{h}</li>)}
                  </ul>
                </div>
              </div>
            ) : !isAgent2Active && (
              <p className="empty-state">Waiting for raw ads data...</p>
            )}
          </div>

          {/* Agent 3: Scripting */}
          <div className={`glass-panel agent-panel ${isAgent3Active ? 'panel-active' : ''}`}>
            <div className="agent-header">
              <span className="agent-icon">✍️</span>
              <h2>Agent 3: GDrive Context & Scripting</h2>
            </div>
            <p className="agent-desc">Fetches GDrive data & generates 60s script tailored to extracted pain points.</p>
            
            {isAgent3Active && (
              <div className="pulse-loading">
                <span className="pulse-dot"></span> Writing highly-converting script...
              </div>
            )}

            {r.ad_script && r.ad_script.scenes ? (
              <div className="scrollable-content pop-in">
                {r.ad_script.scenes.map((scene, i) => (
                  <div key={i} className="scene-card">
                    <div className="scene-header">Scene {i + 1}</div>
                    <p><strong>Voice:</strong> {scene.voiceover}</p>
                    <p><strong>Visual:</strong> {scene.visual}</p>
                  </div>
                ))}
              </div>
            ) : !isAgent3Active && (
              <p className="empty-state">Waiting for marketing insights...</p>
            )}
          </div>

          {/* Agent 4: Video Production */}
          <div className={`glass-panel agent-panel video-production-panel ${isAgent4Active ? 'panel-active' : ''}`}>
            <div className="agent-header">
              <span className="agent-icon">🎬</span>
              <h2>Agent 4: AI Video Production</h2>
            </div>
            <p className="agent-desc">Generates images, 11labs voiceover, and renders MP4 via Remotion.</p>

            {isAgent4Active && (
              <div className="pulse-loading">
                <span className="pulse-dot"></span> Generating assets and rendering MP4...
              </div>
            )}

            <div className="media-preview-container pop-in">
              {r.media?.has_video ? (
                <video controls className="preview-video" src={`http://localhost:8000${r.media.video_url}`} />
              ) : !isAgent4Active && (
                <div className="video-placeholder">
                  <div className="icon">🎥</div>
                  <p>Video rendering pending...</p>
                </div>
              )}

              {r.media?.has_audio && (
                <div className="audio-player">
                  <p><strong>ElevenLabs Voiceover:</strong></p>
                  <audio controls src={`http://localhost:8000${r.media.audio_url}`} />
                </div>
              )}
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}

export default App
