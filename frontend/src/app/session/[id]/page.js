'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import { useTransitionRouter } from '../../context/TransitionContext';
import Link from 'next/link';
import Sidebar from '../../components/Sidebar';
import { Upload, Square, FileText, FileSpreadsheet, ChevronLeft, Users, TrendingUp, TrendingDown, Lock, Unlock } from 'lucide-react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, XAxis, YAxis,
  AreaChart, Area, BarChart, Bar,
} from 'recharts';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const authHeader = () => {
  const t = typeof window !== 'undefined' ? localStorage.getItem('cs_token') : '';
  return t ? { Authorization: `Bearer ${t}` } : {};
};

function EngagementBar({ pct }) {
  const color = pct >= 70 ? 'bg-green-400' : pct >= 40 ? 'bg-yellow-400' : 'bg-red-400';
  return (
    <div className="h-1.5 rounded-full bg-white/10 w-full overflow-hidden">
      <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

function StatusBadge({ status }) {
  const map = {
    active:     'bg-green-500/15 text-green-400',
    ended:      'bg-white/10 text-white/60',
    processing: 'bg-yellow-500/15 text-yellow-400',
  };
  return <span className={`rounded-full px-3 py-1 text-xs font-medium ${map[status] || map.ended}`}>{status}</span>;
}

const PIE_COLORS = { attentive: '#14B8A6', confused: '#F59E0B', distracted: '#F43F5E' };

const CHART_TOOLTIP = {
  contentStyle: { 
    backgroundColor: '#1E293B', 
    border: 'none',
    borderRadius: '12px', 
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3), 0 4px 6px -2px rgba(0, 0, 0, 0.2)',
    color: '#F8FAFC',
    padding: '10px 14px'
  },
  labelStyle: { color: '#94A3B8', fontSize: '11px', fontWeight: '500', marginBottom: '4px' },
  itemStyle: { color: '#F8FAFC', fontSize: '13px', padding: '2px 0' },
};

const LIGHT_CHART_TOOLTIP = {
  contentStyle: { 
    backgroundColor: '#FFFFFF', 
    border: 'none',
    borderRadius: '12px', 
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)',
    color: '#1E293B',
    padding: '10px 14px'
  },
  labelStyle: { color: '#64748B', fontSize: '11px', fontWeight: '500', marginBottom: '4px' },
  itemStyle: { color: '#1E293B', fontSize: '13px', padding: '2px 0' },
};

export default function SessionPage() {
  const router = useTransitionRouter();
  const { id } = useParams();

  const [session, setSession]       = useState(null);
  const [loading, setLoading]       = useState(true);
  const [result, setResult]         = useState(null);
  const [summary, setSummary]       = useState(null);
  const [timeseries, setTimeseries] = useState([]);
  const [uploading, setUploading]   = useState(false);
  const [ending, setEnding]         = useState(false);
  const [dragOver, setDragOver]     = useState(false);
  const [selectedFile, setFile]     = useState(null);
  const [progress, setProgress]     = useState(0);
  const [error, setError]           = useState('');
  const [consecutiveErrors, setConsecutiveErrors] = useState(0);
  const [showSemesterModal, setShowSemesterModal] = useState(false);
  const [semesterReport, setSemesterReport]       = useState(null);
  const [semesterLoading, setSemesterLoading]     = useState(false);
  const [semesterError, setSemesterError]         = useState('');
  const [userRole, setUserRole]     = useState('instructor');
  const fileRef = useRef(null);
  const token = typeof window !== 'undefined' ? localStorage.getItem('cs_token') : '';

  useEffect(() => {
    if (!localStorage.getItem('cs_token')) { router.push('/'); return; }
    fetchSession();
    fetchUserRole();
  }, [id]);

  async function fetchUserRole() {
    const storedRole = localStorage.getItem('cs_role');
    if (storedRole) {
      setUserRole(storedRole);
      return;
    }
    const t = localStorage.getItem('cs_token');
    if (!t) return;
    try {
      const res = await fetch(`${API}/auth/me`, {
        headers: { 'Authorization': `Bearer ${t}` }
      });
      if (res.ok) {
        const data = await res.json();
        setUserRole(data.role);
        localStorage.setItem('cs_role', data.role);
      }
    } catch (err) {
      console.error('Failed to fetch user role:', err);
    }
  }

  useEffect(() => {
    let intervalId;
    if (session && (session.status === 'active' || session.status === 'processing') && consecutiveErrors < 5) {
      intervalId = setInterval(() => {
        fetchSessionSilent();
      }, 3000);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [id, session?.status, consecutiveErrors]);

  async function fetchSessionSilent() {
    if (!id || id === 'undefined') return;
    if (consecutiveErrors >= 5) {
      console.warn('[fetchSessionSilent] Polling suspended due to multiple consecutive network failures.');
      return;
    }
    try {
      const res = await fetch(`${API}/api/sessions/${id}`, { headers: authHeader() });
      setConsecutiveErrors(0); // Reset on successful fetch
      
      if (res.ok) {
        const data = await res.json();
        setSession(data);
        if (data && data.session_id) {
          // Only fetch analytics if the session is completed (ended)
          if (data.status === 'ended') {
            setResult(null); // Clear stale video processing result
            const sumRes = await fetch(`${API}/api/analytics/${data.session_id}/summary`, { headers: authHeader() });
            if (sumRes.ok) {
              const summaryData = await sumRes.json();
              console.log('[fetchSessionSilent] Loaded summary payload:', summaryData);
              if (summaryData && !summaryData.emotion_totals) {
                summaryData.emotion_totals = {
                  attentive: summaryData.total_attentive || 0,
                  confused: summaryData.total_confused || 0,
                  distracted: summaryData.total_distracted || 0,
                };
              }
              setSummary(summaryData);
            }
            const tsRes = await fetch(`${API}/api/analytics/${data.session_id}/timeseries?downsample=5`, { headers: authHeader() });
            if (tsRes.ok) {
              const tsData = await tsRes.json();
              if (tsData && tsData.points) {
                setTimeseries(tsData.points);
              }
            }
          }
        }
      }
    } catch (err) {
      setConsecutiveErrors(prev => prev + 1);
      console.warn(`[fetchSessionSilent] Network connection issue. Failures: ${consecutiveErrors + 1}. Error:`, err.message || err);
    }
  }

  async function fetchSession() {
    if (!id || id === 'undefined') {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError('');
    setConsecutiveErrors(0);
    try {
      const res = await fetch(`${API}/api/sessions/${id}`, { headers: authHeader() });
      if (res.status === 401) { router.push('/'); return; }
      if (!res.ok) {
        throw new Error(`Failed to load session details (Status ${res.status})`);
      }
      const data = await res.json();
      console.log('[fetchSession] Loaded session details:', data);
      setSession(data);
      if (data && data.session_id) {
        // Only fetch analytics if the session has completed (ended)
        if (data.status === 'ended') {
          setResult(null); // Clear stale video processing result
          await fetchAnalytics(data.session_id);
        }
      }
    } catch (err) {
      console.error('[fetchSession] Error loading session:', err);
      setError('Could not load session.');
      setSession(null);
    } finally {
      setLoading(false);
    }
  }

  async function fetchAnalytics(sessionId) {
    try {
      console.log(`[fetchAnalytics] Querying summary for session ${sessionId}...`);
      const sumRes = await fetch(`${API}/api/analytics/${sessionId}/summary`, { headers: authHeader() });
      console.log(`[fetchAnalytics] Summary response status:`, sumRes.status);
      if (sumRes.ok) {
        const summaryData = await sumRes.json();
        console.log('[fetchAnalytics] Summary data received:', summaryData);
        console.log(summaryData); // quick console.log as requested
        // Ensure emotion_totals is present
        if (summaryData && !summaryData.emotion_totals) {
          summaryData.emotion_totals = {
            attentive: summaryData.total_attentive || 0,
            confused: summaryData.total_confused || 0,
            distracted: summaryData.total_distracted || 0,
          };
        }
        setSummary(summaryData);
      } else {
        console.log('[fetchAnalytics] No summary available yet (session may not be ended).');
      }
    } catch (err) {
      console.error('[fetchAnalytics] Error fetching summary:', err);
    }

    try {
      console.log(`[fetchAnalytics] Querying timeseries for session ${sessionId}...`);
      const tsRes = await fetch(`${API}/api/analytics/${sessionId}/timeseries?downsample=5`, { headers: authHeader() });
      console.log(`[fetchAnalytics] Timeseries response status:`, tsRes.status);
      if (tsRes.ok) {
        const tsData = await tsRes.json();
        console.log('[fetchAnalytics] Timeseries data received:', tsData);
        if (tsData && tsData.points) {
          setTimeseries(tsData.points);
        }
      } else {
        console.log('[fetchAnalytics] No timeseries data available yet.');
      }
    } catch (err) {
      console.error('[fetchAnalytics] Error fetching timeseries:', err);
    }
  }

  async function openSemesterModal() {
    setShowSemesterModal(true);
    const count = session?.semester_sessions_count || 0;
    if (count < 14) return;
    if (semesterReport) return;
    
    setSemesterLoading(true);
    setSemesterError('');
    try {
      console.log(`[Semester Report] Fetching data for ${session.course_name} (${session.time_slot})...`);
      const res = await fetch(
        `${API}/api/analytics/semester/report?course_name=${encodeURIComponent(session.course_name)}&time_slot=${encodeURIComponent(session.time_slot)}`,
        { headers: authHeader() }
      );
      console.log(`[Semester Report] Response status: ${res.status}`);
      if (res.ok) {
        const data = await res.json();
        console.log('[Semester Report] Data received:', data);
        setSemesterReport(data);
      } else {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to load semester report.');
      }
    } catch (err) {
      console.error('[Semester Report] Error:', err);
      setSemesterError(err.message);
    } finally {
      setSemesterLoading(false);
    }
  }

  async function uploadVideo() {
    if (!selectedFile) return;
    setUploading(true); setError(''); setResult(null); setProgress(10); setConsecutiveErrors(0);
    const iv = setInterval(() => setProgress(p => p < 85 ? p + 3 : p), 1500);
    try {
      const fd = new FormData();
      // Use a safe ASCII filename to avoid python-multipart header parsing issues with non-ASCII or special characters in the filename
      const ext = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')) || '.mp4';
      fd.append('file', selectedFile, `video_upload${ext}`);
      const res = await fetch(`${API}/api/sessions/${id}/upload-video`, {
        method: 'POST', headers: authHeader(), body: fd,
      });
      clearInterval(iv); setProgress(100);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Upload failed');
      setResult(data); setFile(null);
      fetchSession();
    } catch (err) { setError(err.message); }
    finally { setUploading(false); }
  }

  async function endSession() {
    setEnding(true); setError('');
    try {
      const res = await fetch(`${API}/api/sessions/${id}/end`, {
        method: 'POST', headers: authHeader(),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed');
      setSummary(data.summary);
      fetchSession();
    } catch (err) { setError(err.message); }
    finally { setEnding(false); }
  }

  const derivedSummary = summary
    ? summary
    : (timeseries && timeseries.length > 0)
    ? {
        avg_students: Math.round(timeseries.reduce((acc, p) => acc + p.student_count, 0) / timeseries.length),
        emotion_totals: (() => {
          let attentive = 0, confused = 0, distracted = 0;
          timeseries.forEach(p => {
            attentive += p.attentive || 0;
            confused += p.confused || 0;
            distracted += p.distracted || 0;
          });
          return { attentive, confused, distracted };
        })()
      }
    : null;

  const engPct   = result?.avg_engagement ?? summary?.avg_engagement ?? (timeseries && timeseries.length > 0 ? (timeseries.reduce((acc, p) => acc + p.engagement_pct, 0) / timeseries.length) : null);
  const pieData  = derivedSummary?.emotion_totals
    ? Object.entries(derivedSummary.emotion_totals).map(([name, value]) => ({ name, value }))
    : null;

  // Real trend data mapped from backend timeseries if available, falling back to dummy data if result is present
  const trendData = timeseries && timeseries.length > 0
    ? timeseries.map(p => {
        const total = (p.attentive || 0) + (p.confused || 0) + (p.distracted || 0);
        const totalVal = total > 0 ? total : 1;
        return {
          time: p.time_str || `S${p.frame_number}`,
          pct: p.engagement_pct,
          attentive: Math.round(((p.attentive || 0) / totalVal) * 100),
          confused: Math.round(((p.confused || 0) / totalVal) * 100),
          distracted: Math.round(((p.distracted || 0) / totalVal) * 100),
        };
      })
    : result
    ? Array.from({ length: 10 }, (_, i) => ({
        time: `00:${(i * 5).toString().padStart(2, '0')}`,
        pct: Math.round(result.avg_engagement + (Math.random() - 0.5) * (result.peak_engagement - result.min_engagement) * 0.5),
        attentive: 60,
        confused: 25,
        distracted: 15,
      }))
    : [];

  return (
    <div className="flex min-h-screen bg-black">
      <Sidebar />

      <main className="flex-1 overflow-y-auto p-8">

        {/* Breadcrumb */}
        <Link href={userRole === 'hod' ? "/hod/dashboard" : "/dashboard"} className="inline-flex items-center gap-1.5 text-xs text-white/40 hover:text-white/70 transition-colors mb-8">
          <ChevronLeft size={14} /> Dashboard
        </Link>

        {loading ? (
          <div className="flex items-center justify-center py-40">
            <span className="w-10 h-10 border-4 border-white/10 border-t-white/60 rounded-full animate-spin" />
          </div>
        ) : error && !session ? (
          <div className="max-w-md mx-auto text-center py-20 bg-[#1A1A1A] rounded-3xl border border-white/5 p-8">
            <div className="text-red-400 mb-4 text-sm font-medium">{error}</div>
            <button
              onClick={fetchSession}
              className="bg-white text-black text-xs font-semibold rounded-xl px-4 h-9 hover:bg-white/90 active:scale-[0.98] transition-all"
            >
              Try Again
            </button>
          </div>
        ) : !session ? (
          <div className="max-w-md mx-auto text-center py-20 bg-[#1A1A1A] rounded-3xl border border-white/5 p-8">
            <p className="text-sm text-white/40 mb-4">Session not found.</p>
            <Link
              href={userRole === 'hod' ? "/hod/dashboard" : "/dashboard"}
              className="inline-flex items-center justify-center bg-white text-black text-xs font-semibold rounded-xl px-4 h-9 hover:bg-white/90 active:scale-[0.98] transition-all"
            >
              Back to Dashboard
            </Link>
          </div>
        ) : (
          <>
            {/* Session Header */}
            <div className="flex items-start justify-between mb-8">
              <div>
                <div className="flex items-center gap-3 mb-1">
                  <h1 className="text-3xl font-medium tracking-tight text-white">{session.course_name}</h1>
                  <StatusBadge status={session.status} />
                </div>
                <p className="text-sm text-white/40">
                  {session.time_slot} · Session <span className="font-mono">#{id}</span>
                </p>
              </div>
              {session.status === 'active' && userRole !== 'hod' && (
                <button
                  onClick={endSession} disabled={ending}
                  className="bg-black border border-white/10 rounded-xl text-white text-sm font-medium px-4 h-11 hover:bg-red-500/5 hover:border-red-500/30 hover:text-red-400 transition-colors duration-150 flex items-center gap-2 disabled:opacity-50"
                >
                  {ending ? <span className="w-4 h-4 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" /> : <><Square size={14} /> End Session</>}
                </button>
              )}
            </div>

            {error && (
              <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-xs text-red-400 mb-6">
                {error}
              </div>
            )}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">

          {/* Column 1: Main Content */}
          <div className="space-y-6">
            {/* ── Upload Card OR Live Active Card ── */}
            {session?.status === 'active' && (
              session?.mode === 'live' ? (
                <div className="bg-[#1A1A1A] rounded-3xl p-6 border border-white/5 space-y-6">
                  <div className="flex items-center justify-between">
                    <h2 className="text-xl font-semibold tracking-tight text-white flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-green-500 animate-pulse" />
                      Live Stream Analysis Active
                    </h2>
                    <span className="text-xs text-green-400 font-mono">1 frame/sec</span>
                  </div>
                  <p className="text-sm text-white/60 leading-relaxed">
                    ClassSense is pulling frames directly from the pre-configured IP Camera RTSP feed in the classroom and analyzing student emotions in real-time.
                  </p>
                  
                  <div className="border border-white/5 bg-black/40 rounded-2xl p-4 flex items-center justify-between text-xs">
                    <span className="text-white/40">Active Room Camera:</span>
                    <span className="font-semibold text-[#DEDBC8]">{session?.time_slot}</span>
                  </div>

                  {userRole !== 'hod' && (
                    <button
                      onClick={async () => {
                        if (!confirm('Are you sure you want to end this live session?')) return;
                        try {
                          const res = await fetch(`${API}/api/sessions/${session.session_id}/end`, {
                            method: 'POST',
                            headers: authHeader()
                          });
                          if (res.ok) {
                            fetchSession();
                          }
                        } catch (err) {
                          alert('Failed to end live session: ' + err.message);
                        }
                      }}
                      className="w-full h-14 bg-red-500 hover:bg-red-600 text-white font-semibold rounded-xl active:scale-[0.98] transition-all duration-150 text-sm flex items-center justify-center gap-2"
                    >
                      End Live Session & Generate Reports
                    </button>
                  )}
                </div>
              ) : (
                userRole === 'hod' ? (
                  <div className="bg-[#1A1A1A] rounded-3xl p-6 border border-white/5 text-center flex flex-col items-center justify-center py-12">
                    <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-white/30 mb-4 animate-pulse">
                      <Upload size={20} />
                    </div>
                    <h3 className="text-base font-semibold text-white mb-1">Waiting for Video Upload</h3>
                    <p className="text-xs text-white/40 max-w-xs leading-relaxed">
                      The instructor has not uploaded a video recording for this session yet. Monitoring will become available once the analysis starts.
                    </p>
                  </div>
                ) : (
                  <div className="bg-[#1A1A1A] rounded-3xl p-6 border border-white/5">
                    <h2 className="text-xl font-semibold tracking-tight text-white mb-1">Upload Video</h2>
                    <p className="text-sm text-white/60 leading-relaxed mb-6">
                      Upload a classroom recording for AI engagement analysis.
                    </p>

                    {/* Drop Zone */}
                    <div
                      onClick={() => fileRef.current?.click()}
                      onDragOver={e => { e.preventDefault(); setDragOver(true); }}
                      onDragLeave={() => setDragOver(false)}
                      onDrop={e => { e.preventDefault(); setDragOver(false); setFile(e.dataTransfer.files[0]); }}
                      className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all duration-150
                        ${dragOver  ? 'border-white/30 bg-white/5'     : ''}
                        ${selectedFile ? 'border-green-500/30 bg-green-500/5' : 'border-white/10 hover:border-white/20 hover:bg-white/[0.02]'}
                      `}
                    >
                      <input
                        ref={fileRef} type="file" accept=".mp4,.avi,.mov,.mkv,.webm"
                        className="hidden" onChange={e => setFile(e.target.files[0])}
                      />
                      <Upload size={24} className="mx-auto mb-3 text-white/20" />
                      {selectedFile ? (
                        <>
                          <p className="text-sm font-medium text-green-400 mb-1">{selectedFile.name}</p>
                          <p className="text-xs text-white/30">{(selectedFile.size / 1e6).toFixed(1)} MB · Click to change</p>
                        </>
                      ) : (
                        <>
                          <p className="text-sm font-medium text-white/60 mb-1">Drop video here or click to browse</p>
                          <p className="text-xs text-white/30">MP4, AVI, MOV, MKV, WEBM · Max 500 MB</p>
                        </>
                      )}
                    </div>

                    {/* Progress */}
                    {uploading && (
                      <div className="mt-5 space-y-2">
                        <div className="flex justify-between text-xs text-white/40">
                          <span>Analysing with AI…</span>
                          <span>{progress}%</span>
                        </div>
                        <EngagementBar pct={progress} />
                        <p className="text-xs text-white/20">Processing each frame for emotion and engagement signals…</p>
                      </div>
                    )}

                    <button
                      onClick={uploadVideo} disabled={!selectedFile || uploading}
                      className="w-full h-14 mt-5 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-all duration-150 text-sm flex items-center justify-center gap-2 disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      {uploading
                        ? <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                        : <><Upload size={16} /> Analyse Video</>
                      }
                    </button>
                  </div>
                )
              )
            )}

            {/* ── Analyzing Video Card ── */}
            {session?.status === 'processing' && (
              <div className="bg-[#1A1A1A] rounded-3xl p-8 border border-white/5 text-center flex flex-col items-center justify-center py-16">
                <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-white/40 mb-4 animate-spin">
                  <span className="w-6 h-6 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                </div>
                <h3 className="text-base font-semibold text-white mb-1">Analyzing Video...</h3>
                <p className="text-xs text-white/40 max-w-xs leading-relaxed">
                  Our Computer Vision model is currently analyzing the classroom recording frame-by-frame. 
                  Please wait, this dashboard will update automatically when complete.
                </p>
              </div>
            )}

            {/* ── Empty State Card ── */}
            {!result && !derivedSummary && session?.status !== 'processing' && (
              <div className="bg-[#1A1A1A] rounded-3xl p-8 border border-white/5 text-center flex flex-col items-center justify-center py-16">
                <div className="w-12 h-12 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-white/30 mb-4">
                  <Users size={20} />
                </div>
                <h3 className="text-base font-semibold text-white mb-1">No Analytics Data Available</h3>
                <p className="text-xs text-white/40 max-w-xs leading-relaxed">
                  No video or frame-level engagement data has been processed for this session yet.
                  {session.status === 'active' ? ' Please upload a classroom video recording above to begin analysis.' : ' This session was closed without any analytics data recorded.'}
                </p>
              </div>
            )}

            {/* ── Results Card ── */}
            {(result || derivedSummary) && session?.status !== 'processing' && (
              <div className="bg-[#1A1A1A] rounded-3xl p-6 border border-white/5 space-y-6">
                <div>
                  <h2 className="text-xl font-semibold tracking-tight text-white mb-1">Engagement Results</h2>
                  <p className="text-sm text-white/60 leading-relaxed">AI analysis complete.</p>
                </div>
                <div className="border-t border-white/5" />

                {/* Hero metric */}
                {engPct !== null && (
                  <div>
                    <p className="text-xs text-white/40 uppercase tracking-widest">Average Engagement</p>
                    <p className={`text-5xl font-bold tracking-tight mt-2 ${engPct >= 70 ? 'text-green-400' : engPct >= 40 ? 'text-yellow-400' : 'text-red-400'}`}>
                      {engPct.toFixed(1)}%
                    </p>
                    <div className="mt-3"><EngagementBar pct={engPct} /></div>
                  </div>
                )}

                {/* Mini stats */}
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { 
                      label: 'Frames', 
                      value: result?.frames_processed ?? summary?.frames_processed ?? summary?.frames_analysed ?? (timeseries && timeseries.length > 0 ? timeseries.length : '—'), 
                      icon: null 
                    },
                    { 
                      label: 'Peak',  
                      value: result?.peak_engagement !== undefined && result?.peak_engagement !== null
                        ? `${result.peak_engagement}%` 
                        : summary?.peak_engagement !== undefined && summary?.peak_engagement !== null
                        ? `${summary.peak_engagement}%`
                        : timeseries && timeseries.length > 0
                        ? `${Math.max(...timeseries.map(p => p.engagement_pct)).toFixed(1)}%`
                        : '—', 
                      icon: <TrendingUp size={14} /> 
                    },
                    { 
                      label: 'Min',   
                      value: result?.min_engagement !== undefined && result?.min_engagement !== null
                        ? `${result.min_engagement}%` 
                        : summary?.min_engagement !== undefined && summary?.min_engagement !== null
                        ? `${summary.min_engagement}%`
                        : timeseries && timeseries.length > 0
                        ? `${Math.min(...timeseries.map(p => p.engagement_pct)).toFixed(1)}%`
                        : '—', 
                      icon: <TrendingDown size={14} /> 
                    },
                  ].map(s => (
                    <div key={s.label} className="bg-[#242424] rounded-2xl p-4">
                      <p className="text-xs text-white/40 uppercase tracking-widest mb-2 flex items-center gap-1.5">
                        {s.icon} {s.label}
                      </p>
                      <p className="text-2xl font-bold text-white tracking-tight">{s.value}</p>
                    </div>
                  ))}
                </div>

                {/* Emotion Pie + Bars */}
                {derivedSummary?.emotion_totals && (
                  <>
                    <div className="border-t border-white/5" />
                    <div>
                      <p className="text-xs text-white/40 uppercase tracking-widest mb-4">Emotion Distribution</p>
                      <div className="flex gap-6 items-center">
                        {/* Pie */}
                        <div className="w-32 h-32 flex-shrink-0">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie data={pieData} dataKey="value" cx="50%" cy="50%" innerRadius={28} outerRadius={54} paddingAngle={3}>
                                {pieData.map(entry => (
                                  <Cell key={entry.name} fill={PIE_COLORS[entry.name] || '#fff'} />
                                ))}
                              </Pie>
                              <Tooltip 
                                {...CHART_TOOLTIP} 
                                formatter={(value) => {
                                  const total = pieData ? pieData.reduce((acc, d) => acc + d.value, 0) : 0;
                                  const pct = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
                                  return [`${pct}%`];
                                }} 
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>
                        {/* Bars */}
                        <div className="flex-1 space-y-3">
                          {[
                            { key: 'attentive',  label: 'Attentive',  cls: 'bg-green-400',  text: 'text-green-400'  },
                            { key: 'confused',   label: 'Confused',   cls: 'bg-yellow-400', text: 'text-yellow-400' },
                            { key: 'distracted', label: 'Distracted', cls: 'bg-red-400',    text: 'text-red-400'   },
                          ].map(({ key, label, cls, text }) => {
                            const total = Object.values(derivedSummary.emotion_totals).reduce((a, b) => a + b, 0);
                            const pct   = total > 0 ? Math.round((derivedSummary.emotion_totals[key] / total) * 100) : 0;
                            return (
                              <div key={key}>
                                <div className="flex justify-between mb-1">
                                  <span className={`text-xs font-medium ${text}`}>{label}</span>
                                  <span className="text-xs text-white/30">{pct}%</span>
                                </div>
                                <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                                  <div className={`h-full rounded-full transition-all duration-700 ${cls}`} style={{ width: `${pct}%` }} />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </>
                )}



              {/* Download buttons */}
              {session?.status === 'ended' && (
                <div className="flex gap-3 pt-2">
                  <a
                    href={`${API}/api/analytics/${id}/report/pdf?token=${token}`}
                    target="_blank" rel="noreferrer"
                    className="flex-1 bg-black border border-white/10 rounded-xl text-white text-sm font-medium px-4 h-11 hover:bg-white/5 transition-colors flex items-center justify-center gap-2"
                  >
                    <FileText size={15} /> PDF Report
                  </a>
                  <a
                    href={`${API}/api/analytics/${id}/report/csv?token=${token}`}
                    target="_blank" rel="noreferrer"
                    className="flex-1 bg-black border border-white/10 rounded-xl text-white text-sm font-medium px-4 h-11 hover:bg-white/5 transition-colors flex items-center justify-center gap-2"
                  >
                    <FileSpreadsheet size={15} /> CSV Export
                  </a>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Column 2: Side Content */}
        <div className="space-y-6">
          {/* Finalise prompt */}
          {session?.status === 'active' && (result || timeseries.length > 0) && !summary && userRole !== 'hod' && (
            <div className="bg-[#1A1A1A] rounded-3xl p-6 border border-white/5">
              <h2 className="text-xl font-semibold tracking-tight text-white mb-1">Finalise Session</h2>
              <p className="text-sm text-white/60 leading-relaxed mb-6">
                Video processed. End the session to compute the full summary and unlock report downloads.
              </p>
              <button
                onClick={endSession} disabled={ending}
                className="w-full h-14 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-all text-sm flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {ending ? <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" /> : <><Square size={16} /> End & Generate Reports</>}
              </button>
            </div>
          )}

          {/* Semester Progress Card */}
          {session && (
            <div className="bg-[#1A1A1A] rounded-3xl p-6 border border-white/5 flex flex-col justify-between h-full space-y-6">
              <div>
                <span className="text-xs text-white/40 uppercase tracking-widest font-semibold">Semester Progress</span>
                <h2 className="text-xl font-bold text-white mt-1 font-semibold leading-tight">Semester Analytics</h2>
                <p className="text-sm text-white/60 mt-1 leading-relaxed">
                  Monitor aggregated metrics and performance trend reports across all sessions this semester.
                </p>
                <div className="mt-6">
                  <div className="flex justify-between text-xs text-white/40 font-mono mb-2">
                    <span>Completed Sessions</span>
                    <span>{session.semester_sessions_count || 0} / 14</span>
                  </div>
                  <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-white h-full rounded-full transition-all duration-500" 
                      style={{ width: `${Math.min(100, ((session.semester_sessions_count || 0) / 14) * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
              <button
                onClick={openSemesterModal}
                className="w-full h-12 bg-black border border-white/10 rounded-xl text-white text-sm font-semibold hover:bg-white/5 transition-all flex items-center justify-center gap-2"
              >
                {(session.semester_sessions_count || 0) >= 14 ? (
                  <><Unlock size={14} className="text-green-400" /> View Semester Report</>
                ) : (
                  <><Lock size={14} className="text-white/40" /> View Semester Report</>
                )}
              </button>
            </div>
          )}
        </div>

      </div>

      {/* Charts Grid */}
      {trendData.length > 0 && session?.status !== 'processing' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-8">
          {/* 1. Engagement Trend */}
          <div className="col-span-full bg-white shadow-md rounded-xl p-6 text-slate-800">
            <p className="text-xs text-slate-500 uppercase tracking-widest mb-4 font-semibold">Engagement Trend</p>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="colorEngagement" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#4F46E5" stopOpacity={0.15}/>
                      <stop offset="95%" stopColor="#4F46E5" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="time" tick={{ fill: '#64748B', fontSize: 11, fontFamily: 'sans-serif' }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tickFormatter={(val) => `${val}%`} tick={{ fill: '#64748B', fontSize: 11, fontFamily: 'sans-serif' }} axisLine={false} tickLine={false} />
                  <Tooltip {...LIGHT_CHART_TOOLTIP} formatter={(value) => [`${value}%`, 'Engagement']} />
                  <Area type="monotone" dataKey="pct" stroke="#4F46E5" strokeWidth={2} fillOpacity={1} fill="url(#colorEngagement)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 2. Emotion Flow Tracker */}
          <div className="bg-white shadow-md rounded-xl p-6 text-slate-800">
            <div className="flex justify-between items-center mb-4">
              <p className="text-xs text-slate-500 uppercase tracking-widest font-semibold">Emotion Share Flow</p>
              <div className="flex gap-3 text-[10px] font-medium">
                <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-[#14B8A6]" /> Attentive</span>
                <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B]" /> Confused</span>
                <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-[#F43F5E]" /> Distracted</span>
              </div>
            </div>
            <div className="h-60">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData}>
                  <defs>
                    <linearGradient id="colorAttentive" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#14B8A6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#14B8A6" stopOpacity={0.05}/>
                    </linearGradient>
                    <linearGradient id="colorConfused" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.05}/>
                    </linearGradient>
                    <linearGradient id="colorDistracted" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F43F5E" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#F43F5E" stopOpacity={0.05}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="time" tick={{ fill: '#64748B', fontSize: 11, fontFamily: 'sans-serif' }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tickFormatter={(val) => `${val}%`} tick={{ fill: '#64748B', fontSize: 11, fontFamily: 'sans-serif' }} axisLine={false} tickLine={false} />
                  <Tooltip {...LIGHT_CHART_TOOLTIP} formatter={(value, name) => [`${value}%`, name.charAt(0).toUpperCase() + name.slice(1)]} />
                  <Area type="monotone" dataKey="attentive" stackId="1" stroke="#14B8A6" strokeWidth={1.5} fill="url(#colorAttentive)" />
                  <Area type="monotone" dataKey="confused" stackId="1" stroke="#F59E0B" strokeWidth={1.5} fill="url(#colorConfused)" />
                  <Area type="monotone" dataKey="distracted" stackId="1" stroke="#F43F5E" strokeWidth={1.5} fill="url(#colorDistracted)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* 3. Engagement Drop-off Zones */}
          <div className="bg-white shadow-md rounded-xl p-6 text-slate-800">
            <div className="flex justify-between items-baseline mb-4">
              <p className="text-xs text-slate-500 uppercase tracking-widest font-semibold">Engagement Drop-off Zones</p>
              <span className="text-[10px] text-red-500 font-medium font-sans">Red highlights segments below 50%</span>
            </div>
            <div className="h-60">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trendData}>
                  <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="time" tick={{ fill: '#64748B', fontSize: 11, fontFamily: 'sans-serif' }} axisLine={false} tickLine={false} />
                  <YAxis domain={[0, 100]} tickFormatter={(val) => `${val}%`} tick={{ fill: '#64748B', fontSize: 11, fontFamily: 'sans-serif' }} axisLine={false} tickLine={false} />
                  <Tooltip {...LIGHT_CHART_TOOLTIP} formatter={(value) => [`${value}%`, 'Engagement']} />
                  <Bar dataKey="pct" radius={[6, 6, 0, 0]}>
                    {trendData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={entry.pct < 50 ? '#F43F5E' : '#6366F1'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Semester Report Modal */}
      {showSemesterModal && session && (
        <div className="fixed inset-0 bg-black/95 backdrop-blur-md flex items-center justify-center z-50 p-4 md:p-8 overflow-y-auto animate-fadeIn" onClick={() => setShowSemesterModal(false)}>
          <div className="bg-[#121212] rounded-3xl p-6 md:p-8 w-full max-w-4xl border border-white/10 shadow-2xl relative my-8" onClick={e => e.stopPropagation()}>
            {/* Close button */}
            <button 
              onClick={() => setShowSemesterModal(false)}
              className="absolute top-6 right-6 text-white/40 hover:text-white/85 transition-colors"
            >
              ✕
            </button>

            {/* Locked Content */}
            {(session.semester_sessions_count || 0) < 14 ? (
              <div className="text-center max-w-xl mx-auto py-12 flex flex-col items-center">
                <div className="w-16 h-16 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-white/40 mb-6">
                  <Lock size={28} />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Semester Report Locked</h2>
                <p className="text-sm text-white/60 leading-relaxed mb-6">
                  Semester report is locked. This report will unlock after completing **14 sessions** for this course and time slot.
                </p>
                <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden mb-3">
                  <div 
                    className="bg-white h-full rounded-full transition-all duration-500" 
                    style={{ width: `${Math.min(100, ((session.semester_sessions_count || 0) / 14) * 100)}%` }}
                  />
                </div>
                <div className="flex justify-between w-full text-xs text-white/40 font-mono">
                  <span>Current: {session.semester_sessions_count || 0} sessions completed</span>
                  <span>Goal: 14 sessions</span>
                </div>
                <button
                  onClick={() => setShowSemesterModal(false)}
                  className="mt-8 bg-white text-black text-sm font-semibold rounded-xl px-6 h-11 hover:bg-white/90 transition-all"
                >
                  Close Modal
                </button>
              </div>
            ) : (
              /* Unlocked Content */
              <div className="space-y-6">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-6">
                  <div>
                    <span className="text-xs text-green-400 font-semibold uppercase tracking-widest flex items-center gap-1.5">
                      <Unlock size={14} className="text-green-400" /> Semester Analytics Unlocked
                    </span>
                    <h2 className="text-2xl font-bold text-white mt-1">{session.course_name}</h2>
                    <p className="text-sm text-white/60">
                      {session.time_slot} · {session.semester_sessions_count} total sessions monitored
                    </p>
                  </div>
                  <div>
                    {semesterReport && (
                      <a
                        href={`${API}/api/analytics/semester/report/pdf?course_name=${encodeURIComponent(session.course_name)}&time_slot=${encodeURIComponent(session.time_slot)}&token=${token}`}
                        target="_blank" rel="noreferrer"
                        className="inline-flex items-center gap-2 bg-white text-black text-sm font-semibold rounded-xl px-4 h-11 hover:bg-white/90 active:scale-[0.98] transition-all"
                      >
                        <FileText size={16} /> Download Full Semester PDF
                      </a>
                    )}
                  </div>
                </div>

                {semesterLoading ? (
                  <div className="flex items-center justify-center py-20">
                    <span className="w-8 h-8 border-2 border-white/10 border-t-white/60 rounded-full animate-spin" />
                  </div>
                ) : semesterError ? (
                  <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 text-center my-6">
                    {semesterError}
                  </div>
                ) : semesterReport ? (
                  <div className="space-y-6 max-h-[70vh] overflow-y-auto pr-2">
                    {/* KPI Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[
                        { label: 'Semester Average', value: `${semesterReport.overall_avg_engagement.toFixed(1)}%` },
                        { label: 'Peak Session',     value: `${semesterReport.peak_engagement.toFixed(1)}%` },
                        { label: 'Lowest Session',   value: `${semesterReport.min_engagement.toFixed(1)}%` },
                      ].map((s) => (
                        <div key={s.label} className="bg-[#1A1A1A] rounded-2xl p-4 border border-white/5">
                          <span className="text-xs text-white/40 uppercase tracking-widest">{s.label}</span>
                          <p className="text-2xl font-bold text-white mt-1 tracking-tight">{s.value}</p>
                        </div>
                      ))}
                    </div>

                    {/* Charts Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      {/* Pie Chart */}
                      <div className="bg-[#1A1A1A] rounded-3xl border border-white/5 p-6 flex flex-col justify-between h-[320px]">
                        <div>
                          <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider">Semester Emotion Share</h3>
                          <p className="text-xs text-white/30 mt-0.5">Cumulative share over all semester frames</p>
                        </div>

                        <div className="h-[160px] relative flex items-center justify-center">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie 
                                data={[
                                  { name: 'Attentive', value: semesterReport.total_attentive || 0, color: '#14B8A6' },
                                  { name: 'Confused', value: semesterReport.total_confused || 0, color: '#F59E0B' },
                                  { name: 'Distracted', value: semesterReport.total_distracted || 0, color: '#F43F5E' }
                                ]} 
                                dataKey="value" cx="50%" cy="50%" innerRadius={35} outerRadius={60} paddingAngle={4}
                              >
                                {[
                                  { color: '#14B8A6' },
                                  { color: '#F59E0B' },
                                  { color: '#F43F5E' }
                                ].map((entry, idx) => (
                                  <Cell key={`cell-${idx}`} fill={entry.color} />
                                ))}
                              </Pie>
                              <Tooltip 
                                {...CHART_TOOLTIP} 
                                formatter={(value, name) => {
                                  const total = (semesterReport.total_attentive || 0) + (semesterReport.total_confused || 0) + (semesterReport.total_distracted || 0);
                                  const pct = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
                                  return [`${pct}%`, name];
                                }}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                        </div>

                        <div className="flex justify-around text-xs border-t border-white/5 pt-4">
                          {[
                            { name: 'Attentive', color: '#14B8A6' },
                            { name: 'Confused', color: '#F59E0B' },
                            { name: 'Distracted', color: '#F43F5E' }
                          ].map(d => (
                            <div key={d.name} className="flex items-center gap-1.5">
                              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                              <span className="text-white/60 text-xs">{d.name}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Area Chart showing Session 1 to Session 14 progression */}
                      <div className="bg-[#1A1A1A] rounded-3xl border border-white/5 p-6 flex flex-col justify-between h-[320px] lg:col-span-2">
                        <div>
                          <h3 className="text-sm font-semibold text-white/60 uppercase tracking-wider">Semester Progression Trend</h3>
                          <p className="text-xs text-white/30 mt-0.5">Average session-by-session engagement progression</p>
                        </div>

                        <div className="h-[200px] w-full mt-4">
                          <ResponsiveContainer width="100%" height="100%">
                            <AreaChart 
                              data={semesterReport.sessions.map((s, idx) => ({
                                label: `S${idx + 1}`,
                                engagement: s.avg_engagement,
                                sessionId: s.session_id
                              }))} 
                              margin={{ left: -20, right: 10, top: 10, bottom: 5 }}
                            >
                              <defs>
                                <linearGradient id="colorSemesterProgression" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="#818CF8" stopOpacity={0.2}/>
                                  <stop offset="95%" stopColor="#818CF8" stopOpacity={0}/>
                                </linearGradient>
                              </defs>
                              <CartesianGrid strokeDasharray="4 4" vertical={false} stroke="rgba(255,255,255,0.05)" />
                              <XAxis dataKey="label" tick={{ fill: 'rgba(255,255,255,0.25)', fontSize: 10, fontFamily: 'sans-serif' }} axisLine={false} tickLine={false} />
                              <YAxis domain={[0, 100]} tick={{ fill: 'rgba(255,255,255,0.25)', fontSize: 10, fontFamily: 'sans-serif' }} axisLine={false} tickLine={false} />
                              <Tooltip {...CHART_TOOLTIP} formatter={(value) => [`${value}%`, 'Avg Engagement']} />
                              <Area type="monotone" dataKey="engagement" stroke="#818CF8" strokeWidth={2} fillOpacity={1} fill="url(#colorSemesterProgression)" activeDot={{ r: 5 }} name="Avg Engagement" />
                            </AreaChart>
                          </ResponsiveContainer>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-20 text-white/40">
                    No data loaded.
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
          </>
        )}
      </main>
    </div>
  );
}
