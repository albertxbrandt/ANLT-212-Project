import { useState, useEffect } from 'react'
import './App.css'
import axios from 'axios'

function App() {
  const [health, setHealth] = useState(null)
  const [greeting, setGreeting] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Check backend health and get greeting on mount
  useEffect(() => {
    const initApp = async () => {
      try {
        const healthResponse = await axios.get('/api/health')
        setHealth(healthResponse.data)
        
        const helloResponse = await axios.get('/api/hello')
        setGreeting(helloResponse.data)
        
        setError(null)
      } catch (err) {
        setError('Failed to connect to backend')
        console.error('Init error:', err)
      } finally {
        setLoading(false)
      }
    }

    initApp()
  }, [])

  return (
    <>
      <header className="app-header">
        <h1>Simple Start</h1>
        <p className="subtitle">A blank slate to build from</p>
      </header>
      
      <main className="app-main">
        {loading && <div className="loading">Loading...</div>}
        
        {error && (
          <div className="error-message">
            <p>⚠ {error}</p>
          </div>
        )}
        
        {!loading && !error && (
          <div className="content">
            <section className="card">
              <h2>Backend Status</h2>
              {health && (
                <div className="info">
                  <p><strong>Status:</strong> {health.status}</p>
                  <p><strong>Timestamp:</strong> {new Date(health.timestamp).toLocaleString()}</p>
                </div>
              )}
            </section>
            
            <section className="card">
              <h2>API Response</h2>
              {greeting && (
                <div className="info">
                  <p><strong>Message:</strong> {greeting.message}</p>
                  <p><strong>Version:</strong> {greeting.version}</p>
                </div>
              )}
            </section>
          </div>
        )}
      </main>
    </>
  )
}

export default App

