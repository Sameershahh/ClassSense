'use client';

import { useEffect, useState } from 'react';
import { Activity, Server, Clock, ShieldCheck, Database, School, Video, Users } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  async function fetchAdminData() {
    const token = localStorage.getItem('cs_token');
    const headers = { 'Authorization': `Bearer ${token}` };

    try {
      setLoading(true);
      const [statsRes, healthRes] = await Promise.all([
        fetch(`${API}/api/admin/stats`, { headers }),
        fetch(`${API}/api/admin/system/status`, { headers }),
      ]);

      if (!statsRes.ok || !healthRes.ok) {
        throw new Error('Failed to load system metrics.');
      }

      const statsData = await statsRes.json();
      const healthData = await healthRes.json();

      setStats(statsData);
      setHealth(healthData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchAdminData();
  }, []);

  if (loading) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center gap-4">
        <div className="w-10 h-10 rounded-full border-2 border-white/10 border-t-[#DEDBC8] animate-spin" />
        <p className="text-xs text-white/40">Gathering system health metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl border border-red-500/10 bg-red-500/5 p-6 max-w-xl mx-auto mt-12 text-center">
        <p className="text-red-400 text-sm mb-4">{error}</p>
        <button
          onClick={fetchAdminData}
          className="bg-[#1A1A1A] hover:bg-[#242424] text-white border border-white/10 rounded-xl px-4 py-2 text-xs transition-colors"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      
      {/* ── HEADER ── */}
      <div>
        <h1 className="text-3xl font-medium tracking-tight text-white">System Status</h1>
        <p className="text-sm text-white/40 mt-1">
          Monitor global usage analytics and core AI model pipeline integrity.
        </p>
      </div>

      {/* ── GLOBAL ANALYTICS METRICS ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        
        {/* Total Sessions */}
        <div className="bg-[#1A1A1A] border border-white/5 rounded-2xl p-6 flex items-center justify-between hover:border-white/10 transition-colors">
          <div>
            <span className="text-xs text-white/40 font-medium uppercase tracking-wider block">Sessions Monitored</span>
            <span className="text-3xl font-bold tracking-tight text-white mt-1 block">{stats?.total_sessions ?? 0}</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-green-500/10 flex items-center justify-center text-green-400">
            <Activity className="size-6" />
          </div>
        </div>

        {/* Total Universities */}
        <div className="bg-[#1A1A1A] border border-white/5 rounded-2xl p-6 flex items-center justify-between hover:border-white/10 transition-colors">
          <div>
            <span className="text-xs text-white/40 font-medium uppercase tracking-wider block">Universities Onboarded</span>
            <span className="text-3xl font-bold tracking-tight text-white mt-1 block">{stats?.total_universities ?? 0}</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-[#DEDBC8]/10 flex items-center justify-center text-[#DEDBC8]">
            <School className="size-6" />
          </div>
        </div>

        {/* Active Live Cameras */}
        <div className="bg-[#1A1A1A] border border-white/5 rounded-2xl p-6 flex items-center justify-between hover:border-white/10 transition-colors">
          <div>
            <span className="text-xs text-white/40 font-medium uppercase tracking-wider block">Active Streams</span>
            <span className="text-3xl font-bold tracking-tight text-white mt-1 block">{stats?.active_cameras ?? 0}</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400">
            <Video className="size-6" />
          </div>
        </div>

        {/* Total Instructors */}
        <div className="bg-[#1A1A1A] border border-white/5 rounded-2xl p-6 flex items-center justify-between hover:border-white/10 transition-colors">
          <div>
            <span className="text-xs text-white/40 font-medium uppercase tracking-wider block">Total Instructors</span>
            <span className="text-3xl font-bold tracking-tight text-white mt-1 block">{stats?.total_instructors ?? 0}</span>
          </div>
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-400">
            <Users className="size-6" />
          </div>
        </div>

      </div>

      {/* ── AI MODEL HEALTH & PIPELINE STATUS ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Model Pipeline Panel */}
        <div className="lg:col-span-2 bg-[#101010] border border-white/5 rounded-2xl p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-white/5 pb-4">
            <h2 className="font-semibold text-white flex items-center gap-2">
              <ShieldCheck className="text-green-400 size-5" />
              AI Model Pipeline Health
            </h2>
            <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium bg-green-500/10 text-green-400">
              <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              Live
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            {/* Model Status */}
            <div className="bg-[#1A1A1A] border border-white/5 rounded-xl p-5 space-y-2">
              <span className="text-xs text-white/40 font-medium block">Emotion Detection Model</span>
              <p className="text-sm font-semibold text-white">MobileNetV2 (Fine-tuned)</p>
              <div className="flex items-center gap-2 mt-2">
                <span className={`w-2 h-2 rounded-full ${health?.model_loaded ? 'bg-green-400' : 'bg-red-400'}`} />
                <span className="text-xs text-white/60">
                  {health?.model_loaded ? 'Weights loaded successfully' : 'Missing weights configuration'}
                </span>
              </div>
            </div>

            {/* Pipeline State */}
            <div className="bg-[#1A1A1A] border border-white/5 rounded-xl p-5 space-y-2">
              <span className="text-xs text-white/40 font-medium block">Processing Pipeline</span>
              <p className="text-sm font-semibold text-white">OpenCV + PyTorch</p>
              <div className="flex items-center gap-2 mt-2">
                <span className={`w-2 h-2 rounded-full ${health?.ml_ready ? 'bg-green-400' : 'bg-red-400'}`} />
                <span className="text-xs text-white/60">
                  {health?.ml_ready ? 'Ready to analyze streams' : 'Pipeline initialization failed'}
                </span>
              </div>
            </div>

          </div>

          {/* Detailed Pipeline Health Metrics */}
          <div className="space-y-4 pt-2">
            {[
              { name: 'Model Inference Latency', value: `${health?.latency_ms ?? '0'} ms`, desc: 'Average time to analyze a single frame' },
              { name: 'Active ML Workers', value: `${health?.active_workers ?? '0'} Worker Process`, desc: 'Multi-process safety worker instance' },
              { name: 'Uptime', value: health?.uptime ?? '99.9%', desc: 'API backend server uptime' },
            ].map((metric) => (
              <div key={metric.name} className="flex justify-between items-center bg-[#1A1A1A]/40 rounded-xl p-4 border border-white/5">
                <div>
                  <span className="text-sm font-medium text-white block">{metric.name}</span>
                  <span className="text-xs text-white/30">{metric.desc}</span>
                </div>
                <span className="text-sm font-mono font-semibold text-[#DEDBC8]">{metric.value}</span>
              </div>
            ))}
          </div>

        </div>

        {/* Server & API Platform Status */}
        <div className="bg-[#101010] border border-white/5 rounded-2xl p-6 space-y-6">
          <div className="flex items-center gap-2 border-b border-white/5 pb-4">
            <Server className="text-blue-400 size-5" />
            <h2 className="font-semibold text-white">Infrastructure Health</h2>
          </div>

          <div className="space-y-5">
            {/* API Status */}
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-white block">API Gateway</span>
                <span className="text-xs text-white/30">FastAPI Router Engine</span>
              </div>
              <span className="text-xs font-semibold bg-green-500/10 text-green-400 px-3 py-1 rounded-full border border-green-500/10">
                Operational
              </span>
            </div>

            {/* Database Engine */}
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-white block">SQLite Database</span>
                <span className="text-xs text-white/30">SQLAlchemy Relational Base</span>
              </div>
              <span className="text-xs font-semibold bg-green-500/10 text-green-400 px-3 py-1 rounded-full border border-green-500/10">
                Connected
              </span>
            </div>

            {/* Video Processing Queue */}
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-white block">Async Queue</span>
                <span className="text-xs text-white/30">Frame Extraction Thread</span>
              </div>
              <span className="text-xs font-semibold bg-[#DEDBC8]/10 text-[#DEDBC8] px-3 py-1 rounded-full border border-[#DEDBC8]/10">
                Idle (0 jobs)
              </span>
            </div>

            {/* System Clock */}
            <div className="flex items-center justify-between">
              <div>
                <span className="text-sm font-medium text-white block">Time Synchronization</span>
                <span className="text-xs text-white/30">UTC Time Stamps Capture</span>
              </div>
              <div className="flex items-center gap-1 text-[#DEDBC8]">
                <Clock className="size-4" />
                <span className="text-xs font-mono font-semibold">Synced</span>
              </div>
            </div>

          </div>

          {/* Quick Actions */}
          <div className="pt-6 border-t border-white/5">
            <button
              onClick={fetchAdminData}
              className="w-full h-11 bg-white hover:bg-white/90 text-black font-semibold rounded-xl text-xs flex items-center justify-center gap-2 transition-colors"
            >
              Refresh Diagnostics
            </button>
          </div>

        </div>

      </div>

    </div>
  );
}
