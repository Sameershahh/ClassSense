'use client';

import { useEffect, useState } from 'react';
import { Plus, Trash2, Mail, ShieldAlert, UserPlus, Award } from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function InstructorsPage() {
  const [instructors, setInstructors] = useState([]);
  const [unis, setUnis] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Modals States
  const [inviteModal, setInviteModal] = useState({ open: false, email: '', password: '', full_name: '', university_id: '' });
  const [mappingModal, setMappingModal] = useState({ open: false, id: null, full_name: '', university_id: '' });

  async function fetchInstructorsData() {
    const token = localStorage.getItem('cs_token');
    const headers = { 'Authorization': `Bearer ${token}` };

    try {
      setLoading(true);
      const [instRes, uniRes] = await Promise.all([
        fetch(`${API}/api/admin/instructors`, { headers }),
        fetch(`${API}/api/admin/universities`, { headers }),
      ]);

      if (!instRes.ok || !uniRes.ok) {
        throw new Error('Failed to fetch instructor accounts or university directories.');
      }

      const instData = await instRes.json();
      const uniData = await uniRes.json();

      setInstructors(instData);
      setUnis(uniData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchInstructorsData();
  }, []);

  // ── INVITE INSTRUCTOR ACTION ──

  async function handleInviteSubmit(e) {
    e.preventDefault();
    const token = localStorage.getItem('cs_token');
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };

    const payload = {
      email: inviteModal.email,
      password: inviteModal.password,
      full_name: inviteModal.full_name,
      university_id: inviteModal.university_id ? parseInt(inviteModal.university_id) : null
    };

    try {
      const res = await fetch(`${API}/api/admin/instructors`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to onboard instructor account');
      }

      setInviteModal({ open: false, email: '', password: '', full_name: '', university_id: '' });
      fetchInstructorsData();
    } catch (err) {
      alert(err.message);
    }
  }

  // ── UPDATE MAPPING ACTION ──

  async function handleMappingSubmit(e) {
    e.preventDefault();
    const token = localStorage.getItem('cs_token');
    const headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };

    const payload = {
      full_name: mappingModal.full_name,
      university_id: mappingModal.university_id ? parseInt(mappingModal.university_id) : null
    };

    try {
      const res = await fetch(`${API}/api/admin/instructors/${mappingModal.id}`, {
        method: 'PUT',
        headers,
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error('Failed to update mapping details.');

      setMappingModal({ open: false, id: null, full_name: '', university_id: '' });
      fetchInstructorsData();
    } catch (err) {
      alert(err.message);
    }
  }

  // ── REVOKE ACCESS ACTION ──

  async function handleRevoke(id) {
    if (!confirm('Are you sure you want to revoke access for this instructor? They will no longer be able to log in.')) return;

    const token = localStorage.getItem('cs_token');
    const headers = { 'Authorization': `Bearer ${token}` };

    try {
      const res = await fetch(`${API}/api/admin/instructors/${id}`, {
        method: 'DELETE',
        headers
      });

      if (!res.ok) throw new Error('Failed to revoke access.');
      fetchInstructorsData();
    } catch (err) {
      alert(err.message);
    }
  }

  // Filter instructors based on search query
  const filteredInstructors = instructors.filter(inst => {
    const query = searchQuery.toLowerCase();
    return (
      (inst.full_name || '').toLowerCase().includes(query) ||
      (inst.email || '').toLowerCase().includes(query) ||
      (inst.university_name || '').toLowerCase().includes(query)
    );
  });

  if (loading) {
    return (
      <div className="h-[60vh] flex flex-col items-center justify-center gap-4">
        <div className="w-10 h-10 rounded-full border-2 border-white/10 border-t-[#DEDBC8] animate-spin" />
        <p className="text-xs text-white/40">Loading instructor directories...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* ── HEADER ── */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-medium tracking-tight text-white">Instructors & Access Control</h1>
          <p className="text-sm text-white/40 mt-1">Manage instructor accounts, assign them to universities, or revoke access.</p>
        </div>
        <button
          onClick={() => setInviteModal({ open: true, email: '', password: '', full_name: '', university_id: '' })}
          className="bg-white hover:bg-white/95 text-black font-semibold text-xs px-4 py-2.5 rounded-xl flex items-center gap-2 transition-colors cursor-pointer"
        >
          <UserPlus size={14} /> Onboard Instructor
        </button>
      </div>

      {error && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/20 px-4 py-3 text-xs text-red-400">
          {error}
        </div>
      )}

      {/* ── SEARCH & TABLE ── */}
      <div className="bg-[#101010] border border-white/5 rounded-2xl p-6 space-y-6">
        
        {/* Search Bar */}
        <div className="max-w-md">
          <input
            type="text"
            placeholder="Search instructors by name, email, or university..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-1 focus:ring-white/20 focus:outline-none text-sm animate-all"
          />
        </div>

        {/* Instructors List Table */}
        {filteredInstructors.length === 0 ? (
          <div className="text-center py-16 border border-dashed border-white/5 rounded-2xl">
            <p className="text-xs text-white/30">No instructor accounts match your query.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-white/5 text-[10px] text-white/40 uppercase tracking-wider font-semibold">
                  <th className="pb-3 pl-4">Full Name</th>
                  <th className="pb-3">Email Address</th>
                  <th className="pb-3">University Mapping</th>
                  <th className="pb-3">Onboarded Date</th>
                  <th className="pb-3 pr-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-sm">
                {filteredInstructors.map((inst) => (
                  <tr key={inst.id} className="hover:bg-white/5 transition-colors group">
                    <td className="py-4 pl-4 font-semibold text-white">{inst.full_name || 'ClassSense Instructor'}</td>
                    <td className="py-4 text-white/70">{inst.email}</td>
                    <td className="py-4">
                      <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium bg-[#DEDBC8]/10 text-[#DEDBC8]">
                        <Award size={10} />
                        {inst.university_name}
                      </span>
                    </td>
                    <td className="py-4 text-white/30 text-xs">
                      {new Date(inst.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}
                    </td>
                    <td className="py-4 pr-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => setMappingModal({ open: true, id: inst.id, full_name: inst.full_name || '', university_id: inst.university_id || '' })}
                          className="text-xs hover:bg-white/5 border border-white/5 text-white/60 hover:text-white px-3 py-1.5 rounded-lg transition-all"
                        >
                          Modify
                        </button>
                        <button
                          onClick={() => handleRevoke(inst.id)}
                          className="text-xs hover:bg-red-500/10 border border-transparent hover:border-red-500/20 text-white/40 hover:text-red-400 p-1.5 rounded-lg transition-all"
                          title="Revoke Instructor Access"
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </div>

      {/* ── ONBOARD/INVITE MODAL ── */}
      {inviteModal.open && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[9999]">
          <div className="bg-[#101010] border border-white/10 rounded-2xl w-full max-w-md p-6 space-y-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <Mail className="text-[#DEDBC8] size-5" /> Onboard Instructor Account
            </h2>

            <form onSubmit={handleInviteSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-white/60 mb-1.5 block">Instructor Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Dr. Sarah J."
                  value={inviteModal.full_name}
                  onChange={e => setInviteModal({ ...inviteModal, full_name: e.target.value })}
                  className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-white/60 mb-1.5 block">Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="instructor@university.edu"
                  value={inviteModal.email}
                  onChange={e => setInviteModal({ ...inviteModal, email: e.target.value })}
                  className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-white/60 mb-1.5 block">Secure Login Password</label>
                <input
                  type="password"
                  required
                  placeholder="At least 6 characters"
                  value={inviteModal.password}
                  onChange={e => setInviteModal({ ...inviteModal, password: e.target.value })}
                  className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white placeholder:text-white/20 focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-white/60 mb-1.5 block">University Assignment</label>
                <select
                  value={inviteModal.university_id}
                  onChange={e => setInviteModal({ ...inviteModal, university_id: e.target.value })}
                  className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                >
                  <option value="">Unassigned / No University</option>
                  {unis.map(uni => (
                    <option key={uni.id} value={uni.id}>{uni.name}</option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setInviteModal({ open: false, email: '', password: '', full_name: '', university_id: '' })}
                  className="h-10 px-4 border border-white/5 rounded-xl hover:bg-white/5 text-xs transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="h-10 px-5 bg-white text-black font-semibold rounded-xl text-xs hover:bg-white/90 transition-colors"
                >
                  Onboard Account
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── MODIFY MAPPING MODAL ── */}
      {mappingModal.open && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-[9999]">
          <div className="bg-[#101010] border border-white/10 rounded-2xl w-full max-w-md p-6 space-y-6">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <ShieldAlert className="text-[#DEDBC8] size-5" /> Modify Instructor Details
            </h2>

            <form onSubmit={handleMappingSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-medium text-white/60 mb-1.5 block">Full Name</label>
                <input
                  type="text"
                  required
                  value={mappingModal.full_name}
                  onChange={e => setMappingModal({ ...mappingModal, full_name: e.target.value })}
                  className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-white/60 mb-1.5 block">University Assignment</label>
                <select
                  value={mappingModal.university_id}
                  onChange={e => setMappingModal({ ...mappingModal, university_id: e.target.value })}
                  className="w-full bg-[#1A1A1A] border border-white/5 rounded-xl h-11 px-4 text-white focus:ring-1 focus:ring-white/20 focus:outline-none text-sm"
                >
                  <option value="">Unassigned / No University</option>
                  {unis.map(uni => (
                    <option key={uni.id} value={uni.id}>{uni.name}</option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setMappingModal({ open: false, id: null, full_name: '', university_id: '' })}
                  className="h-10 px-4 border border-white/5 rounded-xl hover:bg-white/5 text-xs transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="h-10 px-5 bg-white text-black font-semibold rounded-xl text-xs hover:bg-white/90 transition-colors"
                >
                  Save Modifications
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
