'use client';

import { useEffect, useState } from 'react';
import { Plus, Edit2, Trash2, Camera, MapPin, Video, Network } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function UniversitiesPage() {
  const [unis, setUnis] = useState([]);
  const [classrooms, setClassrooms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Selected University for Classroom filtering
  const [selectedUniId, setSelectedUniId] = useState(null);

  // Modals / Forms States
  const [uniModal, setUniModal] = useState({ open: false, mode: 'create', id: null, name: '', address: '' });
  const [classroomModal, setClassroomModal] = useState({ open: false, mode: 'create', id: null, name: '', university_id: '', rtsp_url: '', camera_status: 'offline' });

  async function fetchData() {
    const token = localStorage.getItem('cs_token');
    const headers = { 'Authorization': `Bearer ${token}` };

    try {
      setLoading(true);
      const [uniRes, classroomRes] = await Promise.all([
        fetch(`${API}/api/admin/universities`, { headers }),
        fetch(`${API}/api/admin/classrooms`, { headers }),
      ]);

      if (!uniRes.ok || !classroomRes.ok) {
        throw new Error('Failed to load institution infrastructure data.');
      }

      const uniData = await uniRes.json();
      const classroomData = await classroomRes.json();

      setUnis(uniData);
      setClassrooms(classroomData);

      if (uniData.length > 0 && !selectedUniId) {
        setSelectedUniId(uniData[0].id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchData();
  }, []);

  // ── UNIVERSITY CRUD ACTIONS ──

  async function handleUniSubmit(e) {
    e.preventDefault();
    const token = localStorage.getItem('cs_token');
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };

    const url = uniModal.mode === 'create'
      ? `${API}/api/admin/universities`
      : `${API}/api/admin/universities/${uniModal.id}`;

    const method = uniModal.mode === 'create' ? 'POST' : 'PUT';

    try {
      const res = await fetch(url, {
        method,
        headers,
        body: JSON.stringify({ name: uniModal.name, address: uniModal.address })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to save university');
      }

      setUniModal({ open: false, mode: 'create', id: null, name: '', address: '' });
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  }

  async function handleUniDelete(id) {
    if (!confirm('Are you sure you want to offboard this university? All classrooms inside it will also be deleted!')) return;

    const token = localStorage.getItem('cs_token');
    const headers = { 'Authorization': `Bearer ${token}` };

    try {
      const res = await fetch(`${API}/api/admin/universities/${id}`, {
        method: 'DELETE',
        headers
      });

      if (!res.ok) throw new Error('Failed to delete university');
      
      if (selectedUniId === id) {
        setSelectedUniId(null);
      }
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  }

  // ── CLASSROOM CRUD ACTIONS ──

  async function handleClassroomSubmit(e) {
    e.preventDefault();
    const token = localStorage.getItem('cs_token');
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };

    const url = classroomModal.mode === 'create'
      ? `${API}/api/admin/classrooms`
      : `${API}/api/admin/classrooms/${classroomModal.id}`;

    const method = classroomModal.mode === 'create' ? 'POST' : 'PUT';

    // Body changes between CREATE and UPDATE:
    // Create takes university_id; Update does not
    const bodyObj = classroomModal.mode === 'create'
      ? {
          name: classroomModal.name,
          university_id: parseInt(classroomModal.university_id),
          rtsp_url: classroomModal.rtsp_url,
          camera_status: classroomModal.camera_status
        }
      : {
          name: classroomModal.name,
          rtsp_url: classroomModal.rtsp_url,
          camera_status: classroomModal.camera_status
        };

    try {
      const res = await fetch(url, {
        method,
        headers,
        body: JSON.stringify(bodyObj)
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to save classroom');
      }

      setClassroomModal({ open: false, mode: 'create', id: null, name: '', university_id: '', rtsp_url: '', camera_status: 'offline' });
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  }

  async function handleClassroomDelete(id) {
    if (!confirm('Are you sure you want to remove this classroom?')) return;

    const token = localStorage.getItem('cs_token');
    const headers = { 'Authorization': `Bearer ${token}` };

    try {
      const res = await fetch(`${API}/api/admin/classrooms/${id}`, {
        method: 'DELETE',
        headers
      });

      if (!res.ok) throw new Error('Failed to delete classroom');
      fetchData();
    } catch (err) {
      alert(err.message);
    }
  }

  const activeUni = unis.find(u => u.id === selectedUniId);
  const filteredClassrooms = classrooms.filter(c => c.university_id === selectedUniId);

  if (loading) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center gap-4">
        <div className="w-10 h-10 rounded-full border-2 border-white/10 border-t-[#DEDBC8] animate-spin" />
        <p className="text-xs text-white/40">Loading infrastructure details...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* ── HEADER ── */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-medium tracking-tight text-white">Institutions & Classrooms</h1>
          <p className="text-sm text-white/40 mt-1">Onboard universities, add classrooms, and configure RTSP IP camera streams.</p>
        </div>
        <button
          onClick={() => setUniModal({ open: true, mode: 'create', id: null, name: '', address: '' })}
          className="bg-white hover:bg-white/95 text-black font-semibold text-xs px-4 py-2.5 rounded-xl flex items-center gap-2 transition-colors cursor-pointer"
        >
          <Plus size={14} /> Onboard University
        </button>
      </div>

      {error && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-xs text-red-400">
          {error}
        </div>
      )}

      {/* ── MAIN CONTENT GRID ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: Universities List */}
        <div className="lg:col-span-5 bg-[#101010] border border-white/5 rounded-2xl p-5 space-y-4">
          <h2 className="text-sm font-semibold tracking-wider uppercase text-white/30 px-1">Universities</h2>
          
          {unis.length === 0 ? (
            <div className="text-center py-12 border border-dashed border-white/5 rounded-xl">
              <p className="text-xs text-white/30">No universities onboarded yet.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {unis.map((uni) => {
                const isSelected = uni.id === selectedUniId;
                return (
                  <div
                    key={uni.id}
                    onClick={() => setSelectedUniId(uni.id)}
                    className={`group w-full text-left p-4 rounded-xl border transition-all duration-200 cursor-pointer flex items-center justify-between ${
                      isSelected
                        ? 'bg-[#1A1A1A] border-[#DEDBC8] text-white'
                        : 'bg-[#1A1A1A]/40 border-white/5 text-white/60 hover:border-white/10 hover:text-white'
                    }`}
                  >
                    <div className="space-y-1 pr-4 min-w-0">
                      <p className="font-semibold text-sm truncate">{uni.name}</p>
                      <p className="text-xs text-white/30 truncate flex items-center gap-1">
                        <MapPin size={10} /> {uni.address || 'No address specified'}
                      </p>
                    </div>

                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setUniModal({ open: true, mode: 'edit', id: uni.id, name: uni.name, address: uni.address || '' });
                        }}
                        className="p-1.5 hover:bg-white/10 rounded-lg text-white/40 hover:text-white transition-colors"
                      >
                        <Edit2 size={12} />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleUniDelete(uni.id);
                        }}
                        className="p-1.5 hover:bg-red-500/10 rounded-lg text-white/40 hover:text-red-400 transition-colors"
                      >
                        <Trash2 size={12} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Selected University's Classrooms */}
        <div className="lg:col-span-7 bg-[#101010] border border-white/5 rounded-2xl p-5 space-y-6">
          
          <div className="flex justify-between items-center border-b border-white/5 pb-4">
            <div>
              <h2 className="font-semibold text-white text-base">
                {activeUni ? activeUni.name : 'Select a University'}
              </h2>
              <p className="text-xs text-white/30">Classrooms and IP camera configurations</p>
            </div>
            {activeUni && (
              <button
                onClick={() => setClassroomModal({ open: true, mode: 'create', id: null, name: '', university_id: activeUni.id, rtsp_url: '', camera_status: 'offline' })}
                className="bg-[#1A1A1A] hover:bg-[#242424] text-white border border-white/10 text-xs px-3.5 py-2 rounded-xl flex items-center gap-1.5 transition-colors cursor-pointer"
              >
                <Plus size={12} /> Add Classroom
              </button>
            )}
          </div>

          {!activeUni ? (
            <div className="text-center py-20">
              <p className="text-xs text-white/30">Please select or onboard a university to view classrooms.</p>
            </div>
          ) : filteredClassrooms.length === 0 ? (
            <div className="text-center py-16 border border-dashed border-white/5 rounded-xl">
              <p className="text-xs text-white/30">No classrooms configured for this university.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredClassrooms.map((cr) => (
                <div key={cr.id} className="bg-[#1A1A1A] border border-white/5 rounded-xl p-5 space-y-4 hover:border-white/10 transition-colors relative group">
                  
                  {/* Title & Status */}
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-semibold text-white text-sm">{cr.name}</h3>
                      <span className="text-[10px] text-white/30">ID: {cr.id}</span>
                    </div>
                    <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-semibold flex items-center gap-1 ${
                      cr.camera_status === 'online'
                        ? 'bg-green-500/10 text-green-400'
                        : 'bg-white/5 text-white/40'
                    }`}>
                      <span className={`w-1 h-1 rounded-full ${cr.camera_status === 'online' ? 'bg-green-400 animate-pulse' : 'bg-white/30'}`} />
                      {cr.camera_status}
                    </span>
                  </div>

                  {/* RTSP Stream URL info */}
                  <div className="space-y-1">
                    <span className="text-[10px] text-white/40 uppercase font-medium tracking-wider flex items-center gap-1">
                      <Network size={10} /> RTSP Stream Configuration
                    </span>
                    <p className="text-xs font-mono text-white/70 bg-black/40 rounded px-2.5 py-1.5 break-all truncate">
                      {cr.rtsp_url || 'No stream configured'}
                    </p>
                  </div>

                  {/* Edit/Delete Controls */}
                  <div className="flex items-center gap-2 justify-end pt-2 border-t border-white/5">
                    <button
                      onClick={() => setClassroomModal({
                        open: true,
                        mode: 'edit',
                        id: cr.id,
                        name: cr.name,
                        university_id: cr.university_id,
                        rtsp_url: cr.rtsp_url || '',
                        camera_status: cr.camera_status
                      })}
                      className="text-xs text-white/40 hover:text-white flex items-center gap-1 hover:bg-white/5 px-2.5 py-1 rounded-lg transition-colors"
                    >
                      <Edit2 size={10} /> Edit
                    </button>
                    <button
                      onClick={() => handleClassroomDelete(cr.id)}
                      className="text-xs text-white/40 hover:text-red-400 flex items-center gap-1 hover:bg-red-500/5 px-2.5 py-1 rounded-lg transition-colors"
                    >
                      <Trash2 size={10} /> Delete
                    </button>
                  </div>

                </div>
              ))}
            </div>
          )}

        </div>

      </div>

      {/* ── UNIVERSITY MODAL ── */}
      {uniModal.open && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[9999]">
          <div className="bg-[#101010] border border-white/10 rounded-2xl w-full max-w-md p-6 space-y-6">
            <h2 className="text-lg font-semibold text-white">
              {uniModal.mode === 'create' ? 'Onboard New University' : 'Edit University Details'}
            </h2>

            <form onSubmit={handleUniSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-white/60 mb-1.5 block">University Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Iqra University"
                  value={uniModal.name}
                  onChange={e => setUniModal({ ...uniModal, name: e.target.value })}
                  className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-white/60 mb-1.5 block">Address / Campus</label>
                <input
                  type="text"
                  placeholder="e.g. Main Campus, Karachi"
                  value={uniModal.address}
                  onChange={e => setUniModal({ ...uniModal, address: e.target.value })}
                  className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setUniModal({ open: false, mode: 'create', id: null, name: '', address: '' })}
                  className="h-10 px-4 border border-white/5 rounded-xl hover:bg-white/5 text-xs transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="h-10 px-5 bg-white text-black font-semibold rounded-xl text-xs hover:bg-white/90 transition-colors"
                >
                  {uniModal.mode === 'create' ? 'Onboard' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── CLASSROOM MODAL ── */}
      {classroomModal.open && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[9999]">
          <div className="bg-[#101010] border border-white/10 rounded-2xl w-full max-w-md p-6 space-y-6">
            <h2 className="text-lg font-semibold text-white">
              {classroomModal.mode === 'create' ? 'Add Classroom' : 'Edit Classroom Stream'}
            </h2>

            <form onSubmit={handleClassroomSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-white/60 mb-1.5 block">Classroom Name / Room Number</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. CS Lab 2 / Room 301"
                  value={classroomModal.name}
                  onChange={e => setClassroomModal({ ...classroomModal, name: e.target.value })}
                  className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-white/60 mb-1.5 block">RTSP Camera Stream URL</label>
                <input
                  type="text"
                  placeholder="rtsp://username:password@ip_address:port/path"
                  value={classroomModal.rtsp_url}
                  onChange={e => setClassroomModal({ ...classroomModal, rtsp_url: e.target.value })}
                  className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-white/60 mb-1.5 block">Camera Status</label>
                <select
                  value={classroomModal.camera_status}
                  onChange={e => setClassroomModal({ ...classroomModal, camera_status: e.target.value })}
                  className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                >
                  <option value="offline">offline</option>
                  <option value="online">online</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setClassroomModal({ open: false, mode: 'create', id: null, name: '', university_id: '', rtsp_url: '', camera_status: 'offline' })}
                  className="h-10 px-4 border border-white/5 rounded-xl hover:bg-white/5 text-xs transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="h-10 px-5 bg-white text-black font-semibold rounded-xl text-xs hover:bg-white/90 transition-colors"
                >
                  {classroomModal.mode === 'create' ? 'Add Room' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
