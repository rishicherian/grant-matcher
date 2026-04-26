import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
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
        headers: {
          'Content-Type': 'application/json',
        },
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
        setProjectInfo(data.project_info || {});
        setUserProfile(data.user_profile || {});
        setProjectMatches(data.project_matches || []);
        setEligibleGrants(data.eligible_grants || []);
        setCurrentStage(data.current_stage || 0);
        setCurrentQuestion(data.current_question || 0);
        setMessages([{ text: data.question, sender: 'bot' }]);
      } else {
        setMessages([{ text: 'Unexpected response from server.', sender: 'bot' }]);
      }
    } catch (error) {
      setMessages([{ text: 'Error connecting to the server. Please refresh.', sender: 'bot' }]);
    } finally {
      setLoading(false);
    }
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
        headers: {
          'Content-Type': 'application/json',
        },
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

      if (data.type === 'question') {
        setProjectInfo(data.project_info || {});
        setUserProfile(data.user_profile || {});
        setProjectMatches(data.project_matches || []);
        setEligibleGrants(data.eligible_grants || []);
        setCurrentStage(data.current_stage || 0);
        setCurrentQuestion(data.current_question || 0);

        setMessages((prev) => [
          ...prev,
          { text: data.question, sender: 'bot' },
        ]);
      } else if (data.type === 'stage_complete') {
        setProjectInfo(data.project_info || {});
        setUserProfile(data.user_profile || {});
        setProjectMatches(data.project_matches || []);
        setEligibleGrants(data.eligible_grants || []);
        setCurrentStage(data.current_stage || 0);
        setCurrentQuestion(data.current_question || 0);

        const messagesToAdd = [{ text: data.message, sender: 'bot' }];

        if (data.next_question) {
          messagesToAdd.push({ text: data.next_question, sender: 'bot' });
        }

        setMessages((prev) => [...prev, ...messagesToAdd]);
      } else if (data.type === 'final_results') {
        setProjectInfo(data.project_info || {});
        setUserProfile(data.user_profile || {});
        setProjectMatches(data.project_matches || []);
        setEligibleGrants(data.eligible_grants || []);
        
        let botText = data.message || 'Here are your results.';

        if (data.ranked_results && data.ranked_results.length > 0) {
          const rankedText = data.ranked_results
            .map((grant) => `${grant.rank}. ${grant.grant_title}\n   ${grant.explanation}`)
            .join('\n\n');

          botText = `${botText}\n\n${rankedText}`;
        } else if (data.eligible_grants && data.eligible_grants.length > 0) {
          const eligibleText = data.eligible_grants
            .slice(0, 10)
            .map((grant, index) => {
              const title = grant.grant_title || grant.metadata?.grant_title || 'Unknown Title';
              return `${index + 1}. ${title}`;
            })
            .join('\n');

          botText = `${botText}\n\n${eligibleText}`;
        }

        setMessages((prev) => [...prev, { text: botText, sender: 'bot' }]);

        // reset for a fresh conversation after final step
        setProjectInfo({});
        setUserProfile({});
        setProjectMatches([]);
        setEligibleGrants([]);
        setCurrentStage(0);
        setCurrentQuestion(0);
      } else if (data.type === 'error') {
        setMessages((prev) => [
          ...prev,
          { text: data.message || 'An error occurred.', sender: 'bot' },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          { text: 'Unexpected response from server.', sender: 'bot' },
        ]);
      }
    } catch (error) {
      console.error('Frontend error:', error);
      setMessages((prev) => [
        ...prev,
        { text: 'Error connecting to the server. Please try again.', sender: 'bot' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      sendMessage();
    }
  };

  const handleReset = () => {
    setMessages([]);
    setInput('');
    setProjectInfo({});
    setUserProfile({});
    setProjectMatches([]);
    setEligibleGrants([]);
    setCurrentStage(0);
    setCurrentQuestion(0);
    setLoading(true);
    // Fetch the initial question after reset
    fetch('http://localhost:8001/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: '',
        project_info: {},
        user_profile: {},
        project_matches: [],
        eligible_grants: [],
        current_stage: 0,
        current_question: 0,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.type === 'question') {
          setMessages([{ text: data.question, sender: 'bot' }]);
        }
      })
      .catch((error) => {
        console.error('Reset error:', error);
        setMessages([{ text: 'Error resetting. Please refresh the page.', sender: 'bot' }]);
      })
      .finally(() => setLoading(false));
  };

  return (
    <div className="App">
      <header className="App-header">
        <img src="upenn.png" alt="UPenn Logo" className="upenn-logo" />
        <h1>Penn Grant Matcher</h1>
      </header>

      <div className="chat-container">
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              {msg.text.split('\n').map((line, i) => (
                <div key={i}>{line}</div>
              ))}
            </div>
          ))}
          {loading && <div className="message bot">Thinking...</div>}
          <div ref={messagesEndRef} />
        </div>

        <div className="chat-input">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type your answer..."
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading || !input.trim()}>
            {loading ? 'Sending...' : 'Send'}
          </button>
          <button onClick={handleReset} disabled={loading} className="reset-button">
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;