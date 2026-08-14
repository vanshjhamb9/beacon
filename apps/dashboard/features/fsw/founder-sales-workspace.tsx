"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const STAGES = [
  { key: "revenue_ready", label: "Revenue Ready", color: "#3b82f6" },
  { key: "contacted", label: "Contacted", color: "#8b5cf6" },
  { key: "replied", label: "Replied", color: "#06b6d4" },
  { key: "meeting", label: "Meeting", color: "#f59e0b" },
  { key: "proposal", label: "Proposal", color: "#f97316" },
  { key: "negotiation", label: "Negotiation", color: "#ef4444" },
  { key: "won", label: "Won", color: "#22c55e" },
  { key: "lost", label: "Lost", color: "#6b7280" },
  { key: "archived", label: "Archived", color: "#9ca3af" },
  { key: "garbage", label: "Garbage", color: "#dc2626" },
];

const GARBAGE_REASONS = [
  "ai_company", "competitor", "duplicate", "closed", "no_buying_signal",
  "too_old", "wrong_industry", "wrong_geography", "already_customer", "spam", "other",
];

interface Lead {
  id: string;
  company_name: string;
  stage: string;
  manual_status: string | null;
  owner: string | null;
  revenue_opportunity_score: number;
  fit_score: number;
  intent_score: number;
  industry: string | null;
  country: string | null;
  service_match: string | null;
  source_connector: string | null;
  trigger: string | null;
  why_now: string | null;
  garbage_reason: string | null;
  snoozed_until: string | null;
  created_at: string;
  sort_order: number;
}

interface Note {
  id: string;
  content: string;
  author: string | null;
  is_pinned: boolean;
  created_at: string;
}

interface Task {
  id: string;
  title: string;
  description: string | null;
  due_date: string | null;
  priority: string;
  owner: string | null;
  completed: boolean;
  created_at: string;
}

interface TimelineEvent {
  id: string;
  event_type: string;
  title: string;
  description: string | null;
  actor: string | null;
  created_at: string;
}

export function FounderSalesWorkspace() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [stageCounts, setStageCounts] = useState<Record<string, number>>({});
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [activeTab, setActiveTab] = useState<"details" | "notes" | "tasks" | "timeline">("details");
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [draggedLead, setDraggedLead] = useState<Lead | null>(null);
  const [showGarbageModal, setShowGarbageModal] = useState(false);
  const [garbageReason, setGarbageReason] = useState("");
  const [garbageNote, setGarbageNote] = useState("");
  const [notes, setNotes] = useState<Note[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [newNote, setNewNote] = useState("");
  const [newTask, setNewTask] = useState({ title: "", due_date: "", priority: "medium" });
  const [filters, setFilters] = useState<Record<string, string>>({});

  const fetchLeads = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
      const res = await fetch(`${API}/fsw/leads?${params}`);
      const data = await res.json();
      setLeads(data.items || []);
      setStageCounts(data.stage_counts || {});
    } catch (e) { console.error("Failed to fetch leads:", e); }
    setLoading(false);
  }, [search, filters]);

  useEffect(() => { fetchLeads(); }, [fetchLeads]);

  useEffect(() => {
    if (!selectedLead) return;
    const loadDetails = async () => {
      const [n, t, tl] = await Promise.all([
        fetch(`${API}/fsw/leads/${selectedLead.id}/notes`).then(r => r.json()),
        fetch(`${API}/fsw/leads/${selectedLead.id}/tasks`).then(r => r.json()),
        fetch(`${API}/fsw/leads/${selectedLead.id}/timeline`).then(r => r.json()),
      ]);
      setNotes(n); setTasks(t); setTimeline(tl);
    };
    loadDetails();
  }, [selectedLead]);

  const handleDragStart = (lead: Lead) => setDraggedLead(lead);
  const handleDragEnd = () => setDraggedLead(null);

  const handleDrop = async (targetStage: string) => {
    if (!draggedLead || draggedLead.stage === targetStage) return;
    if (targetStage === "garbage") {
      setDraggedLead(draggedLead);
      setShowGarbageModal(true);
      return;
    }
    try {
      await fetch(`${API}/fsw/leads/${draggedLead.id}/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stage: targetStage }),
      });
      fetchLeads();
      if (selectedLead?.id === draggedLead.id) {
        setSelectedLead({ ...draggedLead, stage: targetStage });
      }
    } catch (e) { console.error("Move failed:", e); }
    setDraggedLead(null);
  };

  const handleGarbage = async () => {
    if (!draggedLead || !garbageReason) return;
    try {
      await fetch(`${API}/fsw/leads/${draggedLead.id}/garbage`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: garbageReason, note: garbageNote }),
      });
      fetchLeads();
      setShowGarbageModal(false);
      setGarbageReason("");
      setGarbageNote("");
    } catch (e) { console.error("Garbage failed:", e); }
    setDraggedLead(null);
  };

  const handleBulkMove = async (stage: string) => {
    if (selectedIds.size === 0) return;
    try {
      await fetch(`${API}/fsw/bulk/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lead_ids: Array.from(selectedIds), stage }),
      });
      setSelectedIds(new Set());
      fetchLeads();
    } catch (e) { console.error("Bulk move failed:", e); }
  };

  const handleBulkDelete = async () => {
    if (selectedIds.size === 0) return;
    if (!confirm(`Delete ${selectedIds.size} leads?`)) return;
    try {
      await fetch(`${API}/fsw/bulk/delete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lead_ids: Array.from(selectedIds) }),
      });
      setSelectedIds(new Set());
      fetchLeads();
    } catch (e) { console.error("Bulk delete failed:", e); }
  };

  const addNote = async () => {
    if (!selectedLead || !newNote.trim()) return;
    try {
      await fetch(`${API}/fsw/leads/${selectedLead.id}/notes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: newNote }),
      });
      setNewNote("");
      const res = await fetch(`${API}/fsw/leads/${selectedLead.id}/notes`);
      setNotes(await res.json());
    } catch (e) { console.error("Add note failed:", e); }
  };

  const addTask = async () => {
    if (!selectedLead || !newTask.title.trim()) return;
    try {
      await fetch(`${API}/fsw/leads/${selectedLead.id}/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newTask),
      });
      setNewTask({ title: "", due_date: "", priority: "medium" });
      const res = await fetch(`${API}/fsw/leads/${selectedLead.id}/tasks`);
      setTasks(await res.json());
    } catch (e) { console.error("Add task failed:", e); }
  };

  const completeTask = async (taskId: string) => {
    try {
      await fetch(`${API}/fsw/tasks/${taskId}/complete`, { method: "POST" });
      setTasks(prev => prev.map(t => t.id === taskId ? { ...t, completed: true } : t));
    } catch (e) { console.error("Complete task failed:", e); }
  };

  const setManualStatus = async (status: string) => {
    if (!selectedLead) return;
    try {
      await fetch(`${API}/fsw/leads/${selectedLead.id}/status`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      });
      setSelectedLead({ ...selectedLead, manual_status: status });
      fetchLeads();
    } catch (e) { console.error("Set status failed:", e); }
  };

  const groupedLeads = useMemo(() => {
    const groups: Record<string, Lead[]> = {};
    STAGES.forEach(s => groups[s.key] = []);
    leads.forEach(l => { if (groups[l.stage]) groups[l.stage].push(l); });
    return groups;
  }, [leads]);

  const toggleSelect = (id: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  if (loading) return <div className="flex items-center justify-center h-96 text-gray-500">Loading FSW...</div>;

  return (
    <div className="flex flex-col h-full">
      {/* Top Bar */}
      <div className="flex items-center gap-4 px-4 py-3 border-b bg-white">
        <h1 className="text-lg font-semibold">Founder Sales Workspace</h1>
        <input
          type="text"
          placeholder="Search leads..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 max-w-sm px-3 py-1.5 border rounded-lg text-sm"
        />
        {selectedIds.size > 0 && (
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">{selectedIds.size} selected</span>
            <button onClick={() => handleBulkMove("contacted")} className="px-2 py-1 bg-blue-100 rounded">Move to Contacted</button>
            <button onClick={() => handleBulkMove("archived")} className="px-2 py-1 bg-gray-100 rounded">Archive</button>
            <button onClick={handleBulkDelete} className="px-2 py-1 bg-red-100 rounded text-red-700">Delete</button>
          </div>
        )}
      </div>

      {/* Kanban Board */}
      <div className="flex-1 overflow-x-auto p-4">
        <div className="flex gap-4 h-full min-w-max">
          {STAGES.map(stage => (
            <div
              key={stage.key}
              className="flex flex-col w-72 bg-gray-50 rounded-xl"
              onDragOver={e => e.preventDefault()}
              onDrop={() => handleDrop(stage.key)}
            >
              <div className="flex items-center gap-2 px-3 py-2 border-b">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: stage.color }} />
                <span className="text-sm font-medium">{stage.label}</span>
                <span className="text-xs text-gray-400 ml-auto">{stageCounts[stage.key] || 0}</span>
              </div>
              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {groupedLeads[stage.key]?.map(lead => (
                  <motion.div
                    key={lead.id}
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`bg-white rounded-lg p-3 border cursor-pointer hover:shadow-md transition-shadow ${
                      selectedIds.has(lead.id) ? "ring-2 ring-blue-500" : ""
                    }`}
                    draggable
                    onDragStart={() => handleDragStart(lead)}
                    onDragEnd={handleDragEnd}
                    onClick={() => { setSelectedLead(lead); setActiveTab("details"); }}
                  >
                    <div className="flex items-start gap-2">
                      <input
                        type="checkbox"
                        checked={selectedIds.has(lead.id)}
                        onChange={() => toggleSelect(lead.id)}
                        onClick={e => e.stopPropagation()}
                        className="mt-0.5"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="text-sm font-medium truncate">{lead.company_name}</div>
                        <div className="text-xs text-gray-500 mt-0.5">
                          ROS {lead.revenue_opportunity_score.toFixed(0)} | {lead.industry || "-"}
                        </div>
                        {lead.why_now && (
                          <div className="text-xs text-gray-400 mt-1 line-clamp-2">{lead.why_now}</div>
                        )}
                        <div className="flex items-center gap-2 mt-2">
                          {lead.owner && (
                            <span className="text-xs bg-purple-100 text-purple-700 px-1.5 rounded">{lead.owner}</span>
                          )}
                          {lead.manual_status && (
                            <span className="text-xs bg-green-100 text-green-700 px-1.5 rounded">{lead.manual_status}</span>
                          )}
                          {lead.snoozed_until && (
                            <span className="text-xs bg-yellow-100 text-yellow-700 px-1.5 rounded">Snoozed</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Lead Detail Slide-over */}
      <AnimatePresence>
        {selectedLead && (
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            className="fixed right-0 top-0 h-full w-[480px] bg-white border-l shadow-xl z-50 flex flex-col"
          >
            <div className="flex items-center justify-between px-4 py-3 border-b">
              <h2 className="font-semibold">{selectedLead.company_name}</h2>
              <button onClick={() => setSelectedLead(null)} className="text-gray-400 hover:text-gray-600">X</button>
            </div>

            {/* Tabs */}
            <div className="flex border-b">
              {(["details", "notes", "tasks", "timeline"] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-4 py-2 text-sm capitalize ${activeTab === tab ? "border-b-2 border-blue-500 text-blue-600" : "text-gray-500"}`}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="flex-1 overflow-y-auto p-4">
              {activeTab === "details" && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div><span className="text-gray-500">Stage:</span> {selectedLead.stage}</div>
                    <div><span className="text-gray-500">ROS:</span> {selectedLead.revenue_opportunity_score.toFixed(1)}</div>
                    <div><span className="text-gray-500">Fit:</span> {selectedLead.fit_score.toFixed(0)}</div>
                    <div><span className="text-gray-500">Intent:</span> {selectedLead.intent_score.toFixed(0)}</div>
                    <div><span className="text-gray-500">Industry:</span> {selectedLead.industry || "-"}</div>
                    <div><span className="text-gray-500">Country:</span> {selectedLead.country || "-"}</div>
                    <div><span className="text-gray-500">Service:</span> {selectedLead.service_match || "-"}</div>
                    <div><span className="text-gray-500">Source:</span> {selectedLead.source_connector || "-"}</div>
                  </div>

                  {selectedLead.why_now && (
                    <div className="text-sm"><span className="text-gray-500">Why Now:</span> {selectedLead.why_now}</div>
                  )}

                  {/* Actions */}
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-gray-700">Quick Actions</h3>
                    <div className="grid grid-cols-2 gap-2">
                      <button className="px-3 py-2 bg-blue-50 text-blue-700 rounded text-sm hover:bg-blue-100">Generate Email</button>
                      <button className="px-3 py-2 bg-green-50 text-green-700 rounded text-sm hover:bg-green-100">Generate WhatsApp</button>
                      <button className="px-3 py-2 bg-purple-50 text-purple-700 rounded text-sm hover:bg-purple-100">Generate Proposal</button>
                      <button className="px-3 py-2 bg-amber-50 text-amber-700 rounded text-sm hover:bg-amber-100">Schedule Meeting</button>
                    </div>
                  </div>

                  {/* Move */}
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-gray-700">Move to Stage</h3>
                    <div className="flex flex-wrap gap-1">
                      {STAGES.filter(s => s.key !== selectedLead.stage).map(s => (
                        <button
                          key={s.key}
                          onClick={async () => {
                            if (s.key === "garbage") {
                              setShowGarbageModal(true);
                              return;
                            }
                            await fetch(`${API}/fsw/leads/${selectedLead.id}/move`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ stage: s.key }),
                            });
                            setSelectedLead({ ...selectedLead, stage: s.key });
                            fetchLeads();
                          }}
                          className="px-2 py-1 text-xs rounded border hover:bg-gray-100"
                        >
                          {s.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Manual Status */}
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-gray-700">Manual Status</h3>
                    <div className="flex flex-wrap gap-1">
                      {["hot", "warm", "cold", "follow_up", "waiting", "done", null].map(s => (
                        <button
                          key={s || "none"}
                          onClick={() => setManualStatus(s || "")}
                          className={`px-2 py-1 text-xs rounded border ${
                            selectedLead.manual_status === s ? "bg-blue-100 border-blue-300" : "hover:bg-gray-100"
                          }`}
                        >
                          {s || "Clear"}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Snooze */}
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium text-gray-700">Snooze</h3>
                    <div className="flex gap-2">
                      {[1, 3, 7].map(days => (
                        <button
                          key={days}
                          onClick={async () => {
                            const until = new Date(Date.now() + days * 86400000).toISOString();
                            await fetch(`${API}/fsw/leads/${selectedLead.id}/snooze`, {
                              method: "POST",
                              headers: { "Content-Type": "application/json" },
                              body: JSON.stringify({ until }),
                            });
                            setSelectedLead({ ...selectedLead, snoozed_until: until });
                          }}
                          className="px-2 py-1 text-xs rounded border hover:bg-gray-100"
                        >
                          {days}d
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Archive / Delete */}
                  <div className="flex gap-2">
                    <button
                      onClick={async () => {
                        await fetch(`${API}/fsw/leads/${selectedLead.id}/archive`, { method: "POST" });
                        setSelectedLead(null);
                        fetchLeads();
                      }}
                      className="px-3 py-2 bg-gray-100 text-gray-700 rounded text-sm hover:bg-gray-200"
                    >
                      Archive
                    </button>
                    <button
                      onClick={async () => {
                        if (!confirm("Send to garbage?")) return;
                        setShowGarbageModal(true);
                      }}
                      className="px-3 py-2 bg-red-50 text-red-700 rounded text-sm hover:bg-red-100"
                    >
                      Garbage
                    </button>
                  </div>
                </div>
              )}

              {activeTab === "notes" && (
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <input
                      value={newNote}
                      onChange={e => setNewNote(e.target.value)}
                      placeholder="Add a note..."
                      className="flex-1 px-3 py-2 border rounded-lg text-sm"
                      onKeyDown={e => e.key === "Enter" && addNote()}
                    />
                    <button onClick={addNote} className="px-3 py-2 bg-blue-500 text-white rounded-lg text-sm">Add</button>
                  </div>
                  {notes.map(note => (
                    <div key={note.id} className="p-3 bg-gray-50 rounded-lg text-sm">
                      <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
                        <span>{note.author || "System"}</span>
                        <span>{new Date(note.created_at).toLocaleString()}</span>
                        {note.is_pinned && <span className="text-yellow-500">Pinned</span>}
                      </div>
                      <div>{note.content}</div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === "tasks" && (
                <div className="space-y-3">
                  <div className="flex gap-2">
                    <input
                      value={newTask.title}
                      onChange={e => setNewTask({ ...newTask, title: e.target.value })}
                      placeholder="New task..."
                      className="flex-1 px-3 py-2 border rounded-lg text-sm"
                      onKeyDown={e => e.key === "Enter" && addTask()}
                    />
                    <select
                      value={newTask.priority}
                      onChange={e => setNewTask({ ...newTask, priority: e.target.value })}
                      className="px-2 py-1 border rounded text-sm"
                    >
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                    <button onClick={addTask} className="px-3 py-2 bg-blue-500 text-white rounded-lg text-sm">Add</button>
                  </div>
                  {tasks.map(task => (
                    <div key={task.id} className={`p-3 rounded-lg text-sm ${task.completed ? "bg-green-50 line-through" : "bg-gray-50"}`}>
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={task.completed}
                          onChange={() => completeTask(task.id)}
                        />
                        <span className="flex-1">{task.title}</span>
                        <span className={`text-xs px-1.5 rounded ${
                          task.priority === "urgent" ? "bg-red-100 text-red-700" :
                          task.priority === "high" ? "bg-orange-100 text-orange-700" :
                          "bg-gray-100 text-gray-600"
                        }`}>{task.priority}</span>
                      </div>
                      {task.due_date && (
                        <div className="text-xs text-gray-400 mt-1">Due: {new Date(task.due_date).toLocaleDateString()}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {activeTab === "timeline" && (
                <div className="space-y-3">
                  {timeline.map(event => (
                    <div key={event.id} className="flex gap-3 text-sm">
                      <div className="w-2 h-2 mt-2 rounded-full bg-blue-400 shrink-0" />
                      <div>
                        <div className="font-medium">{event.title}</div>
                        <div className="text-xs text-gray-400">
                          {event.actor && <span>{event.actor} - </span>}
                          {new Date(event.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Garbage Modal */}
      {showGarbageModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[60]">
          <div className="bg-white rounded-xl p-6 w-96 space-y-4">
            <h3 className="font-semibold">Send to Garbage</h3>
            <select
              value={garbageReason}
              onChange={e => setGarbageReason(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg text-sm"
            >
              <option value="">Select reason...</option>
              {GARBAGE_REASONS.map(r => (
                <option key={r} value={r}>{r.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase())}</option>
              ))}
            </select>
            <textarea
              value={garbageNote}
              onChange={e => setGarbageNote(e.target.value)}
              placeholder="Optional note..."
              className="w-full px-3 py-2 border rounded-lg text-sm"
              rows={3}
            />
            <div className="flex justify-end gap-2">
              <button onClick={() => setShowGarbageModal(false)} className="px-4 py-2 text-gray-600 rounded-lg text-sm">Cancel</button>
              <button onClick={handleGarbage} disabled={!garbageReason} className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm disabled:opacity-50">Confirm</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
