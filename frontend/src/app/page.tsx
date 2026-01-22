"use client";

import { VoiceInput } from "@/components/VoiceInput";
import { ConstraintsDisplay } from "@/components/ConstraintsDisplay";
import { ItineraryView } from "@/components/ItineraryView";
import { useState, useEffect, useRef } from "react";
import { Loader2, MessageCircle, Mic, Volume2, Paperclip, Send, Plus } from "lucide-react";

export default function Home() {
  const [transcript, setTranscript] = useState("");
  const [constraints, setConstraints] = useState<any>(null);
  const [itinerary, setItinerary] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isPlanning, setIsPlanning] = useState(false);
  const [isExplaining, setIsExplaining] = useState(false);
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant', content: string }>>([]);
  const [inputText, setInputText] = useState("");
  const [isTtsEnabled, setIsTtsEnabled] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (!itinerary && transcript && transcript.length > 2 && !transcript.startsWith("Listening") && !transcript.startsWith("Recording") && !transcript.startsWith("Error")) {
      analyzeTranscript(transcript);
    }
    else if (itinerary && transcript && transcript.length > 2 && !transcript.startsWith("Listening") && !transcript.startsWith("Recording")) {
      askQuestion(transcript);
    }
  }, [transcript]);

  const analyzeTranscript = async (text: string) => {
    setIsAnalyzing(true);
    setMessages(prev => [...prev, { role: 'user', content: text }]);

    try {
      const response = await fetch(`${API_BASE}/api/analyze-intent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text,
          existing_constraints: constraints,
          history: messages
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Constraints received:", data);
        setConstraints(data);
        const responseText = data.suggested_response || data.clarification_question || (data.is_complete ? "I've captured your trip details! Ready to plan your itinerary?" : "I've noted that. Could you tell me more about your trip, like when you're planning to go or how long you'll stay?");
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: responseText
        }]);
        playTTS(responseText);
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: "Sorry, I'm having trouble connecting to my brain right now. Please try again in a moment."
        }]);
      }
    } catch (error) {
      console.error("Analysis error:", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const unlockAudio = () => {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      const utterance = new SpeechSynthesisUtterance("");
      window.speechSynthesis.speak(utterance);
      window.speechSynthesis.cancel();
    }
  };

  const askQuestion = async (text: string) => {
    setIsExplaining(true);
    setMessages(prev => [...prev, { role: 'user', content: text }]);

    try {
      const response = await fetch(`${API_BASE}/api/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      if (response.ok) {
        const data = await response.json();
        const answer = data.answer;
        setMessages(prev => [...prev, { role: 'assistant', content: answer }]);
        playTTS(answer);
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: "I'm sorry, I couldn't find an answer to that right now. Could you ask me in a different way?"
        }]);
      }
    } catch (error) {
      console.error("Explanation error:", error);
    } finally {
      setIsExplaining(false);
    }
  };

  const playTTS = async (text: string) => {
    if (!isTtsEnabled) return;

    try {
      const response = await fetch(`${API_BASE}/api/tts`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      if (response.ok) {
        const audioBlob = await response.blob();
        const audioUrl = URL.createObjectURL(audioBlob);
        const audio = new Audio(audioUrl);
        audio.play().catch(e => {
          console.error("Audio play failed:", e);
          fallbackTTS(text);
        });
      } else {
        console.warn("TTS backend failed or quota exceeded, using fallback");
        fallbackTTS(text);
      }
    } catch (e) {
      console.error("TTS backend failed", e);
      fallbackTTS(text);
    }
  };

  const fallbackTTS = (text: string) => {
    if (!isTtsEnabled || typeof window === 'undefined' || !window.speechSynthesis) return;

    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[*#_~]/g, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);

    // Select a better voice if available
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.name.includes("Google") && v.name.includes("Female"))
      || voices.find(v => v.lang.startsWith("en") && v.name.includes("Female"))
      || voices.find(v => v.lang.startsWith("en"));

    if (preferredVoice) utterance.voice = preferredVoice;
    utterance.rate = 1.1; // Slightly faster for responsiveness
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
  };

  const handleConfirm = async () => {
    unlockAudio();
    setIsPlanning(true);
    const startMsg = "Great! Let me create your personalized itinerary...";
    setMessages(prev => [...prev, { role: 'assistant', content: startMsg }]);
    playTTS(startMsg);

    try {
      console.log("Sending constraints to plan-trip:", constraints);
      const response = await fetch(`${API_BASE}/api/plan-trip`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(constraints),
      });

      if (response.ok) {
        const data = await response.json();
        console.log("Itinerary received:", data);
        setItinerary(data);
        const endMsg = "Your itinerary is ready! Check it out on the right.";
        setMessages(prev => [...prev, { role: 'assistant', content: endMsg }]);
        playTTS(endMsg);
        setConstraints(null);
        setTranscript("");
      } else {
        const errorText = await response.text();
        console.error("Plan-trip error:", errorText);
        setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I had trouble creating your itinerary. Please try again." }]);
      }
    } catch (error) {
      console.error("Planning error:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I had trouble creating your itinerary. Please try again." }]);
    } finally {
      setIsPlanning(false);
    }
  };

  const handleSendMessage = () => {
    if (!inputText.trim()) return;
    unlockAudio();

    const text = inputText;
    setInputText("");

    if (itinerary) {
      askQuestion(text);
    } else {
      analyzeTranscript(text);
    }
  };

  const downloadPDF = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/generate-pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(itinerary),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = "trip_itinerary.pdf";
        document.body.appendChild(a);
        a.click();
        a.remove();
      }
    } catch (error) {
      console.error("PDF download error:", error);
    }
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-slate-50 flex overflow-hidden">
      {/* Left Column - Conversation */}
      <div className="flex-1 flex flex-col h-full">
        {/* Header */}
        <div className="p-6 border-b bg-white/80 backdrop-blur-sm flex-shrink-0">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-slate-900">Conversation</h1>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  unlockAudio();
                  setIsTtsEnabled(!isTtsEnabled);
                }}
                className={`p-2 rounded-lg transition ${isTtsEnabled ? 'bg-blue-50 text-blue-600' : 'text-slate-400 hover:bg-slate-100'}`}
                title={isTtsEnabled ? "Disable Text-to-Speech" : "Enable Text-to-Speech"}
              >
                <Volume2 className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <MessageCircle className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-slate-900 mb-2">Start Planning Your Trip</h2>
              <p className="text-slate-600">Tell me where you'd like to go, and I'll help create the perfect itinerary</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${msg.role === 'user'
                ? 'bg-slate-900 text-white'
                : 'bg-white border border-slate-200 text-slate-900'
                }`}>
                {msg.content}
              </div>
            </div>
          ))}

          {(isAnalyzing || isExplaining || isPlanning) && (
            <div className="flex justify-start">
              <div className="bg-white border border-slate-200 rounded-2xl px-4 py-3 flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin text-blue-600" />
                <span className="text-slate-600">Thinking...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-6 border-t bg-white/80 backdrop-blur-sm flex-shrink-0">
          <div className="flex items-center gap-3 bg-white border border-slate-200 rounded-full px-4 py-3 shadow-sm">
            <button className="text-slate-400 hover:text-slate-600 transition">
              <Paperclip className="w-5 h-5" />
            </button>
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Type your response..."
              className="flex-1 outline-none text-slate-900 placeholder:text-slate-400 bg-transparent"
            />
            <VoiceInput onTranscriptChange={setTranscript} />
            <button
              onClick={handleSendMessage}
              className="bg-slate-900 text-white p-2 rounded-full hover:bg-slate-800 transition flex-shrink-0"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Right Column - Trip Overview & Itinerary */}
      <div className="w-[420px] bg-white border-l border-slate-200 flex flex-col h-full overflow-y-auto flex-shrink-0">
        <div className="p-6 space-y-6">
          {/* Trip Overview Card */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Trip Overview</h2>

            {/* Destination */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700">Destination</span>
                {!constraints?.destination_city && (
                  <span className="text-xs bg-red-100 text-red-600 px-2 py-1 rounded-full font-medium">Required</span>
                )}
              </div>
              {constraints?.destination_city ? (
                <div className="text-base text-slate-900">{constraints.destination_city}</div>
              ) : (
                <button className="w-full border border-dashed border-slate-300 rounded-lg py-2 text-sm text-slate-500 hover:border-slate-400 transition flex items-center justify-center gap-2">
                  <Plus className="w-4 h-4" />
                  Add Destination
                </button>
              )}
            </div>

            {/* Budget */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-slate-700">Budget</span>
                {!constraints?.budget_level && (
                  <span className="text-xs bg-red-100 text-red-600 px-2 py-1 rounded-full font-medium">Required</span>
                )}
              </div>
              {constraints?.budget_level ? (
                <div className="text-base text-slate-900">{constraints.budget_level}</div>
              ) : (
                <div className="text-sm text-slate-400">Not specified</div>
              )}
            </div>

            {/* Interests & Preferences */}
            <div className="mb-4">
              <h3 className="text-sm font-medium text-slate-700 mb-2">Interests & Preferences</h3>

              <div className="flex flex-wrap gap-2 mb-3">
                {constraints?.interests?.map((interest: string, i: number) => (
                  <span key={i} className="px-2 py-1 bg-blue-100 text-blue-700 rounded-md text-xs font-medium border border-blue-200">
                    {interest}
                  </span>
                ))}
                {constraints?.must_visit?.map((place: string, i: number) => (
                  <span key={`must-${i}`} className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded-md text-xs font-medium border border-emerald-200">
                    📍 {place}
                  </span>
                ))}
                {(!constraints?.interests?.length && !constraints?.must_visit?.length) && (
                  <span className="text-sm text-slate-400 italic">No specific interests mentioned yet</span>
                )}
              </div>

              <div className="flex items-center gap-4 text-sm text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-100">
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-slate-700">Pace:</span>
                  <span className="capitalize text-slate-900">{constraints?.pace || "Moderate"}</span>
                </div>
                <div className="w-px h-4 bg-slate-300"></div>
                <div className="flex items-center gap-1.5">
                  <span className="font-semibold text-slate-700">Travelers:</span>
                  <span className="text-slate-900">{constraints?.travelers_count || 1}</span>
                </div>
              </div>
            </div>

            {/* Required Information Checklist */}
            <div className="mt-6 pt-6 border-t border-slate-200">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Required Information</h3>
              <div className="space-y-2">
                {[
                  { label: 'Destination', completed: !!constraints?.destination_city },
                  { label: 'Duration', completed: !!constraints?.duration_days },
                  { label: 'Start Date', completed: !!constraints?.start_date },
                  { label: 'Budget', completed: !!constraints?.budget_level },
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${item.completed ? 'bg-emerald-500' : 'bg-slate-300'}`} />
                    <span className={`text-sm ${item.completed ? 'text-slate-900' : 'text-slate-500'}`}>
                      {item.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {constraints?.is_complete && !itinerary && (
              <button
                onClick={handleConfirm}
                disabled={isPlanning}
                className="w-full mt-6 bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition disabled:bg-slate-400 disabled:cursor-not-allowed"
              >
                {isPlanning ? 'Generating...' : 'Generate Itinerary'}
              </button>
            )}
          </div>

          {/* Itinerary Card */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">Your Itinerary</h2>
            {itinerary ? (
              <div>
                <ItineraryView itinerary={itinerary} />
                <button
                  onClick={downloadPDF}
                  className="w-full mt-4 border border-slate-300 text-slate-700 py-2 rounded-lg font-medium hover:bg-slate-50 transition"
                >
                  Download PDF
                </button>
              </div>
            ) : (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <MessageCircle className="w-8 h-8 text-slate-400" />
                </div>
                <p className="text-sm text-slate-500">Your itinerary will appear here once generated</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
