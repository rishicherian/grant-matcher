import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState({});
  const [currentStep, setCurrentStep] = useState(0);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
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
        body: JSON.stringify({ message: "", profile, current_step: currentStep }),
      });
      const data = await response.json();
      if (data.type === "question") {
        setProfile(data.profile);
        setCurrentStep(data.current_step);
        const botMessage = { text: data.question, sender: 'bot' };
        setMessages([botMessage]);
      }
    } catch (error) {
      const botMessage = { text: 'Error connecting to the server. Please refresh.', sender: 'bot' };
      setMessages([botMessage]);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (input.trim() && !loading) {
      const userMessage = { text: input, sender: 'user' };
      setMessages(prev => [...prev, userMessage]);
      setLoading(true);
      const currentInput = input;
      setInput('');

      try {
        const response = await fetch('http://localhost:8001/query', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: currentInput, profile, current_step: currentStep }),
        });
        const data = await response.json();
        if (data.type === "question") {
          setProfile(data.profile);
          setCurrentStep(data.current_step);
          const botMessage = { text: data.question, sender: 'bot' };
          setMessages(prev => [...prev, botMessage]);
        } else if (data.type === "result") {
          const results = data.result;
          let botText = '';
          if (results.success) {
            const eligible = results.eligible || [];
            const uncertain = results.uncertain || [];
            botText = `Found ${eligible.length} eligible grants and ${uncertain.length} uncertain grants.\n\n`;
            if (eligible.length > 0) {
              botText += 'Eligible:\n';
              eligible.slice(0, 3).forEach(grant => {
                botText += `- ${grant.metadata?.grant_title || 'Unknown'} (Score: ${grant.score})\n`;
              });
            }
            if (uncertain.length > 0) {
              botText += '\nUncertain:\n';
              uncertain.slice(0, 3).forEach(grant => {
                botText += `- ${grant.metadata?.grant_title || 'Unknown'} (Score: ${grant.score})\n`;
              });
            }
          } else {
            botText = results.message || results.error || 'Sorry, I couldn\'t process your request.';
          }
          const botMessage = { text: botText, sender: 'bot' };
          setMessages(prev => [...prev, botMessage]);
          // Reset for new conversation
          setProfile({});
          setCurrentStep(0);
        }
      } catch (error) {
        const botMessage = { text: 'Error connecting to the server. Please try again.', sender: 'bot' };
        setMessages(prev => [...prev, botMessage]);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      sendMessage();
    }
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
            onKeyPress={handleKeyPress}
            placeholder="Type your answer..."
            disabled={loading}
          />
          <button onClick={sendMessage} disabled={loading || !input.trim()}>
            {loading ? 'Sending...' : 'Send'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
