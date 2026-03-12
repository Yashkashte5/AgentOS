import { useState, useRef, useEffect, useCallback } from "react";

const API = "https://agentos-4yyz.onrender.com";

const AGENT_META = {
  supervisor:  { label: "Supervisor",  icon: "⬡", color: "#7C6AF7" },
  research:    { label: "Research",    icon: "◎", color: "#4EAEFF" },
  code:        { label: "Code",        icon: "⟨⟩", color: "#43E8A0" },
  executor:    { label: "Executor",    icon: "▶",  color: "#F7C948" },
  self_heal:   { label: "Self Heal",   icon: "⟳",  color: "#FF7043" },
  file:        { label: "File",        icon: "◫",  color: "#CE93D8" },
  api:         { label: "API",         icon: "⬡",  color: "#80DEEA" },
  synthesizer: { label: "Synthesizer", icon: "◈",  color: "#A5D6A7" },
};

const AGENT_ORDER = ["supervisor","research","api","code","executor","self_heal","file","synthesizer"];

function stripFences(text) {
  if (!text) return text;
  return text.replace(/```[\w]*\n?/g, "").replace(/```/g, "").trim();
}

function renderMarkdown(text) {
  if (!text) return null;
  const lines = text.split("\n");
  return lines.map((line, i) => {
    if (line.startsWith("### ")) return <div key={i} style={{ color: "#e0e0e0", fontWeight: 600, marginTop: "12px", marginBottom: "4px" }}>{line.slice(4)}</div>;
    if (line.startsWith("## "))  return <div key={i} style={{ color: "#f0f0f0", fontWeight: 700, marginTop: "14px", marginBottom: "4px", fontSize: "13px" }}>{line.slice(3)}</div>;
    if (line.startsWith("# "))   return <div key={i} style={{ color: "#fff", fontWeight: 700, marginTop: "16px", marginBottom: "6px", fontSize: "14px" }}>{line.slice(2)}</div>;
    if (line.match(/^\d+\. /))   return <div key={i} style={{ color: "#aaa", paddingLeft: "8px", marginBottom: "2px" }}>{line}</div>;
    if (line.startsWith("- ") || line.startsWith("* ")) return <div key={i} style={{ color: "#aaa", paddingLeft: "8px", marginBottom: "2px" }}>• {line.slice(2)}</div>;
    if (line.startsWith("```"))  return null;
    if (line.trim() === "")      return <div key={i} style={{ height: "8px" }} />;
    const parts = line.split(/(`[^`]+`)/g);
    return (
      <div key={i} style={{ color: "#aaa", marginBottom: "2px", lineHeight: "1.8" }}>
        {parts.map((p, j) =>
          p.startsWith("`") && p.endsWith("`")
            ? <code key={j} style={{ background: "#141414", color: "#43E8A0", padding: "1px 5px", borderRadius: "3px", fontSize: "11px", fontFamily: "'DM Mono', monospace" }}>{p.slice(1, -1)}</code>
            : p
        )}
      </div>
    );
  });
}

function extractNodeSummary(node, updates) {
  if (!updates || typeof updates !== "object") return null;
  if (node === "supervisor")  return updates.plan?.length ? `Plan: ${updates.plan.join(" → ")}` : null;
  if (node === "research")    return updates.agent_outputs?.research ? stripFences(updates.agent_outputs.research).slice(0, 220) : null;
  if (node === "code")        return updates.code ? stripFences(updates.code).slice(0, 220) : null;
  if (node === "executor")    return updates.execution_result?.slice(0, 220) || updates.execution_error?.slice(0, 220) || null;
  if (node === "self_heal")   return "Fixing code and retrying...";
  if (node === "file")        return updates.agent_outputs?.file || null;
  if (node === "api")         return updates.agent_outputs?.api?.slice(0, 220) || null;
  if (node === "synthesizer") return updates.final_output?.slice(0, 320) || null;
  return null;
}

function NodeCard({ node, status, summary, index, usedNodes }) {
  const meta = AGENT_META[node] || { label: node, icon: "○", color: "#aaa" };
  const isActive  = status === "active";
  const isDone    = status === "done";
  const isError   = status === "error";
  const isPending = status === "pending";

  if (!usedNodes.has(node) && isPending && usedNodes.size > 0) return null;

  return (
    <div style={{
      display: "flex", gap: "12px", alignItems: "flex-start",
      opacity: isPending ? 0.25 : 1, transition: "opacity 0.4s ease",
    }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", paddingTop: "2px", flexShrink: 0 }}>
        <div style={{
          width: "28px", height: "28px", borderRadius: "50%",
          border: `2px solid ${isDone || isActive ? meta.color : "#191919"}`,
          background: isDone ? meta.color + "15" : isActive ? meta.color + "0d" : "transparent",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: "11px", color: isDone || isActive ? meta.color : "#252525",
          transition: "all 0.3s ease",
          boxShadow: isActive ? `0 0 10px ${meta.color}33` : "none",
        }}>
          {isActive
            ? <span style={{ animation: "spin 1s linear infinite", display: "inline-block" }}>◌</span>
            : isError ? "✕" : meta.icon}
        </div>
        {index < AGENT_ORDER.length - 1 && (
          <div style={{
            width: "1px", flex: 1, minHeight: "14px",
            background: isDone ? `linear-gradient(${meta.color}44, #141414)` : "#111",
            margin: "3px 0", transition: "background 0.5s ease",
          }} />
        )}
      </div>

      <div style={{
        flex: 1, marginBottom: "6px",
        background: isDone ? "#0d0d0d" : isActive ? "#0b0b0b" : "transparent",
        border: `1px solid ${isDone ? "#161616" : isActive ? meta.color + "2a" : "transparent"}`,
        borderRadius: "8px",
        padding: isDone || isActive ? "9px 11px" : "2px 0",
        transition: "all 0.3s ease",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: "7px" }}>
          <span style={{
            fontSize: "10px", fontFamily: "'DM Mono', monospace", fontWeight: 500,
            color: isDone || isActive ? meta.color : "#999",
            letterSpacing: "0.08em", textTransform: "uppercase",
            transition: "color 0.3s ease",
          }}>{meta.label}</span>
          {isDone && (
            <span style={{
              fontSize: "8px", background: meta.color + "15", color: meta.color,
              padding: "1px 5px", borderRadius: "3px", fontFamily: "'DM Mono', monospace",
            }}>done</span>
          )}
          {isActive && (
            <span style={{
              fontSize: "8px", background: meta.color + "15", color: meta.color,
              padding: "1px 5px", borderRadius: "3px", fontFamily: "'DM Mono', monospace",
              animation: "pulse 1.5s ease infinite",
            }}>running</span>
          )}
        </div>
        {summary && (isDone || isActive) && (
          <div style={{
            marginTop: "6px", fontSize: "11px",
            color: "#999",  // ← FIXED: was #555, now readable
            fontFamily: "'DM Mono', monospace", lineHeight: "1.6",
            whiteSpace: "pre-wrap", wordBreak: "break-word",
            borderLeft: `2px solid ${meta.color}1a`, paddingLeft: "8px",
          }}>
            {summary}
            {isActive && <span style={{ animation: "blink 1s step-end infinite" }}>▌</span>}
          </div>
        )}
      </div>
    </div>
  );
}

function TabBtn({ label, active, onClick, badge }) {
  return (
    <button onClick={onClick} style={{
      background: "transparent", border: "none",
      color: active ? "#ffffff" : "#444444",
      fontSize: "10px", fontFamily: "'DM Mono', monospace",
      letterSpacing: "0.08em", textTransform: "uppercase",
      cursor: "pointer", padding: "0 12px", height: "100%",
      borderBottom: `2px solid ${active ? "#7C6AF7" : "transparent"}`,
      transition: "all 0.2s", display: "flex", alignItems: "center", gap: "6px",
    }}>
      {label}
      {badge && (
        <span style={{
          background: "#7C6AF711", color: "#7C6AF7",
          fontSize: "8px", padding: "1px 5px", borderRadius: "3px",
        }}>{badge}</span>
      )}
    </button>
  );
}

function CodeBlock({ code, filename }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <div style={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        padding: "10px 20px", borderBottom: "1px solid #0f0f0f", background: "#080808", flexShrink: 0,
      }}>
        <span style={{ fontSize: "11px", fontFamily: "'DM Mono', monospace", color: "#CE93D8" }}>
          ◫ {filename}
        </span>
        <button onClick={copy} style={{
          background: copied ? "#43E8A015" : "#111",
          border: `1px solid ${copied ? "#43E8A033" : "#1a1a1a"}`,
          color: copied ? "#43E8A0" : "#444",
          fontSize: "10px", fontFamily: "'DM Mono', monospace",
          padding: "3px 10px", borderRadius: "4px", cursor: "pointer",
          transition: "all 0.2s",
        }}>
          {copied ? "✓ copied" : "copy"}
        </button>
      </div>
      <div style={{ flex: 1, overflow: "auto", padding: "20px 24px" }}>
        <pre style={{
          margin: 0, fontSize: "12px", fontFamily: "'DM Mono', monospace",
          color: "#888", lineHeight: "1.8", whiteSpace: "pre-wrap", wordBreak: "break-word",
        }}>
          {stripFences(code)}
        </pre>
      </div>
    </div>
  );
}

export default function App() {
  const [task, setTask]           = useState("");
  const [status, setStatus]       = useState("idle");
  const [nodeStates, setNodeStates]   = useState({});
  const [usedNodes, setUsedNodes]     = useState(new Set());
  const [finalOutput, setFinalOutput] = useState("");
  const [errorMsg, setErrorMsg]       = useState("");
  const [history, setHistory]         = useState([]);
  const [rightTab, setRightTab]       = useState("output");
  const [codeContent, setCodeContent]         = useState(null);
  const [fileName, setFileName]               = useState(null);
  const [executionResult, setExecutionResult] = useState(null);
  const [leftWidth, setLeftWidth] = useState(300);

  const isDragging = useRef(false);
  const dragStartX = useRef(0);
  const dragStartW = useRef(0);

  const bottomRef = useRef(null);
  const esRef     = useRef(null);
  const synthEsRef = useRef(null);
  const taskRef   = useRef(task);
  useEffect(() => { taskRef.current = task; }, [task]);

  const onDividerMouseDown = (e) => {
    isDragging.current = true;
    dragStartX.current = e.clientX;
    dragStartW.current = leftWidth;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  };

  useEffect(() => {
    const onMouseMove = (e) => {
      if (!isDragging.current) return;
      const delta = e.clientX - dragStartX.current;
      const newW = Math.min(600, Math.max(220, dragStartW.current + delta));
      setLeftWidth(newW);
    };
    const onMouseUp = () => {
      if (!isDragging.current) return;
      isDragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
    window.addEventListener("mousemove", onMouseMove);
    window.addEventListener("mouseup", onMouseUp);
    return () => {
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
    };
  }, []);

  // load persisted history from backend on mount
  useEffect(() => {
    fetch(`${API}/history`)
      .then(r => r.json())
      .then(data => {
        if (data.history?.length) {
          setHistory(data.history.map(h => ({
            task: h.task,
            result: h.result,
            id: h.id,
            plan: h.plan ? (typeof h.plan === "string" ? JSON.parse(h.plan) : h.plan) : [],
          })));
        }
      })
      .catch(() => {}); // silent fail if backend not up yet
  }, []);

  // Load persisted history from SQLite on first mount
  useEffect(() => {
    fetch(`${API}/history?limit=20`)
      .then(r => r.json())
      .then(data => {
        if (data.history?.length) {
          setHistory(data.history.map(h => ({
            task:   h.task,
            result: h.result,
            id:     h.id,
            plan:   h.plan || [],
          })));
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (status === "running") bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [nodeStates, status]);

  const reset = useCallback(() => {
    esRef.current?.close();
    synthEsRef.current?.close();
    setStatus("idle");
    setNodeStates({});
    setUsedNodes(new Set());
    setFinalOutput("");
    setErrorMsg("");
    setCodeContent(null);
    setFileName(null);
    setExecutionResult(null);
    setRightTab("output");
  }, []);

  const handleChunk = useCallback((chunk) => {
    const nodeName = Object.keys(chunk)[0];
    const updates  = chunk[nodeName];
    const summary  = extractNodeSummary(nodeName, updates);

    setUsedNodes(prev => new Set([...prev, nodeName]));

    if (nodeName === "code" && updates?.code) setCodeContent(updates.code);
    if (nodeName === "executor" && updates?.execution_result) setExecutionResult(updates.execution_result);
    if (nodeName === "file" && updates?.agent_outputs?.file) {
      const match = updates.agent_outputs.file.match(/outputs\/(.+)/);
      if (match) setFileName(match[1]);
    }

    setNodeStates(prev => {
      const next = { ...prev };
      Object.keys(next).forEach(n => {
        if (next[n].status === "active" && n !== nodeName)
          next[n] = { ...next[n], status: "done" };
      });
      next[nodeName] = { status: "active", summary: summary || prev[nodeName]?.summary || null };
      return next;
    });
  }, []);

  const submit = useCallback(async () => {
    if (!task.trim() || status === "running") return;
    reset();
    await new Promise(r => setTimeout(r, 50));

    try {
      const res = await fetch(`${API}/task`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task: task.trim() }),
      });
      const data = await res.json();
      const id = data.task_id;
      setStatus("running");

      const es = new EventSource(`${API}/task/${id}/stream`);
      esRef.current = es;

      es.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === "connected") return;

        if (msg.type === "chunk") {
          handleChunk(msg.data);

          // when synthesizer node starts, open a dedicated token stream
          const nodeName = msg.node || Object.keys(msg.data || {})[0];
          if (nodeName === "synthesizer" && !synthEsRef.current) {
            setRightTab("output");
            const synthEs = new EventSource(`${API}/task/${id}/synthesizer-stream`);
            synthEsRef.current = synthEs;

            synthEs.onmessage = (se) => {
              const sm = JSON.parse(se.data);
              if (sm.type === "token") {
                setFinalOutput(prev => prev + sm.text);
              }
              if (sm.type === "done" || sm.type === "error") {
                synthEs.close();
                synthEsRef.current = null;
              }
            };

            synthEs.onerror = () => {
              synthEs.close();
              synthEsRef.current = null;
            };
          }
        }

        if (msg.type === "done") {
          setNodeStates(prev => {
            const next = { ...prev };
            Object.keys(next).forEach(n => {
              if (next[n].status === "active") next[n] = { ...next[n], status: "done" };
            });
            return next;
          });
          // only fill from done if token stream didn't already populate it
          setFinalOutput(prev => prev || msg.result || "");
          setStatus("done");
          setRightTab("output");
          setHistory(h => [{ task: taskRef.current, result: msg.result, id }, ...h.slice(0, 19)]);
          es.close();
        }

        if (msg.type === "error") {
          setErrorMsg(msg.message || "Unknown error");
          setStatus("error");
          es.close();
        }
      };

      es.onerror = () => {
        setErrorMsg("Connection lost. Is the server running on :8000?");
        setStatus("error");
        es.close();
      };
    } catch (err) {
      setErrorMsg(err.message);
      setStatus("error");
    }
  }, [task, status, reset, handleChunk]);

  const handleKey = (e) => {
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
  };

  const isRunning = status === "running";
  const isDone    = status === "done";
  const hasCode   = !!codeContent;
  const hasFile   = !!fileName;
  const hasExec   = !!executionResult;

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:ital,wght@0,300;0,400;0,500;1,300&family=Syne:wght@400;500;600;700&display=swap');
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        html, body, #root { height: 100%; }
        body { background: #080808; color: #d4d4d4; font-family: 'Syne', sans-serif; overflow: hidden; }
        ::-webkit-scrollbar { width: 3px; height: 3px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #1a1a1a; border-radius: 2px; }
        textarea { font-family: 'DM Mono', monospace; }
        textarea:focus { outline: none; }
        button:hover:not(:disabled) { opacity: 0.75; }
        button:active:not(:disabled) { transform: scale(0.97); }
        @keyframes spin  { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.35; } }
        @keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0; } }
        @keyframes fadeIn  { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }
        @keyframes slideIn { from { opacity:0; transform:translateX(10px); } to { opacity:1; transform:translateX(0); } }
      `}</style>

      <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>

        {/* ══ LEFT PANEL ══ */}
        <div style={{
          width: `${leftWidth}px`, minWidth: "220px", maxWidth: "600px",
          display: "flex", flexDirection: "column",
          borderRight: "none",
          background: "#080808", flexShrink: 0,
        }}>
          {/* header — just the logo, no subtitle */}
          <div style={{ padding: "22px 22px 16px", borderBottom: "1px solid #0e0e0e" }}>
            <h1 style={{ fontSize: "20px", fontWeight: 700, letterSpacing: "-0.02em", color: "#f0f0f0" }}>
              Agent<span style={{ color: "#7C6AF7" }}>OS</span>
            </h1>
          </div>

          {/* input */}
          <div style={{ padding: "14px 22px", borderBottom: "1px solid #0e0e0e" }}>
            <div style={{
              background: "#0b0b0b", border: "1px solid #141414",
              borderRadius: "9px", padding: "11px 13px",
            }}>
              <textarea
                value={task}
                onChange={e => setTask(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Describe a task..."
                disabled={isRunning}
                rows={3}
                style={{
                  width: "100%", background: "transparent", border: "none",
                  resize: "none", color: "#c8c8c8", fontSize: "12px",
                  lineHeight: "1.7", caretColor: "#7C6AF7",
                }}
              />
              <div style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                marginTop: "9px", paddingTop: "9px", borderTop: "1px solid #0e0e0e",
              }}>
                <div style={{ display: "flex", gap: "5px" }}>
                  {(isRunning || isDone || status === "error") && (
                    <button onClick={reset} style={{
                      background: "transparent", border: "1px solid #161616",
                      color: "#444", padding: "4px 11px", borderRadius: "5px",
                      fontSize: "10px", cursor: "pointer", transition: "all 0.2s",
                      fontFamily: "'DM Mono', monospace",
                    }}>reset</button>
                  )}
                  <button onClick={submit} disabled={!task.trim() || isRunning} style={{
                    background: isRunning ? "#0f0f0f" : "#7C6AF7",
                    border: "none", color: isRunning ? "#2a2a2a" : "#fff",
                    padding: "4px 14px", borderRadius: "5px",
                    fontSize: "10px", fontWeight: 600,
                    cursor: isRunning ? "not-allowed" : "pointer",
                    transition: "all 0.2s", letterSpacing: "0.05em",
                    fontFamily: "'DM Mono', monospace",
                  }}>
                    {isRunning ? "running..." : "run →"}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* pipeline */}
          <div style={{ flex: 1, overflow: "auto", padding: "14px 22px" }}>
            {(isRunning || isDone || status === "error") && (
              <>
                <div style={{
                  fontSize: "8px", fontFamily: "'DM Mono', monospace",
                  color: "#999", letterSpacing: "0.22em", textTransform: "uppercase",
                  marginBottom: "14px",
                }}>Pipeline</div>

                {AGENT_ORDER.map((node, i) => {
                  const ns = nodeStates[node];
                  return (
                    <NodeCard
                      key={node} node={node}
                      status={ns?.status || "pending"}
                      summary={ns?.summary} index={i}
                      usedNodes={usedNodes}
                    />
                  );
                })}

                {status === "error" && (
                  <div style={{
                    background: "#0f0808", border: "1px solid #FF704320",
                    borderRadius: "7px", padding: "10px 12px", marginTop: "8px",
                    fontSize: "11px", color: "#FF7043",
                    fontFamily: "'DM Mono', monospace",
                    animation: "fadeIn 0.3s ease forwards",
                  }}>
                    ✕ {errorMsg}
                  </div>
                )}
              </>
            )}

            {status === "idle" && history.length > 0 && (
              <div>
                <div style={{
                  fontSize: "8px", fontFamily: "'DM Mono', monospace",
                  color: "#ffffff", letterSpacing: "0.22em", textTransform: "uppercase",
                  marginBottom: "10px",
                }}>Recent</div>
                {history.map((h, i) => (
                  <div key={i} onClick={() => setTask(h.task)} style={{
                    padding: "8px 11px", borderRadius: "6px",
                    border: "1px solid #ffffff", marginBottom: "4px",
                    cursor: "pointer", transition: "border-color 0.2s",
                  }}
                    onMouseEnter={e => e.currentTarget.style.borderColor = "#1a1a1a"}
                    onMouseLeave={e => e.currentTarget.style.borderColor = "#0e0e0e"}
                  >
                    <div style={{
                      fontSize: "11px", color: "#444", fontFamily: "'DM Mono', monospace",
                      whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                    }}>{h.task}</div>
                    {Array.isArray(h.plan) && h.plan.length > 0 && (
                      <div style={{ display: "flex", gap: "4px", flexWrap: "wrap", marginTop: "5px" }}>
                        {h.plan.map(agent => (
                          <span key={agent} style={{
                            fontSize: "8px", padding: "1px 5px", borderRadius: "3px",
                            fontFamily: "'DM Mono', monospace", letterSpacing: "0.05em",
                            background: (AGENT_META[agent]?.color || "#555") + "18",
                            color: AGENT_META[agent]?.color || "#555",
                            border: `1px solid ${(AGENT_META[agent]?.color || "#555")}25`,
                          }}>{agent}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {status === "idle" && history.length === 0 && (
              <div style={{
                display: "flex", flexDirection: "column", alignItems: "center",
                justifyContent: "center", height: "40vh", gap: "10px", opacity: 0.3,
              }}>
                <div style={{ fontSize: "28px", color: "#1a1a1a" }}>⬡</div>
                <div style={{ fontSize: "10px", color: "#1e1e1e", fontFamily: "'DM Mono', monospace", letterSpacing: "0.1em" }}>
                  no tasks yet
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </div>

        {/* ══ DIVIDER ══ */}
        <div
          onMouseDown={onDividerMouseDown}
          style={{
            width: "4px", flexShrink: 0, cursor: "col-resize",
            background: "transparent", position: "relative",
            transition: "background 0.15s",
          }}
          onMouseEnter={e => e.currentTarget.style.background = "#7C6AF733"}
          onMouseLeave={e => e.currentTarget.style.background = "transparent"}
        >
          <div style={{
            position: "absolute", top: 0, left: "1px",
            width: "2px", height: "100%", background: "#0e0e0e",
            pointerEvents: "none",
          }} />
        </div>

        {/* ══ RIGHT PANEL ══ */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "#060606" }}>

          {/* tab bar */}
          <div style={{
            display: "flex", alignItems: "stretch",
            borderBottom: "1px solid #0e0e0e",
            background: "#080808", height: "42px", flexShrink: 0,
            paddingLeft: "4px",
          }}>
            <TabBtn label="Output"    active={rightTab === "output"} onClick={() => setRightTab("output")} />
            {hasCode && <TabBtn label="Code"   active={rightTab === "code"} onClick={() => setRightTab("code")} badge="py" />}
            {hasFile && <TabBtn label="File"   active={rightTab === "file"} onClick={() => setRightTab("file")} badge={fileName} />}
            {hasExec && <TabBtn label="Result" active={rightTab === "exec"} onClick={() => setRightTab("exec")} />}

            <div style={{ flex: 1 }} />

            <div style={{ display: "flex", alignItems: "center", paddingRight: "20px" }}>
              {isRunning && (
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <div style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#7C6AF7", animation: "pulse 1s ease infinite" }} />
                  <span style={{ fontSize: "9px", color: "#2a2a2a", fontFamily: "'DM Mono', monospace", letterSpacing: "0.1em" }}>RUNNING</span>
                </div>
              )}
              {isDone && (
                <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                  <div style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#43E8A0" }} />
                  <span style={{ fontSize: "9px", color: "#2a2a2a", fontFamily: "'DM Mono', monospace", letterSpacing: "0.1em" }}>DONE</span>
                </div>
              )}
            </div>
          </div>

          {/* content */}
          <div style={{
            flex: 1, overflow: "auto",
            padding: (rightTab === "code" || rightTab === "file") ? "0" : "32px 36px",
          }}>

            {/* OUTPUT */}
            {rightTab === "output" && (
              <div style={{ animation: "slideIn 0.3s ease forwards", maxWidth: "100%" }}>

                {isRunning && !finalOutput && (
                  <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                    <span style={{ animation: "spin 1.2s linear infinite", display: "inline-block", fontSize: "13px", color: "#333" }}>◌</span>
                    <span style={{ fontSize: "11px", color: "#333", fontFamily: "'DM Mono', monospace", letterSpacing: "0.08em" }}>agents working...</span>
                  </div>
                )}

                {finalOutput && (
                  <div style={{ animation: "fadeIn 0.5s ease forwards" }}>
                    <div style={{
                      display: "flex", alignItems: "center", gap: "10px", marginBottom: "20px",
                    }}>
                      <span style={{ fontSize: "9px", fontFamily: "'DM Mono', monospace", color: "#A5D6A7", letterSpacing: "0.15em", textTransform: "uppercase" }}>
                        ◈ {isRunning ? "Synthesizing..." : "Final Output"}
                      </span>
                      <div style={{ flex: 1, height: "1px", background: "#0e0e0e" }} />
                    </div>
                    <div style={{ fontSize: "13px", fontFamily: "'DM Mono', monospace", lineHeight: "1.8" }}>
                      {renderMarkdown(finalOutput)}
                      {isRunning && (
                        <span style={{
                          display: "inline-block", width: "7px", height: "13px",
                          background: "#A5D6A7", marginLeft: "2px", verticalAlign: "text-bottom",
                          animation: "blink 1s step-end infinite",
                        }} />
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* CODE */}
            {rightTab === "code" && codeContent && (
              <div style={{ height: "100%", animation: "slideIn 0.25s ease forwards" }}>
                <CodeBlock code={codeContent} filename={fileName || "code.py"} />
              </div>
            )}

            {/* FILE */}
            {rightTab === "file" && (
              <div style={{ padding: "32px 36px", animation: "slideIn 0.25s ease forwards" }}>
                <div style={{
                  background: "#0a0a0a", border: "1px solid #141414",
                  borderRadius: "10px", padding: "18px 20px",
                  display: "inline-flex", flexDirection: "column", gap: "8px",
                }}>
                  <div style={{ fontSize: "9px", color: "#CE93D8", fontFamily: "'DM Mono', monospace", letterSpacing: "0.12em", textTransform: "uppercase" }}>
                    ◫ File Saved
                  </div>
                  <div style={{ fontSize: "13px", color: "#888", fontFamily: "'DM Mono', monospace" }}>
                    AgentOS/outputs/<span style={{ color: "#CE93D8" }}>{fileName}</span>
                  </div>
                  <div style={{ fontSize: "10px", color: "#333", fontFamily: "'DM Mono', monospace", marginTop: "4px" }}>
                    Check the outputs/ folder in your project directory.
                  </div>
                </div>
              </div>
            )}

            {/* EXECUTION RESULT */}
            {rightTab === "exec" && executionResult && (
              <div style={{ animation: "slideIn 0.25s ease forwards", maxWidth: "100%" }}>
                <div style={{
                  display: "flex", alignItems: "center", gap: "10px", marginBottom: "20px",
                }}>
                  <span style={{ fontSize: "9px", fontFamily: "'DM Mono', monospace", color: "#F7C948", letterSpacing: "0.15em", textTransform: "uppercase" }}>
                    ▶ Execution Output
                  </span>
                  <div style={{ flex: 1, height: "1px", background: "#0e0e0e" }} />
                </div>
                <pre style={{
                  background: "#0a0a0a", border: "1px solid #141414",
                  borderRadius: "8px", padding: "18px 20px",
                  fontSize: "12px", fontFamily: "'DM Mono', monospace",
                  color: "#F7C948", lineHeight: "1.8",
                  whiteSpace: "pre-wrap", wordBreak: "break-word",
                }}>
                  {executionResult}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
