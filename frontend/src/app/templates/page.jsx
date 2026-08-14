"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  Plus,
  Play,
  Clock,
  HelpCircle,
  BarChart2,
  Trash2,
  Edit2,
  CheckCircle2,
  AlertCircle,
  X,
  Layers,
  Sparkles
} from "lucide-react";
import { endpoints } from "@/lib/api";

export default function TemplatesPage() {
  const router = useRouter();

  // State
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Modals state
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isStartOpen, setIsStartOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  // Form State
  const [formData, setFormData] = useState({
    name: "",
    domain: "python",
    interview_type: "mixed",
    description: "",
    duration_minutes: 45,
    question_count: 10,
    technical_pct: 40,
    behavioral_pct: 30,
    situational_pct: 30,
  });

  // Start Interview Form State
  const [startForm, setStartForm] = useState({
    candidate_id: "",
    candidate_name: "",
    position: "",
    priority: "medium",
  });
  const [starting, setStarting] = useState(false);

  // Fetch templates
  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError("");
      const res = await endpoints.templates();
      if (res && res.templates) {
        setTemplates(res.templates);
      } else {
        setTemplates([]);
      }
    } catch (err) {
      console.error("Failed to load templates:", err);
      setError(err.message || "Failed to load interview templates.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTemplates();
  }, []);

  // Form handlers
  const handleOpenCreate = () => {
    setFormData({
      name: "Python Dev - 45 min",
      domain: "python",
      interview_type: "mixed",
      description: "Standard Python Developer template with 40% technical, 30% behavioral, 30% situational distribution.",
      duration_minutes: 45,
      question_count: 10,
      technical_pct: 40,
      behavioral_pct: 30,
      situational_pct: 30,
    });
    setIsCreateOpen(true);
  };

  const handleOpenEdit = (template) => {
    setSelectedTemplate(template);
    const catDist = template.category_distribution || { technical: 0.4, behavioral: 0.3, situational: 0.3 };
    
    // Check if values are decimals or percentages
    const tPct = catDist.technical <= 1 ? Math.round(catDist.technical * 100) : catDist.technical;
    const bPct = catDist.behavioral <= 1 ? Math.round(catDist.behavioral * 100) : catDist.behavioral;
    const sPct = catDist.situational <= 1 ? Math.round(catDist.situational * 100) : catDist.situational;

    setFormData({
      name: template.name || "",
      domain: template.domain || "python",
      interview_type: template.interview_type || "mixed",
      description: template.description || "",
      duration_minutes: template.duration_minutes || 45,
      question_count: template.question_count || 10,
      technical_pct: tPct,
      behavioral_pct: bPct,
      situational_pct: sPct,
    });
    setIsEditOpen(true);
  };

  const handleOpenStart = (template) => {
    setSelectedTemplate(template);
    setStartForm({
      candidate_id: `cand_${Math.floor(1000 + Math.random() * 9000)}`,
      candidate_name: "",
      position: template.name,
      priority: "medium",
    });
    setIsStartOpen(true);
  };

  const handleSaveTemplate = async (e) => {
    e.preventDefault();
    setError("");

    // Validate percentage sum = 100%
    const totalPct =
      Number(formData.technical_pct) +
      Number(formData.behavioral_pct) +
      Number(formData.situational_pct);

    if (totalPct !== 100) {
      setError(`Category distribution must sum to 100%. Current sum: ${totalPct}%`);
      return;
    }

    const payload = {
      name: formData.name,
      domain: formData.domain,
      interview_type: formData.interview_type,
      description: formData.description,
      duration_minutes: Number(formData.duration_minutes),
      question_count: Number(formData.question_count),
      category_distribution: {
        technical: Number(formData.technical_pct) / 100,
        behavioral: Number(formData.behavioral_pct) / 100,
        situational: Number(formData.situational_pct) / 100,
      },
    };

    try {
      if (isEditOpen && selectedTemplate) {
        await endpoints.updateTemplate(selectedTemplate.template_id, payload);
        setSuccessMsg(`Template "${formData.name}" updated successfully!`);
        setIsEditOpen(false);
      } else {
        await endpoints.createTemplate(payload);
        setSuccessMsg(`Template "${formData.name}" created successfully!`);
        setIsCreateOpen(false);
      }
      fetchTemplates();
      setTimeout(() => setSuccessMsg(""), 4000);
    } catch (err) {
      setError(err.message || "Error saving template.");
    }
  };

  const handleDeleteTemplate = async (templateId, templateName) => {
    if (!confirm(`Are you sure you want to delete template "${templateName}"?`)) return;
    try {
      await endpoints.deleteTemplate(templateId);
      setSuccessMsg(`Template "${templateName}" deleted successfully.`);
      fetchTemplates();
      setTimeout(() => setSuccessMsg(""), 4000);
    } catch (err) {
      setError(err.message || "Failed to delete template.");
    }
  };

  const handleStartInterview = async (e) => {
    e.preventDefault();
    if (!startForm.candidate_id) {
      setError("Please enter a Candidate ID.");
      return;
    }

    try {
      setStarting(true);
      setError("");
      const payload = {
        candidate_id: startForm.candidate_id.trim(),
        candidate_name: startForm.candidate_name.trim() || undefined,
        position: startForm.position.trim() || undefined,
        priority: startForm.priority,
        template_id: selectedTemplate.template_id,
      };

      const res = await endpoints.startInterview(payload);
      setSuccessMsg(`Interview started for candidate ${res.candidate_id}! Session ID: ${res.session_id}`);
      setIsStartOpen(false);
      setTimeout(() => {
        router.push(`/sessions`);
      }, 1200);
    } catch (err) {
      setError(err.message || "Failed to start interview session.");
    } finally {
      setStarting(false);
    }
  };

  // Helper for Category Bar colors
  const getCategoryPercent = (template, catName) => {
    const dist = template.category_distribution || {};
    const val = dist[catName] ?? 0;
    return val <= 1 ? Math.round(val * 100) : val;
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header Banner */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between rounded-xl bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-bg-panel border border-border p-6 shadow-xl backdrop-blur-md">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-lg bg-accent/20 text-accent-light border border-accent/30">
              <FileText size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-zinc-100 tracking-tight">Interview Templates</h1>
              <p className="text-sm text-zinc-400">
                Create and manage reusable domain templates (Python Dev, Data Science, Web Dev) with configured category distributions.
              </p>
            </div>
          </div>
        </div>

        <button
          onClick={handleOpenCreate}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-accent hover:bg-accent/90 text-white font-medium transition shadow-lg shadow-accent/20 active:scale-95"
        >
          <Plus size={18} />
          Create Template
        </button>
      </div>

      {/* Notifications */}
      {successMsg && (
        <div className="flex items-center gap-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 p-4 text-emerald-400 text-sm animate-in fade-in duration-200">
          <CheckCircle2 size={18} className="shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {error && (
        <div className="flex items-center gap-3 rounded-lg bg-red-500/10 border border-red-500/30 p-4 text-red-400 text-sm animate-in fade-in duration-200">
          <AlertCircle size={18} className="shrink-0" />
          <span>{error}</span>
          <button onClick={() => setError("")} className="ml-auto text-zinc-400 hover:text-white">
            <X size={16} />
          </button>
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map((n) => (
            <div key={n} className="h-64 rounded-xl border border-border bg-bg-panel p-6 animate-pulse space-y-4">
              <div className="h-6 w-3/4 bg-zinc-800 rounded"></div>
              <div className="h-4 w-1/2 bg-zinc-800/60 rounded"></div>
              <div className="h-16 bg-zinc-800/40 rounded-lg"></div>
              <div className="h-10 bg-zinc-800/80 rounded-lg"></div>
            </div>
          ))}
        </div>
      ) : templates.length === 0 ? (
        /* Empty State */
        <div className="flex flex-col items-center justify-center py-16 px-4 rounded-xl border border-dashed border-border bg-bg-panel/50 text-center space-y-4">
          <div className="p-4 rounded-full bg-accent/10 text-accent">
            <Layers size={36} />
          </div>
          <h3 className="text-lg font-semibold text-zinc-200">No Interview Templates Found</h3>
          <p className="text-sm text-zinc-400 max-w-md">
            Get started by creating standard interview templates for Python Developer, Data Science, or Web Development roles.
          </p>
          <button
            onClick={handleOpenCreate}
            className="px-4 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent/90 transition"
          >
            Create New Template
          </button>
        </div>
      ) : (
        /* Template Cards Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((template) => {
            const tech = getCategoryPercent(template, "technical");
            const beh = getCategoryPercent(template, "behavioral");
            const sit = getCategoryPercent(template, "situational");

            return (
              <div
                key={template.template_id}
                className="group relative flex flex-col justify-between rounded-xl border border-border bg-bg-panel p-6 transition-all duration-200 hover:border-accent/40 hover:shadow-xl hover:shadow-accent/5"
              >
                <div>
                  {/* Top Row: Title & Domain Badge */}
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div>
                      <h3 className="font-semibold text-lg text-zinc-100 group-hover:text-accent-light transition">
                        {template.name}
                      </h3>
                      <span className="inline-flex items-center gap-1 mt-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 uppercase tracking-wider">
                        <Sparkles size={12} />
                        {template.domain || "Python"}
                      </span>
                    </div>

                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleOpenEdit(template)}
                        className="p-1.5 rounded-md text-zinc-400 hover:text-white hover:bg-bg-card transition"
                        title="Edit Template"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => handleDeleteTemplate(template.template_id, template.name)}
                        className="p-1.5 rounded-md text-zinc-400 hover:text-red-400 hover:bg-red-500/10 transition"
                        title="Delete Template"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>

                  {/* Description */}
                  <p className="text-xs text-zinc-400 line-clamp-2 mb-4">
                    {template.description || "Reusable interview structure template."}
                  </p>

                  {/* Key Stats Row */}
                  <div className="grid grid-cols-2 gap-3 p-3 rounded-lg bg-bg/60 border border-border/60 mb-4">
                    <div className="flex items-center gap-2">
                      <Clock size={16} className="text-accent-light" />
                      <div>
                        <div className="text-[10px] uppercase text-zinc-400">Duration</div>
                        <div className="text-xs font-medium text-zinc-200">{template.duration_minutes} min</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <HelpCircle size={16} className="text-emerald-400" />
                      <div>
                        <div className="text-[10px] uppercase text-zinc-400">Questions</div>
                        <div className="text-xs font-medium text-zinc-200">{template.question_count} items</div>
                      </div>
                    </div>
                  </div>

                  {/* Category Distribution Section */}
                  <div className="space-y-2 mb-6">
                    <div className="flex items-center justify-between text-xs text-zinc-300">
                      <span className="font-medium">Category Distribution</span>
                      <span className="text-[11px] text-zinc-400">Total: 100%</span>
                    </div>

                    {/* Multi-segment Progress Bar */}
                    <div className="h-2.5 w-full rounded-full bg-zinc-800 overflow-hidden flex">
                      <div
                        style={{ width: `${tech}%` }}
                        className="bg-blue-500 transition-all duration-300"
                        title={`Technical: ${tech}%`}
                      />
                      <div
                        style={{ width: `${beh}%` }}
                        className="bg-purple-500 transition-all duration-300"
                        title={`Behavioral: ${beh}%`}
                      />
                      <div
                        style={{ width: `${sit}%` }}
                        className="bg-amber-500 transition-all duration-300"
                        title={`Situational: ${sit}%`}
                      />
                    </div>

                    {/* Breakdown Badges */}
                    <div className="grid grid-cols-3 gap-1 pt-1 text-[11px]">
                      <div className="flex items-center gap-1.5 text-blue-400">
                        <span className="h-2 w-2 rounded-full bg-blue-500" />
                        <span>Tech: {tech}%</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-purple-400">
                        <span className="h-2 w-2 rounded-full bg-purple-500" />
                        <span>Beh: {beh}%</span>
                      </div>
                      <div className="flex items-center gap-1.5 text-amber-400">
                        <span className="h-2 w-2 rounded-full bg-amber-500" />
                        <span>Sit: {sit}%</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Footer Action */}
                <button
                  onClick={() => handleOpenStart(template)}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-accent/15 hover:bg-accent text-accent-light hover:text-white font-medium text-sm border border-accent/30 transition shadow-sm"
                >
                  <Play size={16} />
                  Start Interview with Template
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* CREATE / EDIT TEMPLATE MODAL */}
      {(isCreateOpen || isEditOpen) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-lg rounded-xl border border-border bg-bg-panel p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <h2 className="text-lg font-bold text-zinc-100">
                {isEditOpen ? "Edit Interview Template" : "Create New Interview Template"}
              </h2>
              <button
                onClick={() => {
                  setIsCreateOpen(false);
                  setIsEditOpen(false);
                }}
                className="text-zinc-400 hover:text-white"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSaveTemplate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Template Name</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Python Dev - 45 min"
                  className="w-full rounded-lg border border-border bg-bg p-2.5 text-sm text-zinc-100 focus:border-accent focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-300 mb-1">Domain</label>
                  <select
                    value={formData.domain}
                    onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                    className="w-full rounded-lg border border-border bg-bg p-2.5 text-sm text-zinc-100 focus:border-accent focus:outline-none"
                  >
                    <option value="python">Python Developer</option>
                    <option value="data_science">Data Science</option>
                    <option value="web_dev">Web Development</option>
                    <option value="general">General Software Eng</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-zinc-300 mb-1">Interview Type</label>
                  <select
                    value={formData.interview_type}
                    onChange={(e) => setFormData({ ...formData, interview_type: e.target.value })}
                    className="w-full rounded-lg border border-border bg-bg p-2.5 text-sm text-zinc-100 focus:border-accent focus:outline-none"
                  >
                    <option value="mixed">Mixed</option>
                    <option value="technical">Technical Focus</option>
                    <option value="behavioral">Behavioral Focus</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-zinc-300 mb-1">Duration (Minutes)</label>
                  <input
                    type="number"
                    min="5"
                    max="180"
                    value={formData.duration_minutes}
                    onChange={(e) => setFormData({ ...formData, duration_minutes: e.target.value })}
                    className="w-full rounded-lg border border-border bg-bg p-2.5 text-sm text-zinc-100 focus:border-accent focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-zinc-300 mb-1">Question Count</label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={formData.question_count}
                    onChange={(e) => setFormData({ ...formData, question_count: e.target.value })}
                    className="w-full rounded-lg border border-border bg-bg p-2.5 text-sm text-zinc-100 focus:border-accent focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Description</label>
                <textarea
                  rows="2"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Optional description..."
                  className="w-full rounded-lg border border-border bg-bg p-2.5 text-sm text-zinc-100 focus:border-accent focus:outline-none"
                />
              </div>

              {/* Category Distribution inputs */}
              <div className="p-3.5 rounded-lg bg-bg/80 border border-border space-y-3">
                <div className="flex justify-between items-center text-xs font-medium text-zinc-200">
                  <span>Category Distribution (%)</span>
                  <span
                    className={
                      Number(formData.technical_pct) +
                        Number(formData.behavioral_pct) +
                        Number(formData.situational_pct) ===
                      100
                        ? "text-emerald-400 font-semibold"
                        : "text-amber-400 font-semibold"
                    }
                  >
                    Sum:{" "}
                    {Number(formData.technical_pct) +
                      Number(formData.behavioral_pct) +
                      Number(formData.situational_pct)}
                    % / 100%
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="block text-[11px] text-blue-400 mb-1">Technical %</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={formData.technical_pct}
                      onChange={(e) => setFormData({ ...formData, technical_pct: e.target.value })}
                      className="w-full rounded-md border border-border bg-bg p-2 text-xs text-zinc-100 focus:border-accent focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-purple-400 mb-1">Behavioral %</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={formData.behavioral_pct}
                      onChange={(e) => setFormData({ ...formData, behavioral_pct: e.target.value })}
                      className="w-full rounded-md border border-border bg-bg p-2 text-xs text-zinc-100 focus:border-accent focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] text-amber-400 mb-1">Situational %</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={formData.situational_pct}
                      onChange={(e) => setFormData({ ...formData, situational_pct: e.target.value })}
                      className="w-full rounded-md border border-border bg-bg p-2 text-xs text-zinc-100 focus:border-accent focus:outline-none"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setIsCreateOpen(false);
                    setIsEditOpen(false);
                  }}
                  className="px-4 py-2 rounded-lg border border-border text-zinc-300 text-sm hover:bg-bg-card transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent/90 transition shadow-md shadow-accent/20"
                >
                  {isEditOpen ? "Update Template" : "Save Template"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* START INTERVIEW MODAL */}
      {isStartOpen && selectedTemplate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-xl border border-border bg-bg-panel p-6 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-border pb-4">
              <div>
                <h2 className="text-lg font-bold text-zinc-100">Start Interview Session</h2>
                <p className="text-xs text-accent-light">Using Template: {selectedTemplate.name}</p>
              </div>
              <button onClick={() => setIsStartOpen(false)} className="text-zinc-400 hover:text-white">
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleStartInterview} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Candidate ID *</label>
                <input
                  type="text"
                  required
                  value={startForm.candidate_id}
                  onChange={(e) => setStartForm({ ...startForm, candidate_id: e.target.value })}
                  placeholder="e.g. cand_1001"
                  className="w-full rounded-lg border border-border bg-bg p-2.5 text-sm text-zinc-100 focus:border-accent focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Candidate Name</label>
                <input
                  type="text"
                  value={startForm.candidate_name}
                  onChange={(e) => setStartForm({ ...startForm, candidate_name: e.target.value })}
                  placeholder="e.g. Alex Johnson"
                  className="w-full rounded-lg border border-border bg-bg p-2.5 text-sm text-zinc-100 focus:border-accent focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Position / Role</label>
                <input
                  type="text"
                  value={startForm.position}
                  onChange={(e) => setStartForm({ ...startForm, position: e.target.value })}
                  placeholder="e.g. Senior Python Developer"
                  className="w-full rounded-lg border border-border bg-bg p-2.5 text-sm text-zinc-100 focus:border-accent focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-zinc-300 mb-1">Priority</label>
                <select
                  value={startForm.priority}
                  onChange={(e) => setStartForm({ ...startForm, priority: e.target.value })}
                  className="w-full rounded-lg border border-border bg-bg p-2.5 text-sm text-zinc-100 focus:border-accent focus:outline-none"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsStartOpen(false)}
                  className="px-4 py-2 rounded-lg border border-border text-zinc-300 text-sm hover:bg-bg-card transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={starting}
                  className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-white text-sm font-medium hover:bg-accent/90 transition shadow-md shadow-accent/20 disabled:opacity-50"
                >
                  {starting ? "Launching..." : "Launch Interview"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
