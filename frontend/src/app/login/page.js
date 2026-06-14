'use client';

import { useState } from 'react';
import { useTransitionRouter } from '../context/TransitionContext';
import Link from 'next/link';
import { Eye, EyeOff, LogIn } from 'lucide-react';
// ── GLOBAL LOADER HOOK IMPORT ──
import { useGlobalLoading } from '../context/LoadingContext';
const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function LoginPage() {
  const router = useTransitionRouter();
  const { startLoading, stopLoading } = useGlobalLoading(); // <-- Global loading controllers nikal liye
  const [form, setForm]         = useState({ username: '', password: '' });
  const [showPass, setShowPass] = useState(false);
  const [error, setError]       = useState('');

  async function handleLogin(e) {
    e.preventDefault();
    setError('');
    
    try {
      startLoading(); // <-- API hit hone se pehle premium "C" loader ON!
      
      const res = await fetch(`${API}/auth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams({ username: form.username, password: form.password }),
      });
      
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Authentication failed');
      
      localStorage.setItem('cs_token', data.access_token);
      
      // Check role by calling /auth/me
      const profileRes = await fetch(`${API}/auth/me`, {
        headers: { 'Authorization': `Bearer ${data.access_token}` }
      });
      if (profileRes.ok) {
        const profile = await profileRes.json();
        if (profile.role === 'admin') {
          router.push('/admin/dashboard');
        } else if (profile.role === 'hod') {
          router.push('/hod/dashboard');
        } else {
          router.push('/dashboard');
        }
      } else {
        router.push('/dashboard');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      stopLoading(); // <-- Response milte hi (chahe success ho ya error) global loader OFF!
    }
  }

  return (
    <div className="min-h-screen bg-black flex flex-col text-[#E1E0CC]">

      {/* ── BACK BUTTON ── */}
      <div className="fixed top-5 left-5 z-50">
        <Link
          href="/"
          className="group flex items-center gap-2 bg-[#1A1A1A]/60 backdrop-blur-md border border-white/10 rounded-full px-4 py-2 text-xs font-medium text-[#E1E0CC]/70 hover:text-[#E1E0CC] hover:border-white/20 hover:bg-[#1A1A1A]/80 transition-all duration-200"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="group-hover:-translate-x-0.5 transition-transform duration-200"
          >
            <path d="M19 12H5" />
            <path d="M12 5l-7 7 7 7" />
          </svg>
          Home
        </Link>
      </div>

      {/* ── MAIN CONTENT ── */}
      <div className="flex flex-1">

        {/* ── Left Hero Column ── */}
        <div className="hidden lg:flex w-[52%] relative overflow-hidden bg-[#0a0a0a] items-center justify-center">
          {/* Subtle grid pattern */}
          <div
            className="absolute inset-0 opacity-20"
            style={{
              backgroundImage: `linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
                                linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)`,
              backgroundSize: '40px 40px',
            }}
          />
          {/* Center content */}
          <div className="relative z-10 px-16 max-w-lg">
            <div className="mb-8">
              <span className="text-xs font-medium text-white/30 uppercase tracking-widest">ClassSense</span>
            </div>
            <h1 className="text-4xl font-medium tracking-tight text-white leading-snug mb-6">
              Real-time classroom intelligence.
            </h1>
            <p className="text-sm text-white/40 leading-relaxed mb-12">
              Monitor student engagement, detect emotion states, and receive actionable insights all in one focused dashboard.
            </p>
            {/* Stat pills */}
            <div className="flex flex-col gap-3">
              {[
                { label: 'Avg Engagement Tracked', value: '92%', color: 'text-green-400' },
                { label: 'Frames Analysed / Session', value: '1,400+', color: 'text-white' },
                { label: 'Detection Accuracy', value: '98.3%', color: 'text-white' },
              ].map((s) => (
                <div key={s.label} className="flex items-center justify-between bg-[#1A1A1A] rounded-xl px-4 py-3 border border-white/5">
                  <span className="text-xs text-white/40">{s.label}</span>
                  <span className={`text-sm font-semibold ${s.color}`}>{s.value}</span>
                </div>
              ))}
            </div>
            <p className="text-xs text-white/30 text-center mt-6">
              Trusted by instructors at Iqra University
            </p>
          </div>
        </div>

        {/* ── Right Form Column ── */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="w-full max-w-sm">

            {/* Logo */}
            <div className="mb-10">
              <h2 className="text-xl font-semibold tracking-tight text-white flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-400"></span> ClassSense
              </h2>
              <p className="text-sm text-white/40 mt-1">Instructor Portal</p>
            </div>

            {/* Heading */}
            <div className="mb-8">
              <h1 className="text-3xl font-medium tracking-tight text-white">Welcome back</h1>
              <p className="text-sm text-white/60 mt-2 leading-relaxed">
                Log in to your ClassSense account
              </p>
            </div>

            {/* Form */}
            <form onSubmit={handleLogin} className="space-y-4">
              {/* Email */}
              <div>
                <label className="text-sm font-medium text-white mb-1.5 block">Email address</label>
                <input
                  type="email"
                  placeholder="instructor@classsense.com"
                  value={form.username}
                  onChange={e => setForm({ ...form, username: e.target.value })}
                  required
                  className="w-full bg-[#1A1A1A] border-none rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-2 focus:ring-white/20 focus:outline-none text-sm"
                />
              </div>

              {/* Password */}
              <div>
                <label className="text-sm font-medium text-white mb-1.5 block">Password</label>
                <div className="relative">
                  <input
                    type={showPass ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={form.password}
                    onChange={e => setForm({ ...form, password: e.target.value })}
                    required
                    className="w-full bg-[#1A1A1A] border-none rounded-xl h-11 px-4 pr-10 text-white placeholder:text-white/20 focus:ring-2 focus:ring-white/20 focus:outline-none text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass(!showPass)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 cursor-pointer hover:text-white/60 transition-colors"
                  >
                    {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {/* Remember me & Forgot Password */}
              <div className="flex items-center justify-between text-xs py-1">
                <label className="flex items-center gap-2 text-white/60 cursor-pointer select-none">
                  <input type="checkbox" className="rounded border-white/10 bg-[#1A1A1A] focus:ring-0 focus:ring-offset-0 text-white" />
                  Remember me
                </label>
                <a href="#" className="text-green-400 hover:underline">Forgot Password?</a>
              </div>

              {/* Error */}
              {error && (
                <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-xs text-red-400">
                  {error}
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                className="w-full h-14 bg-white text-black font-semibold rounded-xl hover:bg-white/90 active:scale-[0.98] transition-all duration-150 text-sm flex items-center justify-center gap-2 mt-2"
              >
                <LogIn size={16} /> Log In →
              </button>
            </form>

            {/* Hint */}
            <p className="text-xs text-white/20 text-center mt-8 leading-relaxed">
              Default credentials: instructor@classsense.com / instructor123
            </p>
          </div>
        </div>

      </div>

    </div>
  );
}