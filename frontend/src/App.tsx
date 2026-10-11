import React, { useState, useEffect, useRef, useCallback } from "react";
import { Sidebar } from "./components/Sidebar";
import { ChatWorkspace } from "./components/ChatWorkspace";
import { ArtifactViewer } from "./components/ArtifactViewer";
import { Ship30Modal } from "./components/Ship30Modal";
import { api } from "./api/client";
import type { Session, Message, Artifact, ProvidersStatusResponse } from "./types";

export function App() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [activeArtifactId, setActiveArtifactId] = useState<string | null>(null);

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);
  const [isArtifactOpen, setIsArtifactOpen] = useState<boolean>(true);
  const [isShip30ModalOpen, setIsShip30ModalOpen] = useState<boolean>(false);
  const [ship30Error, setShip30Error] = useState<string | null>(null);

  // Model & SDK configuration state
  const [selectedModelProvider, setSelectedModelProvider] = useState<string>("ollama");
  const [selectedModelName, setSelectedModelName] = useState<string>("llama3.2");
  const [agentSdk, setAgentSdk] = useState<string>("pi"); // Default to official Pi SDK
  const [providersStatus, setProvidersStatus] = useState<ProvidersStatusResponse | null>(null);

  // Responsive viewport width tracking
  const [windowWidth, setWindowWidth] = useState<number>(() =>
    typeof window !== "undefined" ? window.innerWidth : 1440
  );

  useEffect(() => {
    const handleResize = () => {
      const w = window.innerWidth;
      setWindowWidth(w);
      if (w < 768) {
        setIsSidebarOpen(false);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  // Resizable Right Panel State (min 320px, max 800px)
  const [artifactPanelWidth, setArtifactPanelWidth] = useState<number>(() => {
    const saved = localStorage.getItem("lenny_artifact_width");
    return saved ? parseInt(saved, 10) : 480;
  });
  const isDraggingRef = useRef<boolean>(false);

  // 1. Initial Load: Fetch Sessions & Providers Status
  useEffect(() => {
    const initialize = async () => {
      try {
        const [sessList, pStatus] = await Promise.all([
          api.listSessions().catch(() => []),
          api.getProvidersStatus().catch(() => null),
        ]);

        if (pStatus) {
          setProvidersStatus(pStatus);
        }

        if (sessList && sessList.length > 0) {
          setSessions(sessList);
          setActiveSessionId(sessList[0].id);
        } else {
          // Create initial default session
          const newSess = await api.createSession("Growth Strategy Chat");
          setSessions([newSess]);
          setActiveSessionId(newSess.id);
        }
      } catch (err) {
        console.error("Initialization error:", err);
      }
    };
    initialize();
  }, []);

  // 2. Load Session History & Artifacts on Active Session Change
  useEffect(() => {
    if (!activeSessionId) return;

    const loadSessionData = async () => {
      try {
        const [historyRes, artifactsRes] = await Promise.all([
          api.getSessionHistory(activeSessionId).catch(() => ({ messages: [] })),
          api.getSessionArtifacts(activeSessionId).catch(() => ({ artifacts: [] })),
        ]);

        setMessages(historyRes.messages || []);
        const loadedArtifacts = artifactsRes.artifacts || [];
        setArtifacts(loadedArtifacts);

        if (loadedArtifacts.length > 0) {
          setActiveArtifactId(loadedArtifacts[0].id);
        } else {
          setActiveArtifactId(null);
        }
      } catch (err) {
        console.error("Failed to load session data:", err);
      }
    };

    loadSessionData();
  }, [activeSessionId]);

  // 3. New Session Handler
  const handleNewSession = async () => {
    try {
      const newSess = await api.createSession(
        `Chat ${new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`,
        selectedModelProvider,
        selectedModelName
      );
      setSessions((prev) => [newSess, ...prev]);
      setActiveSessionId(newSess.id);
      setMessages([]);
      setArtifacts([]);
      setActiveArtifactId(null);
    } catch (err) {
      console.error("Failed to create new session:", err);
    }
  };

  // 4. Rename Session
  const handleRenameSession = async (id: string, newTitle: string) => {
    const updated = await api.renameSession(id, newTitle);
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, title: updated.title } : s)));
  };

  // 5. Delete Session
  const handleDeleteSession = async (id: string) => {
    await api.deleteSession(id);
    const filtered = sessions.filter((s) => s.id !== id);
    setSessions(filtered);
    if (activeSessionId === id) {
      if (filtered.length > 0) {
        setActiveSessionId(filtered[0].id);
      } else {
        handleNewSession();
      }
    }
  };

  // 6. Send Message Handler
  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isLoading) return;

    // Optimistic user message
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      session_id: activeSessionId || "",
      role: "user",
      content: text,
      citations: [],
      metadata: {},
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const response = await api.sendChatMessage({
        session_id: activeSessionId || undefined,
        message: text,
        model_provider: selectedModelProvider,
        model_name: selectedModelName,
        agentic: Boolean(agentSdk),
        agent_sdk: agentSdk || undefined,
      });

      // Update session ID if newly created
      if (response.session_id && response.session_id !== activeSessionId) {
        setActiveSessionId(response.session_id);
      }

      setMessages((prev) => [...prev, response]);

      // If new artifacts arrived, add to state and reveal in viewer
      if (response.artifacts && response.artifacts.length > 0) {
        setArtifacts((prev) => {
          const combined = [...response.artifacts!, ...prev];
          return combined.filter((v, i, a) => a.findIndex((t) => t.id === v.id) === i);
        });
        setActiveArtifactId(response.artifacts[0].id);
        setIsArtifactOpen(true);
      }
    } catch (err: any) {
      console.error("Chat message error:", err);
      // Append assistant error notice
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        session_id: activeSessionId || "",
        role: "assistant",
        content: `⚠️ **Inference Error**: Failed to get response (${err.message}). Please check that the local server and Ollama are reachable.`,
        citations: [],
        metadata: { notice: "Request failed" },
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // 7. Ship 30 Essay Generation Handler
  const handleGenerateShip30 = async (topic: string, targetAudience: string) => {
    setIsLoading(true);
    setShip30Error(null);

    try {
      const res = await api.generateShip30Essay({
        session_id: activeSessionId || undefined,
        topic,
        target_audience: targetAudience,
        model_provider: selectedModelProvider,
        model_name: selectedModelName,
      });

      // Optimistic user prompt & assistant response
      const userPrompt = `Generate a Ship 30 for 30 essay on: ${topic} for ${targetAudience}`;
      const tempUserMsg: Message = {
        id: `ship30-user-${Date.now()}`,
        session_id: res.session_id || activeSessionId || "",
        role: "user",
        content: userPrompt,
        citations: [],
        metadata: { skill: "ship30" },
        created_at: new Date().toISOString(),
      };

      const essayHeadline = res.headline || `Ship 30: ${topic}`;
      const guestList = Array.isArray(res.guest_references) && res.guest_references.length > 0
        ? res.guest_references.join(", ")
        : "Lenny's Podcast Guests";
      const wordCount = res.word_count || (res.essay ? res.essay.split(/\s+/).filter(Boolean).length : 0);

      const assistantMsg: Message = {
        id: `ship30-res-${Date.now()}`,
        session_id: res.session_id || activeSessionId || "",
        role: "assistant",
        content: `### 🚀 Ship 30 for 30 Essay Generated: "${essayHeadline}"\n\nWord Count: **${wordCount} words** | Grounded in: **${guestList}**\n\nThe full structured essay has been saved as a Markdown artifact and is now open in your Artifact Viewer on the right!`,
        citations: res.citations || [],
        metadata: { skill: "ship30", model_name: selectedModelName },
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, tempUserMsg, assistantMsg]);

      // Create artifact in viewer
      const newArtifact: Artifact = {
        id: res.artifact_id || `art-${Date.now()}`,
        session_id: res.session_id || activeSessionId || "",
        title: essayHeadline,
        artifact_type: "markdown",
        content: res.essay || "",
        created_at: new Date().toISOString(),
      };

      setArtifacts((prev) => [newArtifact, ...prev]);
      setActiveArtifactId(newArtifact.id);
      setIsArtifactOpen(true);
      setIsShip30ModalOpen(false);
      setShip30Error(null);
    } catch (err: any) {
      console.error("Failed to generate Ship 30 essay:", err);
      const friendlyError = err.message || "Failed to generate Ship 30 essay";
      setShip30Error(friendlyError);

      const errMsg: Message = {
        id: `err-${Date.now()}`,
        session_id: activeSessionId || "",
        role: "assistant",
        content: `⚠️ Failed to generate Ship 30 essay: ${friendlyError}`,
        citations: [],
        metadata: {},
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // 8. Horizontal Resizing Drag Handle Logic
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isDraggingRef.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";

    const handleMouseMove = (moveEvent: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const windowWidth = window.innerWidth;
      const newWidth = windowWidth - moveEvent.clientX;

      // Constrain panel width between 320px and 850px, ensuring center workspace has >= 400px
      const clampedWidth = Math.min(Math.max(newWidth, 320), Math.min(850, windowWidth - 450));
      setArtifactPanelWidth(clampedWidth);
      localStorage.setItem("lenny_artifact_width", clampedWidth.toString());
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
  }, []);

  const activeSession = sessions.find((s) => s.id === activeSessionId) || null;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#101B27] text-[#FFF6E9] font-sans">
      {/* 1. LEFT PANEL: Session Sidebar (Research Library) */}
      {windowWidth < 768 && isSidebarOpen ? (
        <div className="fixed inset-0 z-50 bg-[#101B27]/70 backdrop-blur-sm flex animate-in fade-in duration-150">
          <Sidebar
            sessions={sessions}
            activeSessionId={activeSessionId}
            onSelectSession={(id) => {
              setActiveSessionId(id);
              setIsSidebarOpen(false);
            }}
            onNewSession={() => {
              handleNewSession();
              setIsSidebarOpen(false);
            }}
            onRenameSession={handleRenameSession}
            onDeleteSession={handleDeleteSession}
            isOpen={true}
            onToggleOpen={() => setIsSidebarOpen(false)}
            currentProvider={selectedModelProvider}
            currentModel={selectedModelName}
          />
          <div className="flex-1" onClick={() => setIsSidebarOpen(false)} />
        </div>
      ) : (
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onSelectSession={setActiveSessionId}
          onNewSession={handleNewSession}
          onRenameSession={handleRenameSession}
          onDeleteSession={handleDeleteSession}
          isOpen={isSidebarOpen}
          onToggleOpen={() => setIsSidebarOpen(!isSidebarOpen)}
          currentProvider={selectedModelProvider}
          currentModel={selectedModelName}
        />
      )}

      {/* 2. CENTER PANEL: Conversation Workspace (Research Desk) */}
      <div className="flex-1 h-full min-w-0 flex flex-col overflow-hidden relative">
        <ChatWorkspace
          session={activeSession}
          messages={messages}
          isLoading={isLoading}
          onSendMessage={handleSendMessage}
          selectedModelProvider={selectedModelProvider}
          selectedModelName={selectedModelName}
          onSelectModel={(p, m) => {
            setSelectedModelProvider(p);
            setSelectedModelName(m);
          }}
          agentSdk={agentSdk}
          onSelectAgentSdk={setAgentSdk}
          onOpenShip30={() => setIsShip30ModalOpen(true)}
          isArtifactOpen={isArtifactOpen}
          onToggleArtifact={() => setIsArtifactOpen(!isArtifactOpen)}
          artifactCount={artifacts.length}
          providersStatus={providersStatus}
        />
      </div>

      {/* Horizontal Resizing Drag Handle (Desktop/Tablet Only) */}
      {isArtifactOpen && windowWidth >= 768 && (
        <div
          onMouseDown={handleMouseDown}
          className="w-1.5 h-full bg-[#101B27] hover:bg-[#FF7952] cursor-col-resize shrink-0 transition-colors duration-150 z-20 group relative"
          title="Drag to resize Artifact Studio"
        >
          <div className="absolute inset-y-0 -left-1 -right-1" />
          <div className="h-10 w-1 bg-white/20 group-hover:bg-[#101B27] rounded-full mx-auto my-auto top-1/2 -translate-y-1/2 relative transition-colors" />
        </div>
      )}

      {/* 3. RIGHT PANEL: Resizable Artifact Viewer (Artifact Studio) */}
      {isArtifactOpen &&
        (windowWidth < 768 ? (
          /* Mobile full-screen overlay */
          <div className="fixed inset-0 z-40 bg-[#172634] flex flex-col animate-in fade-in zoom-in-95 duration-150">
            <ArtifactViewer
              artifacts={artifacts}
              activeArtifactId={activeArtifactId}
              onSelectArtifact={setActiveArtifactId}
              onClose={() => setIsArtifactOpen(false)}
              onGenerateShip30={() => setIsShip30ModalOpen(true)}
            />
          </div>
        ) : (
          /* Desktop/Tablet resizable panel */
          <div
            style={{ width: `${Math.min(artifactPanelWidth, windowWidth - 360)}px` }}
            className="h-full shrink-0 transition-all duration-75 relative z-10"
          >
            <ArtifactViewer
              artifacts={artifacts}
              activeArtifactId={activeArtifactId}
              onSelectArtifact={setActiveArtifactId}
              onClose={() => setIsArtifactOpen(false)}
              onGenerateShip30={() => setIsShip30ModalOpen(true)}
            />
          </div>
        ))}

      {/* Ship 30 Essay Generator Modal */}
      <Ship30Modal
        isOpen={isShip30ModalOpen}
        onClose={() => {
          setIsShip30ModalOpen(false);
          setShip30Error(null);
        }}
        onSubmit={handleGenerateShip30}
        isLoading={isLoading}
        errorMessage={ship30Error}
        onClearError={() => setShip30Error(null)}
      />
    </div>
  );
}

export default App;
