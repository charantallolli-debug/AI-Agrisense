import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Hero from './components/Hero';
import DiseaseDetection from './components/DiseaseDetection';
import PredictionDashboard from './components/PredictionDashboard';
import WeatherWidget from './components/WeatherWidget';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import CropCatalog from './components/CropCatalog';
import InfoHub from './components/InfoHub';
import { addHistoryEntry } from './utils/history';
import { Send, Sparkles } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [cropCatalogInfo, setCropCatalogInfo] = useState(null);
  
  // Detection Module State
  const [scanResult, setScanResult] = useState(null);
  const [scanLoading, setScanLoading] = useState(false);
  const [scanError, setScanError] = useState(null);
  
  // Weather Widget State
  const [weatherData, setWeatherData] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(false);

  // LLM Treatment Plan State
  const [llmPlanContent, setLlmPlanContent] = useState('');
  const [llmPlanLoading, setLlmPlanLoading] = useState(false);

  // Chatbot State
  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', content: 'Namaste! I am your AgriSense Smart Advisory chatbot. Scan a crop leaf or ask me any question about pests, treatments, weather, or farming advice.' }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Fetch crop list & demo weather on mount
  useEffect(() => {
    fetchCrops();
    fetchWeather(null, null, 'Mumbai');
  }, []);

  const fetchCrops = async () => {
    try {
      const res = await fetch('/api/assistant/crops');
      const data = await res.json();
      setCropCatalogInfo(data);
    } catch (err) {
      console.error('Failed to fetch crops catalog:', err);
    }
  };

  const fetchWeather = async (lat, lon, city) => {
    setWeatherLoading(true);
    try {
      const qs = city ? `city=${encodeURIComponent(city)}` : `lat=${lat}&lon=${lon}`;
      const res = await fetch(`/api/assistant/weather?${qs}`);
      const data = await res.json();
      setWeatherData(data);
    } catch (err) {
      console.error('Failed to fetch weather:', err);
    } finally {
      setWeatherLoading(false);
    }
  };

  const handleAnalyze = async (base64Image) => {
    setScanLoading(true);
    setScanError(null);
    setScanResult(null);
    setLlmPlanContent('');
    
    try {
      const response = await fetch('/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: base64Image }),
      });
      
      const result = await response.json();
      
      if (result.status === 'error') {
        setScanError(result.message || 'Analysis failed. Please try another crop leaf photo.');
        return;
      }
      
      setScanResult(result);
      
      // Save to localStorage history log
      addHistoryEntry({
        crop: result.crop,
        disease: result.disease,
        prediction: result.prediction,
        confidence: result.confidence,
        is_healthy: result.is_healthy,
        severity_percent: result.severity_percent,
        harmfulness: result.harmfulness,
        impact: result.impact
      });
    } catch (err) {
      console.error('Analysis API error:', err);
      setScanError('Could not reach the AI detection server. Check your connection.');
    } finally {
      setScanLoading(false);
    }
  };

  const handleFetchLlmPlan = async () => {
    if (!scanResult) return;
    setLlmPlanLoading(true);
    setLlmPlanContent('');
    
    try {
      const res = await fetch('/api/assistant/treatment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          crop: scanResult.crop,
          disease: scanResult.disease,
          confidence: scanResult.confidence,
          solution: scanResult.solution,
          weather: weatherData,
        }),
      });
      const data = await res.json();
      setLlmPlanContent(data.content || data.message || 'Custom treatment advice currently unavailable.');
    } catch (err) {
      console.error('LLM Treatment API error:', err);
      setLlmPlanContent('Error fetching AI treatment plan.');
    } finally {
      setLlmPlanLoading(false);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    const message = chatInput.trim();
    if (!message || chatLoading) return;
    
    setChatInput('');
    const updatedMessages = [...chatMessages, { role: 'user', content: message }];
    setChatMessages(updatedMessages);
    setChatLoading(true);

    const context = {
      ...(scanResult && scanResult.status === 'success' ? {
        crop: scanResult.crop,
        disease: scanResult.disease,
        confidence: scanResult.confidence
      } : {}),
      ...(weatherData ? { weather: weatherData } : {})
    };

    try {
      const res = await fetch('/api/assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          history: updatedMessages.slice(0, -1),
          context
        }),
      });
      const data = await res.json();
      const reply = data.reply || data.message || 'I am sorry, I could not process your query right now.';
      setChatMessages(prev => [...prev, { role: 'assistant', content: reply }]);
    } catch (err) {
      console.error('Chatbot API error:', err);
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Connection error. Please try again.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleStartScanFromHero = () => {
    setScanResult(null);
    setScanError(null);
    setActiveTab('detect');
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 pb-16 md:pb-0">
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        cropCatalogInfo={cropCatalogInfo}
      />
      
      <main className="flex-grow">
        {activeTab === 'home' && (
          <Hero 
            onStartScan={handleStartScanFromHero}
            onSwitchTab={setActiveTab}
          />
        )}
        
        {activeTab === 'detect' && (
          <div className="space-y-6 py-6">
            <DiseaseDetection 
              onAnalyze={handleAnalyze}
              isLoading={scanLoading}
              errorMsg={scanError}
              clearError={() => setScanError(null)}
            />
            {scanResult && (
              <PredictionDashboard 
                result={scanResult}
                onFetchLlmPlan={handleFetchLlmPlan}
                llmPlanLoading={llmPlanLoading}
                llmPlanContent={llmPlanContent}
              />
            )}
          </div>
        )}
        
        {activeTab === 'analytics' && (
          <AnalyticsDashboard />
        )}
        
        {activeTab === 'weather' && (
          <WeatherWidget 
            weatherData={weatherData}
            onFetchWeather={fetchWeather}
            isLoading={weatherLoading}
          />
        )}
        
        {activeTab === 'chat' && (
          <div className="mx-auto max-w-3xl px-4 py-8">
            <div className="bg-white border border-slate-200 rounded-3xl overflow-hidden shadow-sm h-[600px] flex flex-col justify-between">
              {/* Chat Header */}
              <div className="p-5 border-b border-slate-100 flex items-center gap-3 bg-slate-900 text-white">
                <div className="p-2 w-fit bg-primary-500/10 rounded-full text-primary-400">
                  <Sparkles className="w-5 h-5 shrink-0" />
                </div>
                <div>
                  <h3 className="font-serif text-lg font-bold leading-none">Farmer AI Assistant</h3>
                  <p className="text-[10px] font-sans font-medium tracking-wide text-slate-400 mt-1 uppercase">Direct Agronomist Chat</p>
                </div>
              </div>
              
              {/* Chat Message Thread */}
              <div className="flex-1 p-5 overflow-y-auto space-y-4 bg-slate-50/50">
                {chatMessages.map((msg, idx) => (
                  <div 
                    key={idx} 
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div 
                      className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed shadow-sm font-medium ${
                        msg.role === 'user'
                          ? 'bg-primary-600 text-white rounded-br-none'
                          : 'bg-white text-slate-800 rounded-bl-none border border-slate-200/50'
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))}
                
                {chatLoading && (
                  <div className="flex justify-start">
                    <div className="bg-white text-slate-400 px-4 py-3 rounded-2xl rounded-bl-none border border-slate-200/50 flex items-center gap-1.5 text-xs font-semibold shadow-sm">
                      <div className="flex gap-1">
                        <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce"></span>
                        <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.2s]"></span>
                        <span className="w-1.5 h-1.5 bg-slate-400 rounded-full animate-bounce [animation-delay:0.4s]"></span>
                      </div>
                      AI is typing...
                    </div>
                  </div>
                )}
              </div>

              {/* Message Input Box */}
              <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-100 flex gap-2 bg-white">
                <input
                  type="text"
                  placeholder="Type a farming query (e.g. wheat rust control)..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  disabled={chatLoading}
                  className="flex-grow px-4 py-2.5 text-sm rounded-full border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 bg-slate-50/50"
                  style={{ minHeight: '44px' }}
                />
                <button
                  type="submit"
                  disabled={chatLoading || !chatInput.trim()}
                  className="p-2.5 rounded-full bg-slate-900 hover:bg-slate-800 disabled:bg-slate-100 text-white disabled:text-slate-400 transition-all flex items-center justify-center"
                  style={{ width: '44px', height: '44px' }}
                >
                  <Send className="w-4.5 h-4.5" />
                </button>
              </form>
            </div>
          </div>
        )}
      </main>

      <InfoHub />
      
      {/* Footer Details */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-400 font-bold uppercase tracking-wider">
        © 2026 AgriSense Platform · Pusa Agri-Science Institute
      </footer>
    </div>
  );
}
