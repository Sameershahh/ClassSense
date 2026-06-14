'use client';

import { useState, useEffect } from 'react';
import { useTransitionRouter } from '../context/TransitionContext';
import Link from 'next/link';
import Sidebar from '../components/Sidebar';
import { ChevronRight, Users, TrendingUp, TrendingDown } from 'lucide-react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, XAxis, YAxis
} from 'recharts';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const authHeader = () => {
  const t = typeof window !== 'undefined' ? localStorage.getItem('cs_token') : '';
  return t ? { Authorization: `Bearer ${t}` } : {};
};

const PIE_COLORS = { attentive: '#4ADE80', confused: '#FACC15', distracted: '#F87171' };

const CHART_TOOLTIP = {
  contentStyle: { backgroundColor: '#1A1A1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' },
  labelStyle:   { color: 'rgba(255,255,255,0.5)', fontSize: '11px' },
  itemStyle:    { color: '#fff', fontSize: '13px' },
};

export default function DashboardPage() {
  const router = useTransitionRouter();
  const [sessions, setSessions]   = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState('');
  const [instructorName, setInstructorName] = useState('Instructor');

  useEffect(() => {
    async function fetchProfile() {
      const token = localStorage.getItem('cs_token');
      if (!token) return;
      try {
        const res = await fetch(`${API}/auth/me`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
          const profile = await res.json();
          setInstructorName(profile.full_name || 'Instructor');
        }
      } catch (err) {
        console.error('Failed to load profile:', err);
      }
    }
    fetchProfile();
  }, []);

  // Selected course & slot
  const [selectedCourse, setSelectedCourse] = useState('');
  const [selectedSlot, setSelectedSlot]     = useState('');

  // Single Session Details (Latest completed overall)
  const [lastSessionSummary, setLastSessionSummary] = useState(null);
  const [lastSessionTimeSeries, setLastSessionTimeSeries] = useState([]);
  const [lastSessionLoading, setLastSessionLoading] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem('cs_token')) { router.push('/'); return; }
    fetchSessions();
  }, []);

  async function fetchSessions() {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/sessions/?limit=100`, { headers: authHeader() });
      if (res.status === 401) { router.push('/'); return; }
      const data = await res.json();
      setSessions(data);

      // Check query parameters first, fallback to first item
      const params = new URLSearchParams(window.location.search);
      const queryCourse = params.get('course_name');
      const querySlot = params.get('time_slot');
      if (queryCourse && querySlot) {
        setSelectedCourse(queryCourse);
        setSelectedSlot(querySlot);
      } else if (data.length > 0) {
        setSelectedCourse(data[0].course_name);
        setSelectedSlot(data[0].time_slot);
      }
    } catch {
      setError('Failed to load sessions.');
    } finally {
      setLoading(false);
    }
  }

  // Fetch single session stats when course/slot selection changes (in 'session' tab)
  useEffect(() => {
    if (sessions.length > 0 && selectedCourse && selectedSlot) {
      const matchingEnded = sessions.find(
        s => s.course_name === selectedCourse && s.time_slot === selectedSlot && s.status === 'ended'
      );
      if (matchingEnded) {
        fetchLastSessionDetails(matchingEnded.id);
      } else {
        setLastSessionSummary(null);
        setLastSessionTimeSeries([]);
      }
    }
  }, [sessions, selectedCourse, selectedSlot]);

  async function fetchLastSessionDetails(sessionId) {
    setLastSessionLoading(true);
    try {
      const [sumRes, tsRes] = await Promise.all([
        fetch(`${API}/api/analytics/${sessionId}/summary`, { headers: authHeader() }),
        fetch(`${API}/api/analytics/${sessionId}/timeseries?downsample=5`, { headers: authHeader() })
      ]);
      if (sumRes.ok) {
        setLastSessionSummary(await sumRes.json());
      }
      if (tsRes.ok) {
        const tsData = await tsRes.json();
        setLastSessionTimeSeries(tsData.points || []);
      }
    } catch (err) {
      console.error('Failed to fetch last session details:', err);
    } finally {
      setLastSessionLoading(false);
    }
  }





  // Extract unique course/slot combinations for the selection dropdown
  const uniqueCombinations = [];
  const processedKeys = new Set();
  sessions.forEach(s => {
    const key = `${s.course_name} ||| ${s.time_slot}`;
    if (!processedKeys.has(key)) {
      processedKeys.add(key);
      uniqueCombinations.push({ course: s.course_name, slot: s.time_slot });
    }
  });

  const active = sessions.filter(s => s.status === 'active').length;
  const ended  = sessions.filter(s => s.status === 'ended').length;

  // Single Session Chart preparation
  const pieData = lastSessionSummary
    ? [
        { name: 'Attentive', value: lastSessionSummary.total_attentive || 0, color: '#4ADE80' },
        { name: 'Confused', value: lastSessionSummary.total_confused || 0, color: '#FACC15' },
        { name: 'Distracted', value: lastSessionSummary.total_distracted || 0, color: '#F87171' }
      ]
    : [];

  const lineData = lastSessionTimeSeries.map((p, idx) => ({
    index: idx + 1,
    engagement: p.engagement_pct,
    studentCount: p.student_count
  }));



  return (
    <div className="flex min-h-screen bg-black">
      <Sidebar />

      <main className="flex-1 overflow-y-auto p-8 max-w-6xl">

        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
          <div>
            <h1 className="text-3xl font-medium tracking-tight text-white">Welcome back, {instructorName}</h1>
            <p className="text-sm text-white/60 mt-1 leading-relaxed">
              Monitor classroom engagement sessions and semester-long metrics.
            </p>
          </div>
          <div className="flex flex-wrap gap-3 items-center">
            {/* Course & Slot Dropdown Selector */}
            {uniqueCombinations.length > 0 && (
              <div className="bg-[#1A1A1A] border border-white/10 rounded-xl px-3 h-11 flex items-center gap-2">
                <span className="text-xs text-white/40 uppercase tracking-wider font-semibold">Course:</span>
                <select
                  value={`${selectedCourse}|||${selectedSlot}`}
                  onChange={(e) => {
                    const [c, s] = e.target.value.split('|||');
                    setSelectedCourse(c);
                    setSelectedSlot(s);
                  }}
                  className="bg-transparent border-none text-white text-sm focus:outline-none pr-4 font-medium"
                >
                  {uniqueCombinations.map(x => (
                    <option key={`${x.course}|||${x.slot}`} value={`${x.course}|||${x.slot}`} className="bg-[#1A1A1A]">
                      {x.course} ({x.slot})
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>
        </div>

        {error && (
          <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-xs text-red-400 mb-8">
            {error}
          </div>
        )}

        {/* Metric Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Sessions',  value: sessions.length, sub: 'all time' },
            { label: 'Active',          value: active,          sub: 'currently running', color: 'text-green-400' },
            { label: 'Completed',       value: ended,           sub: 'ended sessions' },
            { 
              label: 'Avg Engagement',  
              value: lastSessionSummary ? `${lastSessionSummary.avg_engagement.toFixed(1)}%` : '—', 
              sub: 'last completed session' 
            },
          ].map((s) => (
            <div key={s.label} className="bg-[#1A1A1A] rounded-3xl p-6 border border-white/5">
              <p className="text-xs text-white/40 uppercase tracking-widest">{s.label}</p>
              <p className={`text-5xl font-bold text-white mt-2 tracking-tight ${s.color || ''}`}>{s.value}</p>
              <p className="text-xs text-white/30 mt-1">{s.sub}</p>
            </div>
          ))}
        </div>

        {/* Tab Panel: Latest Session */}
        {loading || lastSessionLoading ? (
          <div className="flex items-center justify-center py-20 bg-[#1A1A1A] rounded-3xl border border-white/5">
            <span className="w-6 h-6 border-2 border-white/10 border-t-white/60 rounded-full animate-spin" />
          </div>
        ) : lastSessionSummary ? (
          <div className="space-y-8 animate-fadeIn">
            {/* Header Details Card */}
            <div className="bg-[#1A1A1A] rounded-3xl border border-white/5 p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <span className="text-xs text-white/40 uppercase tracking-widest font-semibold">Latest Session Analytics</span>
                <h2 className="text-2xl font-bold text-white mt-1">{lastSessionSummary.course_name}</h2>
                <p className="text-sm text-white/60 mt-0.5">
                  {lastSessionSummary.time_slot} · {lastSessionSummary.duration_mins ? `${Math.round(lastSessionSummary.duration_mins)} mins` : 'N/A'} duration
                </p>
              </div>
              <div>
                <Link
                  href={`/session/${lastSessionSummary.session_id}`}
                  className="inline-flex items-center gap-1.5 bg-white text-black text-xs font-semibold rounded-xl px-4 h-11 hover:bg-white/90 active:scale-[0.98] transition-all"
                >
                  View Full Session <ChevronRight size={14} />
                </Link>
              </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Pie Chart */}
              <div className="bg-[#1A1A1A] rounded-3xl border border-white/5 p-6 flex flex-col justify-between h-[360px]">
                <div>
                  <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider">Emotion Share</h3>
                  <p className="text-xs text-white/30 mt-0.5">Distribution of student emotions</p>
                </div>
                
                {pieData.reduce((a, b) => a + b.value, 0) > 0 ? (
                  <div className="h-[200px] relative flex items-center justify-center">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={pieData} dataKey="value" cx="50%" cy="50%" innerRadius={45} outerRadius={75} paddingAngle={4}>
                          {pieData.map((entry, idx) => (
                            <Cell key={`cell-${idx}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip {...CHART_TOOLTIP} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center text-xs text-white/30">
                    No emotion data
                  </div>
                )}
                
                <div className="flex justify-around text-xs border-t border-white/5 pt-4">
                  {pieData.map(d => (
                    <div key={d.name} className="flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                      <span className="text-white/60">{d.name}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Line Chart */}
              <div className="bg-[#1A1A1A] rounded-3xl border border-white/5 p-6 flex flex-col justify-between h-[360px] lg:col-span-2">
                <div>
                  <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider">Engagement Trend</h3>
                  <p className="text-xs text-white/30 mt-0.5">Real-time engagement percentage over frames</p>
                </div>

                {lineData.length > 0 ? (
                  <div className="h-[220px] w-full mt-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={lineData} margin={{ left: -20, right: 10, top: 10, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="index" tick={{ fill: 'rgba(255,255,255,0.25)', fontSize: 10 }} axisLine={false} tickLine={false} />
                        <YAxis domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.25)', fontSize: 10 }} axisLine={false} tickLine={false} />
                        <Tooltip {...CHART_TOOLTIP} />
                        <Line type="monotone" dataKey="engagement" stroke="#60A5FA" strokeWidth={2.5} dot={false} name="Engagement %" />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center text-xs text-white/30">
                    No engagement trend data
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="text-center py-20 bg-[#1A1A1A] rounded-3xl border border-white/5">
            <p className="text-sm text-white/40">No completed sessions found for this combination.</p>
          </div>
        )}
      </main>
    </div>
  );
}
