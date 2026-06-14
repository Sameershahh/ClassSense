'use client';

import { useEffect, useState } from 'react';
import { useTransitionRouter } from '../../context/TransitionContext';
import Sidebar from '../../components/Sidebar';
import { BookOpen, Calendar, MapPin, CheckCircle, Video, Upload, Play, AlertCircle } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const authHeader = () => {
  const t = typeof window !== 'undefined' ? localStorage.getItem('cs_token') : '';
  return t ? { Authorization: `Bearer ${t}` } : {};
};

export default function InstructorCoursesPage() {
  const router = useTransitionRouter();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Start Session Modal States
  const [modal, setModal] = useState({ open: false, slotId: null, courseCode: '', courseName: '' });
  const [starting, setStarting] = useState(false);

  async function fetchAssignedCourses() {
    try {
      setLoading(true);
      setError('');
      
      const token = localStorage.getItem('cs_token');
      console.log('[fetchAssignedCourses] Token check:', token ? 'Token exists' : 'Token missing');
      
      const res = await fetch(`${API}/api/sessions/assigned`, {
        headers: {
          'Authorization': `Bearer ${token || ''}`,
          'Accept': 'application/json'
        }
      });

      console.log('[fetchAssignedCourses] Response status received:', res.status);
      
      if (res.status === 401) {
        console.warn('[fetchAssignedCourses] Session expired/unauthorized. Routing to login.');
        router.push('/');
        return;
      }
      
      if (!res.ok) {
        const errorBody = await res.json().catch(() => ({}));
        console.error('[fetchAssignedCourses] Server rejected request:', errorBody);
        throw new Error(errorBody.detail || 'Failed to load pre-assigned courses.');
      }
      
      const data = await res.json();
      console.log('[fetchAssignedCourses] Loaded courses successfully:', data);
      setCourses(data);
    } catch (err) {
      console.error('[fetchAssignedCourses] Fetch failed with error:', err);
      setError(err.message || 'Failed to load pre-assigned courses.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchAssignedCourses();
  }, []);

  async function handleStartSession(mode) {
    if (!modal.slotId) return;

    setStarting(true);
    try {
      const res = await fetch(`${API}/api/sessions/`, {
        method: 'POST',
        headers: {
          ...authHeader(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          course_slot_id: modal.slotId,
          mode: mode,
          instructor_id: 1
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to start session.');
      }

      const data = await res.json();
      setModal({ open: false, slotId: null, courseCode: '', courseName: '' });
      
      // Redirect to the newly created session details page
      router.push(`/session/${data.session_id}`);
    } catch (err) {
      alert(err.message);
    } finally {
      setStarting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen bg-black">
        <Sidebar />
        <main className="flex-1 flex flex-col items-center justify-center gap-4">
          <div className="w-10 h-10 rounded-full border-2 border-white/10 border-t-[#DEDBC8] animate-spin" />
          <p className="text-xs text-white/40">Loading assigned courses...</p>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-black">
      <Sidebar />

      <main className="flex-1 overflow-y-auto p-8 max-w-6xl">
        
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-medium tracking-tight text-white">My Pre-Assigned Courses</h1>
          <p className="text-sm text-white/60 mt-1 leading-relaxed">
            Manage your HOD-assigned lectures, view past analytics, or launch a live session.
          </p>
        </div>

        {error && (
          <div className="rounded-2xl border border-red-500/10 bg-red-500/5 p-6 text-center max-w-xl mb-6">
            <p className="text-red-400 text-sm mb-4">{error}</p>
            <button
              onClick={fetchAssignedCourses}
              className="bg-[#1A1A1A] hover:bg-[#242424] text-white border border-white/10 rounded-xl px-4 py-2 text-xs transition-colors"
            >
              Retry
            </button>
          </div>
        )}

        {/* Courses Cards Grid */}
        {courses.length === 0 ? (
          <div className="text-center py-20 border border-dashed border-white/5 rounded-3xl bg-[#101010]/40 max-w-xl">
            <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-white/20 mx-auto mb-4">
              <BookOpen size={20} />
            </div>
            <h3 className="text-base font-semibold text-white mb-1">No Assigned Courses</h3>
            <p className="text-xs text-white/40 max-w-xs mx-auto leading-relaxed">
              You do not have any lectures mapped by your Head of Department. Please contact your HOD for syllabus distribution.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {courses.map((course) => (
              <div
                key={course.slot_id}
                className="bg-[#1A1A1A] border border-white/5 rounded-3xl p-6 space-y-6 hover:border-white/10 transition-all duration-200"
              >
                {/* Course Header */}
                <div className="flex justify-between items-start gap-4">
                  <div className="space-y-1">
                    <span className="inline-flex items-center gap-1 rounded-full bg-[#DEDBC8]/10 text-[#DEDBC8] text-[10px] font-semibold px-2.5 py-0.5">
                      {course.course_code}
                    </span>
                    <h2 className="text-lg font-semibold tracking-tight text-white line-clamp-1">{course.course_name}</h2>
                  </div>
                </div>

                {/* Logistics */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-white/5 text-xs text-white/60">
                  <div className="flex items-center gap-2">
                    <Calendar size={14} className="text-white/20" />
                    <span>{course.time_slot}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin size={14} className="text-white/20" />
                    <span>{course.room_name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle size={14} className="text-white/20" />
                    <span>{course.sessions_completed} Lectures Monitored</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="grid grid-cols-2 gap-3 pt-4 border-t border-white/5">
                  <button
                    onClick={() => {
                      const fullCourseName = `${course.course_code} — ${course.course_name}`;
                      router.push(`/dashboard?course_name=${encodeURIComponent(fullCourseName)}&time_slot=${encodeURIComponent(course.time_slot)}`);
                    }}
                    className="h-11 bg-[#101010] border border-white/10 hover:bg-[#1A1A1A] hover:border-white/20 text-white font-medium rounded-xl text-xs flex items-center justify-center gap-1.5 transition-all cursor-pointer"
                  >
                    View Analytics
                  </button>
                  <button
                    onClick={() => setModal({ open: true, slotId: course.slot_id, courseCode: course.course_code, courseName: course.course_name })}
                    className="h-11 bg-white hover:bg-white/95 text-black font-semibold rounded-xl text-xs flex items-center justify-center gap-1.5 transition-all cursor-pointer"
                  >
                    <Play size={12} fill="black" /> Start Session
                  </button>
                </div>

              </div>
            ))}
          </div>
        )}

      </main>

      {/* ── START SESSION MODAL ── */}
      {modal.open && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[9999]">
          <div className="bg-[#101010] border border-white/10 rounded-3xl w-full max-w-lg p-8 space-y-6 relative">
            
            {/* Modal Header */}
            <div>
              <span className="text-[10px] text-white/40 uppercase tracking-widest font-semibold block mb-1">Launch Lecture Session</span>
              <h2 className="text-xl font-bold tracking-tight text-white">
                {modal.courseCode} — {modal.courseName}
              </h2>
              <p className="text-xs text-white/30 mt-1">Select the collection mode for emotion tracking.</p>
            </div>

            {/* Mode Cards Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Mode: Live Camera */}
              <button
                disabled={starting}
                onClick={() => handleStartSession('live')}
                className="group p-6 rounded-2xl border border-white/5 bg-[#1A1A1A]/40 text-left hover:bg-[#1A1A1A] hover:border-white/10 transition-all flex flex-col justify-between h-48 cursor-pointer disabled:opacity-50"
              >
                <div className="w-10 h-10 rounded-xl bg-green-500/10 text-green-400 flex items-center justify-center">
                  <Video size={18} />
                </div>
                <div className="space-y-1">
                  <h3 className="font-semibold text-white text-sm group-hover:text-[#DEDBC8] transition-colors">Live Camera Stream</h3>
                  <p className="text-[10px] text-white/30 leading-normal">
                    Pulls real-time frames from preconfigured RTSP room cameras automatically.
                  </p>
                </div>
              </button>

              {/* Mode: Video Upload */}
              <button
                disabled={starting}
                onClick={() => handleStartSession('video')}
                className="group p-6 rounded-2xl border border-white/5 bg-[#1A1A1A]/40 text-left hover:bg-[#1A1A1A] hover:border-white/10 transition-all flex flex-col justify-between h-48 cursor-pointer disabled:opacity-50"
              >
                <div className="w-10 h-10 rounded-xl bg-[#DEDBC8]/10 text-[#DEDBC8] flex items-center justify-center">
                  <Upload size={18} />
                </div>
                <div className="space-y-1">
                  <h3 className="font-semibold text-white text-sm group-hover:text-[#DEDBC8] transition-colors">Upload Recorded Video</h3>
                  <p className="text-[10px] text-white/30 leading-normal">
                    Manually drag-and-drop or select an MP4 recording file after lecture completion.
                  </p>
                </div>
              </button>

            </div>

            {/* Modal Actions */}
            <div className="flex justify-end pt-2 border-t border-white/5">
              <button
                disabled={starting}
                onClick={() => setModal({ open: false, slotId: null, courseCode: '', courseName: '' })}
                className="h-11 px-6 border border-white/5 rounded-xl hover:bg-white/5 text-xs text-white/60 hover:text-white transition-colors cursor-pointer disabled:opacity-35"
              >
                Cancel
              </button>
            </div>

            {starting && (
              <div className="absolute inset-0 bg-black/60 rounded-3xl flex flex-col items-center justify-center gap-3">
                <div className="w-8 h-8 rounded-full border-2 border-white/10 border-t-[#DEDBC8] animate-spin" />
                <p className="text-xs text-white/40">Initializing session engine...</p>
              </div>
            )}

          </div>
        </div>
      )}

    </div>
  );
}
