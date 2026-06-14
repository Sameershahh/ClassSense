'use client';

import { useEffect, useState } from 'react';
import { Plus, Check, Award, BookOpen, Layers, Users, Mail, Lock, ChevronRight, Calendar, Activity, Video, UserCheck } from 'lucide-react';
import Link from 'next/link';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function HodDashboard() {
  const [depts, setDepts] = useState([]);
  const [courses, setCourses] = useState([]);
  const [instructors, setInstructors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [activeTab, setActiveTab] = useState('onboard'); // 'onboard' or 'monitor'
  const [selectedInstructorId, setSelectedInstructorId] = useState(null);
  const [selectedSlotId, setSelectedSlotId] = useState(null);
  const [instructorSessions, setInstructorSessions] = useState([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  useEffect(() => {
    if (activeTab === 'monitor' && instructors.length > 0) {
      if (!selectedInstructorId) {
        setSelectedInstructorId(instructors[0].id);
        setSelectedSlotId(null);
      }
    }
  }, [activeTab, instructors, selectedInstructorId]);

  useEffect(() => {
    if (selectedInstructorId) {
      fetchInstructorSessions(selectedInstructorId, selectedSlotId);
    }
  }, [selectedInstructorId, selectedSlotId]);

  async function fetchInstructorSessions(instructorId, slotId = null) {
    const token = localStorage.getItem('cs_token');
    const headers = { 'Authorization': `Bearer ${token}` };
    try {
      setSessionsLoading(true);
      let url = `${API}/api/sessions/?instructor_id=${instructorId}&limit=100`;
      if (slotId) {
        url += `&course_slot_id=${slotId}`;
      }
      console.log(`[fetchInstructorSessions] Fetching sessions from URL: ${url}`);
      
      const res = await fetch(url, { headers });
      if (res.ok) {
        const data = await res.json();
        console.log('[fetchInstructorSessions] Sessions fetched successfully:', data);
        setInstructorSessions(data);
      } else {
        const errText = await res.text();
        console.error(`[fetchInstructorSessions] API error! Status: ${res.status}, Body: ${errText}`);
      }
    } catch (err) {
      console.error('[fetchInstructorSessions] Fetch execution failed with exception:', err);
    } finally {
      setSessionsLoading(false);
    }
  }

  // Form State
  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    department_code: ''
  });
  
  // Selected course slots for assignment
  const [selectedSlotIds, setSelectedSlotIds] = useState([]);

  async function fetchInitialData() {
    const token = localStorage.getItem('cs_token');
    const headers = { 'Authorization': `Bearer ${token}` };

    try {
      setLoading(true);
      const [deptRes, instRes] = await Promise.all([
        fetch(`${API}/api/hod/departments`, { headers }),
        fetch(`${API}/api/hod/instructors`, { headers }),
      ]);

      if (!deptRes.ok || !instRes.ok) {
        throw new Error('Failed to load HOD metrics and configurations.');
      }

      const deptData = await deptRes.json();
      const instData = await instRes.json();

      setDepts(deptData);
      setInstructors(instData);

      if (deptData.length > 0) {
        setForm(prev => ({ ...prev, department_code: deptData[0].code }));
        fetchCourses(deptData[0].code);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function fetchCourses(deptCode) {
    if (!deptCode) return;
    const token = localStorage.getItem('cs_token');
    const headers = { 'Authorization': `Bearer ${token}` };

    try {
      const res = await fetch(`${API}/api/hod/courses?dept_code=${deptCode}`, { headers });
      if (res.ok) {
        const data = await res.json();
        setCourses(data);
        // Reset selected slots when department changes
        setSelectedSlotIds([]);
      }
    } catch (err) {
      console.error('Failed to load department courses:', err);
    }
  }

  useEffect(() => {
    fetchInitialData();
  }, []);

  // Fetch courses whenever HOD updates the select dropdown
  function handleDeptChange(e) {
    const code = e.target.value;
    setForm(prev => ({ ...prev, department_code: code }));
    fetchCourses(code);
  }

  // Toggle selection of a course slot
  function handleSlotToggle(slotId) {
    setSelectedSlotIds(prev =>
      prev.includes(slotId)
        ? prev.filter(id => id !== slotId)
        : [...prev, slotId]
    );
  }

  async function handleOnboardSubmit(e) {
    e.preventDefault();
    const token = localStorage.getItem('cs_token');
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };

    if (selectedSlotIds.length === 0) {
      alert('Please assign at least one course slot to the instructor.');
      return;
    }

    const payload = {
      name: form.name,
      email: form.email,
      password: form.password,
      department_code: form.department_code,
      course_slot_ids: selectedSlotIds
    };

    try {
      const res = await fetch(`${API}/api/hod/instructors`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to onboard instructor.');
      }

      alert('Instructor onboarded successfully and course slots mapped!');
      
      // Reset form
      setForm(prev => ({
        ...prev,
        name: '',
        email: '',
        password: ''
      }));
      setSelectedSlotIds([]);
      
      // Refresh instructor list
      const instRes = await fetch(`${API}/api/hod/instructors`, { headers });
      if (instRes.ok) {
        const instData = await instRes.json();
        setInstructors(instData);
      }
    } catch (err) {
      alert(err.message);
    }
  }

  if (loading) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center gap-4">
        <div className="w-10 h-10 rounded-full border-2 border-white/10 border-t-[#DEDBC8] animate-spin" />
        <p className="text-xs text-white/40">Loading department configurations...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* ── HEADER ── */}
      <div>
        <h1 className="text-3xl font-medium tracking-tight text-white">Department Console</h1>
        <p className="text-sm text-white/40 mt-1">Onboard instructors and distribute pre-assigned courses and rooms.</p>
      </div>

      {/* ── TABS ── */}
      <div className="flex gap-4 border-b border-white/5 pb-1">
        <button
          onClick={() => setActiveTab('onboard')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-all cursor-pointer ${
            activeTab === 'onboard'
              ? 'border-[#DEDBC8] text-white'
              : 'border-transparent text-white/40 hover:text-white/60'
          }`}
        >
          Manage & Onboard
        </button>
        <button
          onClick={() => setActiveTab('monitor')}
          className={`pb-3 text-sm font-semibold border-b-2 transition-all cursor-pointer ${
            activeTab === 'monitor'
              ? 'border-[#DEDBC8] text-white'
              : 'border-transparent text-white/40 hover:text-white/60'
          }`}
        >
          Monitor Faculty
        </button>
      </div>

      {error && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-xs text-red-400">
          {error}
        </div>
      )}

      {/* ── ONBOARD TAB CONTENT ── */}
      {activeTab === 'onboard' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start animate-fadeIn">
          
          {/* Left Column: Onboard Instructor Form */}
          <div className="lg:col-span-7 bg-[#101010] border border-white/5 rounded-2xl p-6 space-y-6">
            <div className="border-b border-white/5 pb-4">
              <h2 className="font-semibold text-white text-base flex items-center gap-2">
                <UserPlusIcon className="text-[#DEDBC8] size-5" />
                Onboard & Map Instructor
              </h2>
              <p className="text-xs text-white/30">Create instructor login and assign course slots immediately.</p>
            </div>

            <form onSubmit={handleOnboardSubmit} className="space-y-5">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                
                {/* Full Name */}
                <div>
                  <label className="text-xs font-medium text-white/60 mb-1.5 block">Instructor Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Dr. Sarah"
                    value={form.name}
                    onChange={e => setForm({ ...form, name: e.target.value })}
                    className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                  />
                </div>

                {/* Email Address */}
                <div>
                  <label className="text-xs font-medium text-white/60 mb-1.5 block">Email Address (Unique)</label>
                  <input
                    type="email"
                    required
                    placeholder="sarah@iqra.edu.pk"
                    value={form.email}
                    onChange={e => setForm({ ...form, email: e.target.value })}
                    className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                  />
                </div>

                {/* Password */}
                <div>
                  <label className="text-xs font-medium text-white/60 mb-1.5 block">Secure Password</label>
                  <input
                    type="password"
                    required
                    placeholder="Min 6 characters"
                    value={form.password}
                    onChange={e => setForm({ ...form, password: e.target.value })}
                    className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                  />
                </div>

                {/* Department */}
                <div>
                  <label className="text-xs font-medium text-white/60 mb-1.5 block">Department</label>
                  <select
                    value={form.department_code}
                    onChange={handleDeptChange}
                    className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                  >
                    {depts.map(d => (
                      <option key={d.id} value={d.code}>{d.name} ({d.code})</option>
                    ))}
                  </select>
                </div>

              </div>

              {/* Course Slot Allocator Checklist */}
              <div className="space-y-3 pt-2">
                <span className="text-xs font-semibold uppercase text-white/30 tracking-wider block">Assign Course Slots ({selectedSlotIds.length} selected)</span>
                
                <div className="border border-white/5 rounded-xl bg-black/40 max-h-72 overflow-y-auto divide-y divide-white/5 p-2">
                  {courses.length === 0 ? (
                    <p className="text-xs text-white/30 text-center py-12">No courses available for this department.</p>
                  ) : (
                    courses.map(c => (
                      <div key={c.id} className="p-3 space-y-2.5">
                        <div className="flex items-center gap-2">
                          <BookOpen size={14} className="text-[#DEDBC8]" />
                          <span className="text-sm font-semibold text-white">{c.course_code} — {c.course_name}</span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pl-6">
                          {c.slots.map(s => {
                            const isChecked = selectedSlotIds.includes(s.id);
                            return (
                              <button
                                key={s.id}
                                type="button"
                                onClick={() => handleSlotToggle(s.id)}
                                className={`flex items-center justify-between p-3 rounded-lg text-left border transition-all text-xs ${
                                  isChecked
                                    ? 'bg-[#DEDBC8]/10 border-[#DEDBC8] text-white'
                                    : 'bg-[#1A1A1A]/40 border-white/5 text-white/40 hover:border-white/10'
                                }`}
                              >
                                <div className="space-y-0.5 pr-2">
                                  <p className="font-medium">{s.time_slot}</p>
                                  <p className="text-[10px] text-white/30">{s.room_name}</p>
                                </div>
                                {isChecked && <Check size={12} className="text-[#DEDBC8]" />}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Onboard Button */}
              <button
                type="submit"
                className="w-full h-12 bg-white hover:bg-white/95 text-black font-semibold rounded-xl text-xs flex items-center justify-center gap-2 transition-colors cursor-pointer"
              >
                Onboard Instructor Account
              </button>
            </form>

          </div>

          {/* Right Column: Active Instructors Directories */}
          <div className="lg:col-span-5 bg-[#101010] border border-white/5 rounded-2xl p-5 space-y-4 max-h-[85vh] overflow-y-auto">
            <h2 className="text-sm font-semibold tracking-wider uppercase text-white/30 px-1">Active Faculty</h2>
            
            {instructors.length === 0 ? (
              <div className="text-center py-12 border border-dashed border-white/5 rounded-xl">
                <p className="text-xs text-white/30">No instructors onboarded yet.</p>
              </div>
            ) : (
              <div className="space-y-3">
                {instructors.map((inst) => (
                  <div key={inst.id} className="bg-[#1A1A1A] border border-white/5 rounded-xl p-4 space-y-3">
                    <div>
                      <h3 className="font-semibold text-white text-sm">{inst.name}</h3>
                      <p className="text-xs text-white/30">{inst.email}</p>
                    </div>
                    
                    <div className="space-y-1.5">
                      <span className="text-[10px] text-white/40 uppercase font-medium tracking-wider block">Assigned Lectures</span>
                      {inst.assigned_courses.length === 0 ? (
                        <p className="text-[10px] text-white/30">No courses assigned.</p>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {inst.assigned_courses.map((c, idx) => (
                            <span
                              key={idx}
                              className="inline-flex items-center gap-1 rounded-full bg-white/5 border border-white/5 px-2 py-0.5 text-[10px] text-white/70"
                              title={`${c.course_name} (${c.time_slot} @ ${c.room_name})`}
                            >
                              {c.course_code}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      )}

      {/* ── MONITOR FACULTY TAB CONTENT ── */}
      {activeTab === 'monitor' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start animate-fadeIn">
          
          {/* Faculty List Sidebar */}
          <div className="lg:col-span-4 bg-[#101010] border border-white/5 rounded-2xl p-5 space-y-4 max-h-[80vh] overflow-y-auto">
            <h2 className="text-sm font-semibold tracking-wider uppercase text-white/30 px-1">Faculty Members</h2>
            {instructors.length === 0 ? (
              <div className="text-center py-12 border border-dashed border-white/5 rounded-xl">
                <p className="text-xs text-white/30">No instructors onboarded yet.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {instructors.map((inst) => {
                  const isSelected = selectedInstructorId === inst.id;
                  return (
                    <button
                      key={inst.id}
                      onClick={() => {
                        setSelectedInstructorId(inst.id);
                        setSelectedSlotId(null);
                      }}
                      className={`w-full text-left p-4 rounded-xl border transition-all duration-200 cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? 'bg-[#DEDBC8]/10 border-[#DEDBC8] text-white font-medium'
                          : 'bg-[#1A1A1A]/40 border-white/5 text-white/60 hover:border-white/10 hover:text-white'
                      }`}
                    >
                      <div className="min-w-0 pr-2">
                        <h3 className="font-semibold text-sm truncate">{inst.name}</h3>
                        <p className="text-xs text-white/30 truncate mt-0.5">{inst.email}</p>
                      </div>
                      <ChevronRight size={14} className={isSelected ? 'text-[#DEDBC8]' : 'text-white/20'} />
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Selected Instructor Detail Panel */}
          <div className="lg:col-span-8 space-y-6">
            {(() => {
              const selectedInst = instructors.find(i => i.id === selectedInstructorId);
              if (!selectedInst) {
                return (
                  <div className="bg-[#101010] border border-white/5 rounded-2xl p-8 text-center py-24">
                    <p className="text-sm text-white/30">Select an instructor from the list to monitor their lectures and sessions.</p>
                  </div>
                );
              }

              return (
                <>
                  {/* Instructor Profile Header Card */}
                  <div className="bg-[#101010] border border-white/5 rounded-2xl p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-xl bg-[#DEDBC8]/10 border border-[#DEDBC8]/30 flex items-center justify-center text-[#DEDBC8] font-bold text-lg">
                        {selectedInst.name.charAt(0)}
                      </div>
                      <div>
                        <h2 className="text-xl font-bold text-white">{selectedInst.name}</h2>
                        <p className="text-xs text-white/40 mt-0.5">{selectedInst.email} · Faculty Instructor</p>
                      </div>
                    </div>
                  </div>

                  {/* Assigned Courses Cards */}
                  <div className="bg-[#101010] border border-white/5 rounded-2xl p-6 space-y-4">
                    <h3 className="text-xs font-semibold uppercase text-white/40 tracking-wider flex items-center gap-1.5">
                      <BookOpen size={14} className="text-[#DEDBC8]" />
                      Assigned Courses & Lecture Rooms
                    </h3>
                    {selectedInst.assigned_courses.length === 0 ? (
                      <p className="text-xs text-white/30">No courses mapped to this instructor yet.</p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {selectedInst.assigned_courses.map((c, idx) => {
                          const isSelected = selectedSlotId === c.slot_id;
                          return (
                            <button
                              key={idx}
                              onClick={() => {
                                if (selectedSlotId === c.slot_id) {
                                  setSelectedSlotId(null);
                                } else {
                                  setSelectedSlotId(c.slot_id);
                                }
                              }}
                              className={`w-full text-left bg-[#1A1A1A]/40 border rounded-xl p-4 space-y-2 transition-all duration-200 cursor-pointer ${
                                isSelected
                                  ? 'border-[#DEDBC8] bg-[#DEDBC8]/5 shadow-sm'
                                  : 'border-white/5 hover:border-white/10'
                              }`}
                            >
                              <div className="flex items-center gap-2">
                                <span className="px-2 py-0.5 rounded-md bg-[#DEDBC8]/10 text-[#DEDBC8] text-[10px] font-semibold">{c.course_code}</span>
                                <h4 className="text-xs font-semibold text-white truncate flex-1">{c.course_name}</h4>
                              </div>
                              <div className="border-t border-white/5 pt-2 flex flex-col gap-1 text-[10px] text-white/40">
                                <p>Schedule: <span className="text-white/60 font-medium">{c.time_slot}</span></p>
                                <p>Room: <span className="text-white/60 font-medium">{c.room_name}</span></p>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>

                  {/* Sessions History Card */}
                  <div className="bg-[#101010] border border-white/5 rounded-2xl p-6 space-y-4">
                    <h3 className="text-xs font-semibold uppercase text-white/40 tracking-wider flex items-center gap-1.5">
                      <Activity size={14} className="text-[#DEDBC8]" />
                      Conducted Lecture Sessions
                    </h3>

                    {sessionsLoading ? (
                      <div className="flex flex-col items-center justify-center py-12 gap-3">
                        <div className="w-8 h-8 rounded-full border-2 border-white/10 border-t-[#DEDBC8] animate-spin" />
                        <p className="text-[10px] text-white/30">Retrieving session history...</p>
                      </div>
                    ) : instructorSessions.length === 0 ? (
                      <div className="text-center py-12 border border-dashed border-white/5 rounded-xl">
                        <Video size={20} className="mx-auto mb-2 text-white/20" />
                        <p className="text-xs text-white/30">No sessions recorded yet for this instructor.</p>
                      </div>
                    ) : (
                      <div className="divide-y divide-white/5 border border-white/5 rounded-xl overflow-hidden bg-black/20">
                        {instructorSessions.map((s) => (
                          <Link
                            key={s.id}
                            href={`/session/${s.id}`}
                            className="p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-white/[0.02] transition-colors duration-150 group"
                          >
                            <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                <h4 className="text-sm font-semibold text-white group-hover:text-[#DEDBC8] transition-colors">{s.course_name}</h4>
                                <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${
                                  s.status === 'active' ? 'bg-green-500/15 text-green-400' :
                                  s.status === 'processing' ? 'bg-yellow-500/15 text-yellow-400' :
                                  'bg-white/10 text-white/40'
                                }`}>
                                  {s.status}
                                </span>
                              </div>
                              <div className="flex flex-wrap items-center gap-3 text-xs text-white/40">
                                <span className="flex items-center gap-1"><Calendar size={12} /> {s.start_date_time || 'N/A'}</span>
                                <span>·</span>
                                <span>Slot: {s.time_slot}</span>
                              </div>
                            </div>
                            
                            <div className="flex items-center gap-2 text-xs text-white/30 group-hover:text-white/60 transition-colors">
                              <span>View Reports</span>
                              <ChevronRight size={14} />
                            </div>
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      )}

    </div>
  );
}

// Simple Helper Icon component
function UserPlusIcon({ className }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth="2"
      stroke="currentColor"
      className={className}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M18 7.5v3m0 0v3m0-3h3m-3 0h-3m-2.25-4.125a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0ZM3 19.235v-.11a6.375 6.375 0 0 1 12.75 0v.109A12.318 12.318 0 0 1 9.374 21c-2.331 0-4.512-.645-6.374-1.766Z" />
    </svg>
  );
}
