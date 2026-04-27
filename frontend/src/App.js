import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  
  // State for the agent's memory
  const [projectInfo, setProjectInfo] = useState({});
  const [userProfile, setUserProfile] = useState({});
  const [projectMatches, setProjectMatches] = useState([]);
  const [eligibleGrants, setEligibleGrants] = useState([]);
  const [currentStage, setCurrentStage] = useState(0);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(scrollToBottom, [messages]);

  useEffect(() => {
    sendInitial();
  }, []);

  const sendInitial = async () => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8001/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: '',
          project_info: {},
          user_profile: {},
          project_matches: [],
          eligible_grants: [],
          current_stage: 0,
          current_question: 0,
        }),
      });

      const data = await response.json();

      if (data.type === 'question') {
        updateAgentMemory(data);
        setMessages([{ text: data.question, sender: 'bot' }]);
      }
    } catch (error) {
      setMessages([{ text: 'Error connecting to the server. Is your Python backend running?', sender: 'bot error' }]);
    } finally {
      setLoading(false);
    }
  };

  const updateAgentMemory = (data) => {
    setProjectInfo(data.project_info || {});
    setUserProfile(data.user_profile || {});
    setProjectMatches(data.project_matches || []);
    setEligibleGrants(data.eligible_grants || []);
    setCurrentStage(data.current_stage || 0);
    setCurrentQuestion(data.current_question || 0);
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const currentInput = input;
    setMessages((prev) => [...prev, { text: currentInput, sender: 'user' }]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8001/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: currentInput,
          project_info: projectInfo,
          user_profile: userProfile,
          project_matches: projectMatches,
          eligible_grants: eligibleGrants,
          current_stage: currentStage,
          current_question: currentQuestion,
        }),
      });

      const data = await response.json();
      updateAgentMemory(data);

      if (data.type === 'question') {
        setMessages((prev) => [...prev, { text: data.question, sender: 'bot' }]);
      } else if (data.type === 'stage_complete') {
        const messagesToAdd = [{ text: data.message, sender: 'bot' }];
        if (data.next_question) {
          messagesToAdd.push({ text: data.next_question, sender: 'bot' });
        }
        setMessages((prev) => [...prev, ...messagesToAdd]);
      } else if (data.type === 'final_results') {
        let botText = data.message || 'Here are your results.';

        if (data.ranked_results && data.ranked_results.length > 0) {
          const rankedText = data.ranked_results
            .map((grant) => `**${grant.rank}. ${grant.grant_title}**\n${grant.explanation}`)
            .join('\n\n');
          botText = `${botText}\n\n${rankedText}`;
        } else if (data.eligible_grants && data.eligible_grants.length > 0) {
          const eligibleText = data.eligible_grants
            .slice(0, 10)
            .map((grant, index) => {
              const title = grant.grant_title || grant.metadata?.grant_title || 'Unknown Title';
              return `**${index + 1}. ${title}**`;
            })
            .join('\n');
          botText = `${botText}\n\n${eligibleText}`;
        }

        setMessages((prev) => [...prev, { text: botText, sender: 'bot' }]);
        
        // Reset memory for a new search
        updateAgentMemory({});
      }
    } catch (error) {
      setMessages((prev) => [...prev, { text: 'Connection lost. Please try again.', sender: 'bot error' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) sendMessage();
  };

  const handleReset = () => {
    setMessages([]);
    setInput('');
    updateAgentMemory({});
    sendInitial();
  };

  // Helper function to safely render **bold** text from the backend
  const formatMessage = (text) => {
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index}>{part.slice(2, -2)}</strong>;
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className="App">
      <div className="app-wrapper">
        <header className="app-header">
          <div className="header-icon">🧭</div>
          <div className="header-text">
            <h1>Northeast Grant Explorer</h1>
            <p>Intelligent funding matches for PA, NY, NJ, and New England.</p>
          </div>
        </header>

        <div className="chat-container">
          <div className="chat-messages">
            {messages.length === 0 && !loading && (
              <div className="welcome-placeholder">
                <p>Connecting to the Grant Database...</p>
              </div>
            )}
            
            {messages.map((msg, index) => (
              <div key={index} className={`message-row ${msg.sender === 'user' ? 'row-user' : 'row-bot'}`}>
                {msg.sender !== 'user' && <div className="avatar bot-avatar">AI</div>}
                
                <div className={`message-bubble ${msg.sender}`}>
                  {msg.text.split('\n').map((line, i) => (
                    <div key={i} className="message-line">
                      {formatMessage(line)}
                    </div>
                  ))}
                </div>

                {msg.sender === 'user' && <div className="avatar user-avatar">You</div>}
              </div>
            ))}
            
            {loading && (
              <div className="message-row row-bot">
                <div className="avatar bot-avatar">AI</div>
                <div className="message-bubble bot typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-area">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Describe your project or answer the prompt..."
              disabled={loading}
              autoFocus
            />
            <button className="btn-send" onClick={sendMessage} disabled={loading || !input.trim()}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
            <button className="btn-reset" onClick={handleReset} disabled={loading} title="Start Over">
               <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="1 4 1 10 7 10"></polyline>
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;