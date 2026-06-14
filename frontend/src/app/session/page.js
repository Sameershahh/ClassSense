'use client';

import { useState, useEffect } from 'react';
import { useTransitionRouter } from '../context/TransitionContext';
import Link from 'next/link';
import Sidebar from '../components/Sidebar';
import { Plus, ChevronRight } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const authHeader = () => {
  const t = typeof window !== 'undefined' ? localStorage.getItem('cs_token') : '';
  return t ? { Authorization: `Bearer ${t}` } : {};
};

function StatusBadge({ status }) {
  const map = {
    active:     'bg-green-500/15 text-green-400',
    ended:      'bg-white/10 text-white/60',
    processing: 'bg-yellow-500/15 text-yellow-400',
  };
  return (
    <span className={`rounded-full px-3 py-1 text-xs font-medium ${map[status] || map.ended}`}>
      {status}
    </span>
  );
}

export default function SessionsPage() {
  const router = useTransitionRouter();
  const [sessions, setSessions]   = useState([]);
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [creating, setCreating]   = useState(false);
  const [error, setError]         = useState('');
  const [form, setForm]           = useState({ course_name: '', time_slot: '' });

  useEffect(() => {
    if (!localStorage.getItem('cs_token')) { router.push('/'); return; }
    fetchSessions();
  }, []);

  async function fetchSessions() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/sessions/?limit=50`, { headers: authHeader() });
      if (res.status === 401) { router.push('/'); return; }
      setSessions(await res.json());
    } catch { 
      setError('Failed to load sessions.'); 
    } finally { 
      setLoading(false); 
    }
  }

  async function createSession(e) {
    e.preventDefault();
    setCreating(true); setError('');
    try {
      const res = await fetch(`${API}/api/sessions/`, {
        method: 'POST',
        headers: { ...authHeader(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ course_name: form.course_name, time_slot: form.time_slot, instructor_id: 1 }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed');
      setShowModal(false);
      router.push(`/session/${data.session_id}`);
    } catch (err) { 
      setError(err.message); 
    } finally { 
      setCreating(false); 
    }
  }

  return (
    <div className="flex min-h-screen bg-black">
      <Sidebar />

      <main className="flex-1 overflow-y-auto p-8 max-w-6xl">

        {/* Header */}
        <div className="flex items-start justify-between mb-10">
          <div>
            <h1 className="text-3xl font-medium tracking-tight text-white">Sessions</h1>
            <p className="text-sm text-white/60 mt-1 leading-relaxed">
              View and manage all classroom monitoring sessions.
            </p>
          </div>
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 bg-white text-black text-sm font-semibold rounded-xl px-4 h-11 hover:bg-white/90 active:scale-[0.98] transition-all duration-150"
          >
            <Plus size={16} /> New Session
          </button>
        </div>

        {error && (
          <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-xs text-red-400 mb-8">
            {error}
          </div>
        )}

        {/* Sessions Table */}
        <div className="bg-[#1A1A1A] rounded-3xl border border-white/5 overflow-hidden">
          <div className="px-6 py-5 border-b border-white/5 flex items-center justify-between">
            <h2 className="text-xl font-semibold tracking-tight text-white">All Sessions</h2>
            <span className="text-xs text-white/30">{sessions.length} total</span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <span className="w-6 h-6 border-2 border-white/10 border-t-white/60 rounded-full animate-spin" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-20">
              <p className="text-sm text-white/30">No sessions yet. Start your first session.</p>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/5">
                  {['Course', 'Time Slot', 'Start Time', 'End Time', 'Status', ''].map(h => (
                    <th key={h} className="text-left px-6 py-3 text-xs uppercase tracking-widest text-white/30 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sessions.map(s => (
                  <tr key={s.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                    <td className="px-6 py-4 text-sm font-medium text-white">{s.course_name}</td>
                    <td className="px-6 py-4 text-sm text-white/60">{s.time_slot}</td>
                    <td className="px-6 py-4 text-xs text-white/30 font-mono">{s.start_date_time || '—'}</td>
                    <td className="px-6 py-4 text-xs text-white/30 font-mono">{s.end_date_time || '—'}</td>
                    <td className="px-6 py-4"><StatusBadge status={s.status} /></td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        href={`/session/${s.id}`}
                        className="inline-flex items-center gap-1.5 bg-black border border-white/10 rounded-xl text-white text-xs font-medium px-3 h-8 hover:bg-white/5 transition-colors"
                      >
                        View <ChevronRight size={12} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </main>

      {/* Create Session Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4" onClick={() => setShowModal(false)}>
          <div className="bg-[#1A1A1A] rounded-3xl p-8 w-full max-w-md border border-white/5" onClick={e => e.stopPropagation()}>
            <h2 className="text-xl font-semibold tracking-tight text-white mb-1">Start New Session</h2>
            <p className="text-sm text-white/60 leading-relaxed mb-6">Create a new classroom monitoring session.</p>

            <form onSubmit={createSession} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-white mb-1.5 block">Course Name</label>
                <input
                  className="w-full bg-[#242424] border-none rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-2 focus:ring-white/20 focus:outline-none text-sm"
                  placeholder="e.g. CS101 — Data Structures"
                  value={form.course_name}
                  onChange={e => setForm({ ...form, course_name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="text-sm font-medium text-white mb-1.5 block">Time Slot</label>
                <input
                  className="w-full bg-[#242424] border-none rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-2 focus:ring-white/20 focus:outline-none text-sm"
                  placeholder="e.g. Mon 10:00 AM"
                  value={form.time_slot}
                  onChange={e => setForm({ ...form, time_slot: e.target.value })}
                  required
                />
              </div>
              {error && <p className="text-xs text-red-400">{error}</p>}
              <div className="flex gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)}
                  className="flex-1 bg-black border border-white/10 rounded-xl text-white text-sm font-medium px-4 h-11 hover:bg-white/5 transition-colors">
                  Cancel
                </button>
                <button type="submit" disabled={creating}
                  className="flex-1 bg-white text-black text-sm font-semibold rounded-xl h-11 hover:bg-white/90 active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-2">
                  {creating ? <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" /> : 'Start Monitoring'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
