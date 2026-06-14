'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useTransitionRouter } from '../context/TransitionContext';
import {
  LayoutDashboard, Video, Clock, TrendingUp, Settings, LogOut, BookOpen
} from 'lucide-react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Sidebar() {
  const router   = useTransitionRouter();
  const pathname = usePathname();

  const [role, setRole] = useState('instructor');
  const [email, setEmail] = useState('instructor@classsense.com');
  const [name, setName] = useState('Instructor');

  useEffect(() => {
    async function loadProfile() {
      const storedRole = localStorage.getItem('cs_role');
      if (storedRole) {
        setRole(storedRole);
      }
      const token = localStorage.getItem('cs_token');
      if (token) {
        try {
          const res = await fetch(`${API}/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (res.ok) {
            const data = await res.json();
            setRole(data.role);
            setEmail(data.username);
            setName(data.full_name || (data.role === 'hod' ? 'HOD' : 'Instructor'));
            localStorage.setItem('cs_role', data.role);
          }
        } catch (e) {
          console.error(e);
        }
      }
    }
    loadProfile();
  }, []);

  function logout() {
    localStorage.removeItem('cs_token');
    localStorage.removeItem('cs_role');
    router.push('/');
  }

  const navItems = role === 'hod'
    ? [ { label: 'Dashboard', href: '/hod/dashboard', icon: LayoutDashboard } ]
    : [
        { label: 'Dashboard',  href: '/dashboard', icon: LayoutDashboard },
        { label: 'Courses',    href: '/dashboard/courses', icon: BookOpen },
        { label: 'Sessions',   href: '/session', icon: Video },
      ];

  return (
    <aside className="hidden lg:flex w-64 h-screen sticky top-0 flex-col bg-[#1A1A1A] border-r border-white/5">

      {/* Logo */}
      <div className="px-5 pt-6 pb-5 border-b border-white/5">
        <span className="text-xl font-semibold tracking-tight text-white">ClassSense</span>
        <p className="text-xs text-white/30 mt-0.5">{role === 'hod' ? 'HOD Portal' : 'Analytics Portal'}</p>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map(({ label, href, icon: Icon }) => {
          const active = pathname === href || (href !== '/dashboard' && href !== '/hod/dashboard' && pathname.startsWith(href));
          
          return (
            <Link
              key={label}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 text-sm rounded-xl transition-colors duration-150 ${
                active
                  ? 'bg-white/10 text-white font-medium'
                  : 'text-white/40 hover:text-white hover:bg-white/5 font-normal'
              }`}
            >
              <Icon size={16} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* User + Logout */}
      <div className="px-3 pb-4 border-t border-white/5 pt-4 space-y-2">
        <div className="flex items-center gap-3 px-3 py-2">
          <div className="w-8 h-8 rounded-full bg-[#242424] flex items-center justify-center text-xs font-medium text-white/60 flex-shrink-0">
            {name.charAt(0)}
          </div>
          <div className="min-w-0">
            <p className="text-sm font-medium text-white truncate">{name}</p>
            <p className="text-xs text-white/30 truncate">{email}</p>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2.5 text-sm rounded-xl text-white/40 hover:text-white hover:bg-white/5 transition-colors duration-150"
        >
          <LogOut size={16} />
          Log out
        </button>
      </div>
    </aside>
  );
}
