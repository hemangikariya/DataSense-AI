"use client"

import React, { useState, useEffect } from "react"
import { Send, Pin, Trash2, Edit2, Share2, Plus, MessageSquare, ShieldAlert } from "lucide-react"
import axios from "axios"

export default function ConversationalBIPage() {
  const [conversations, setConversations] = useState<any[]>([])
  const [activeConv, setActiveConv] = useState<any>(null)
  const [messages, setMessages] = useState<any[]>([])
  const [inputText, setInputText] = useState("")
  
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [streamingToken, setStreamingToken] = useState("")

  const workspaceId = typeof window !== "undefined" ? localStorage.getItem("workspace_id") || "00000000-0000-0000-0000-000000000000" : "00000000-0000-0000-0000-000000000000"

  const fetchConversations = async () => {
    try {
      const token = localStorage.getItem("token")
      const res = await axios.get(`/api/v1/ai/conversations`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      setConversations(res.data)
    } catch (err) {
      setError("Failed to fetch conversation history list.")
    }
  }

  useEffect(() => {
    fetchConversations()
  }, [])

  // Create new conversation thread
  const startNewConversation = async () => {
    try {
      const token = localStorage.getItem("token")
      const res = await axios.post(`/api/v1/ai/conversations`, {
        title: "New Conversation Thread"
      }, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      setActiveConv(res.data)
      setMessages([])
      fetchConversations()
    } catch (err) {
      setError("Failed to initialize conversation thread.")
    }
  }

  // Load selected conversation history messages
  useEffect(() => {
    if (!activeConv) return
    const loadMessages = async () => {
      try {
        const token = localStorage.getItem("token")
        const res = await axios.get(`/api/v1/ai/conversations/${activeConv.id}`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Workspace-ID": workspaceId
          }
        })
        setMessages(res.data.messages || [])
      } catch (err) {
        console.error(err)
      }
    }
    loadMessages()
  }, [activeConv])

  // Post message and stream response tokens
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputText.trim() || !activeConv) return

    const userText = inputText.trim()
    setInputText("")
    setError(null)
    
    // Add user message to state
    setMessages(prev => [...prev, { role: "user", content: userText, created_at: new Date().toISOString() }])
    
    setLoading(true)
    setStreamingToken("")

    try {
      const token = localStorage.getItem("token")
      const response = await fetch(`/api/v1/ai/conversations/${activeConv.id}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        },
        body: JSON.stringify({ content: userText })
      })

      if (!response.body) return
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      
      let chunkAccumulator = ""

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        const text = decoder.decode(value, { stream: true })
        chunkAccumulator += text
        setStreamingToken(chunkAccumulator)
      }

      // Add final assistant message response
      setMessages(prev => [...prev, { role: "assistant", content: chunkAccumulator, created_at: new Date().toISOString() }])
      setStreamingToken("")
    } catch (err) {
      setError("Token query stream failed or was blocked by guardrails.")
    } finally {
      setLoading(false)
    }
  }

  // Pin thread
  const togglePin = async (id: string, pinned: boolean) => {
    try {
      const token = localStorage.getItem("token")
      await axios.post(`/api/v1/ai/conversations/${id}/pin?is_pinned=${!pinned}`, {}, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      fetchConversations()
    } catch (err) {
      console.error(err)
    }
  }

  // Delete thread
  const deleteConversation = async (id: string) => {
    try {
      const token = localStorage.getItem("token")
      await axios.delete(`/api/v1/ai/conversations/${id}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Workspace-ID": workspaceId
        }
      })
      if (activeConv?.id === id) {
        setActiveConv(null)
        setMessages([])
      }
      fetchConversations()
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Sidebar history list */}
      <div className="w-80 bg-slate-900 border-r border-slate-800 flex flex-col h-full">
        <div className="p-4 border-b border-slate-800">
          <button 
            onClick={startNewConversation}
            className="w-full flex items-center justify-center gap-2 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium text-xs transition"
          >
            <Plus className="w-4 h-4" /> Start New Chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {conversations.map(c => {
            const isActive = activeConv?.id === c.id
            return (
              <div 
                key={c.id}
                onClick={() => setActiveConv(c)}
                className={`group flex items-center justify-between p-3 rounded-lg cursor-pointer transition ${
                  isActive ? "bg-slate-800 text-blue-500" : "hover:bg-slate-800/40 text-slate-300"
                }`}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <MessageSquare className="w-4 h-4 flex-shrink-0" />
                  <span className="text-xs truncate font-semibold">{c.title}</span>
                </div>

                <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1">
                  <button 
                    onClick={(e) => { e.stopPropagation(); togglePin(c.id, c.is_pinned) }}
                    className={`p-1 rounded hover:bg-slate-700 ${c.is_pinned ? "text-blue-500" : "text-slate-500"}`}
                  >
                    <Pin className="w-3.5 h-3.5" />
                  </button>
                  <button 
                    onClick={(e) => { e.stopPropagation(); deleteConversation(c.id) }}
                    className="p-1 rounded hover:bg-red-500/10 text-slate-500 hover:text-red-500"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Main chat window container */}
      <div className="flex-1 flex flex-col h-full bg-slate-950">
        {activeConv ? (
          <>
            <div className="p-4 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
              <div>
                <h2 className="font-bold text-slate-200 text-sm">{activeConv.title}</h2>
                <p className="text-[10px] text-slate-500 mt-0.5">Conversational BI analysis thread</p>
              </div>
            </div>

            {error && (
              <div className="m-4 p-4 bg-red-950/20 border border-red-900/40 text-red-400 text-xs rounded flex items-center gap-3">
                <ShieldAlert className="w-4 h-4" />
                <span>{error}</span>
              </div>
            )}

            {/* Message list window */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {messages.map((m, idx) => {
                const isUser = m.role === "user"
                return (
                  <div key={idx} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
                    <div className={`max-w-xl p-4 rounded-lg shadow ${
                      isUser 
                        ? "bg-blue-600 text-white rounded-br-none" 
                        : "bg-slate-900 border border-slate-800 text-slate-200 rounded-bl-none"
                    }`}>
                      <p className="text-xs leading-relaxed whitespace-pre-wrap">{m.content}</p>
                    </div>
                  </div>
                )
              })}

              {streamingToken && (
                <div className="flex justify-start">
                  <div className="max-w-xl p-4 bg-slate-900 border border-slate-800 text-slate-200 rounded-lg rounded-bl-none shadow">
                    <p className="text-xs leading-relaxed whitespace-pre-wrap">{streamingToken}</p>
                    <span className="inline-block w-1.5 h-3.5 bg-blue-500 animate-pulse ml-1" />
                  </div>
                </div>
              )}
            </div>

            {/* Input form */}
            <form onSubmit={handleSendMessage} className="p-4 border-t border-slate-800 bg-slate-900/40 flex gap-4">
              <input 
                type="text" 
                value={inputText}
                onChange={e => setInputText(e.target.value)}
                className="flex-1 bg-slate-950 border border-slate-800 px-4 py-3 rounded text-xs text-slate-100 focus:outline-none focus:border-blue-600"
                placeholder="Ask your dataset (e.g. 'explain data drift metrics' or 'show sales sum')"
                disabled={loading}
              />
              <button 
                type="submit"
                disabled={loading || !inputText.trim()}
                className="px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-800 disabled:text-slate-600 rounded text-white font-semibold transition"
              >
                <Send className="w-4 h-4" />
              </button>
            </form>
          </>
        ) : (
          <div className="flex-1 flex flex-col justify-center items-center">
            <MessageSquare className="w-12 h-12 text-slate-700 mb-4 animate-bounce" />
            <h3 className="font-semibold text-slate-350">Conversational Business Intelligence</h3>
            <p className="text-slate-500 text-xs mt-1">Select or start a chat thread from the history sidebar.</p>
          </div>
        )}
      </div>
    </div>
  )
}
