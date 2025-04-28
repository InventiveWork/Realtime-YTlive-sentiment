// src/App.js
import React, { useState, useEffect } from 'react';
import './App.css'; // You can create this for styling

function App() {
  const [sentimentData, setSentimentData] = useState({});
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState(null);

  const fetchSentiment = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/sentiment');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSentimentData(data);
      setError(null);
    } catch (e) {
      console.error("Could not fetch sentiment:", e);
      setError("Failed to fetch sentiment data.");
    }
  };

  const startSentimentAnalysis = async () => {
    try {
      const response = await fetch('http://localhost:5000/api/start');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      console.log(data.message);
      setIsRunning(true);
      setError(null);
    } catch (e) {
      console.error("Could not start sentiment analysis:", e);
      setError("Failed to start sentiment analysis.");
    }
  };

  const getBackgroundColor = (score) => {
    if (score >= 7) {
      return 'lightgreen'; // Positive sentiment
    } else if (score <= 4) {
      return 'lightcoral'; // Negative sentiment
    } else {
      return 'lightyellow'; // Neutral sentiment (scores 5 and 6)
    }
  };

  const getEmoji = (score) => {
    if (score >= 7) {
      return '😊'; // Happy emoji code
    } else if (score <= 4) {
      return '😞'; // Sad emoji code
    } else {
      return '😐'; // Neutral emoji code
    }
  };

  useEffect(() => {
    let intervalId;

    if (isRunning) {
      intervalId = setInterval(fetchSentiment, 3000); // Fetch every 1 second
    } else {
      clearInterval(intervalId);
    }

    return () => clearInterval(intervalId); // Cleanup on unmount or when isRunning changes
  }, [isRunning]);

  const backgroundColor = sentimentData.score ? getBackgroundColor(sentimentData.score) : 'white';
  const currentEmoji = sentimentData.score ? getEmoji(sentimentData.score) : null;

  return (
    <div className="App" style={{ backgroundColor }}>
      <h1>Sentiment Analysis Dashboard</h1>
      <button onClick={startSentimentAnalysis} disabled={isRunning}>
        {isRunning ? 'Running...' : 'Start Analysis'}
      </button>

      {error && <p className="error">{error}</p>}

      <h2>Latest Sentiment:</h2>
      {currentEmoji && <span style={{ fontSize: '3em', marginBottom: '10px' }}>{currentEmoji}</span>}
      {Object.keys(sentimentData).length > 0 ? (
        <pre>{JSON.stringify(sentimentData, null, 2)}</pre>
      ) : (
        <p>{isRunning ? 'Fetching data...' : 'No sentiment data available. Start the analysis.'}</p>
      )}
    </div>
  );
}

export default App;