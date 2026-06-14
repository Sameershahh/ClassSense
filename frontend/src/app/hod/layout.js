'use client';

import { usePathname } from 'next/navigation';
import { useTransitionRouter } from '../context/TransitionContext';
import { LayoutDashboard, LogOut } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';

const HOD_NAV = [
  { label: 'Courses & Instructors', href: '/hod/dashboard', icon: LayoutDashboard },
];

export default function HodLayout({ children }) {
  const router = useTransitionRouter();
  const pathname = usePathname();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Basic authentication guard
    const token = localStorage.getItem('cs_token');
    if (!token) {
      router.push('/');
      return;
    }
    setLoading(false);
  }, [router]);

  function handleLogout() {
    localStorage.removeItem('cs_token');
    router.push('/');
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="w-12 h-12 rounded-full border-2 border-white/10 border-t-[#DEDBC8] animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black flex text-[#E1E0CC]">
      {/* ── HOD SIDEBAR ── */}
      <aside className="w-64 border-r border-white/5 bg-[#101010] flex flex-col h-screen sticky top-0">
        {/* Logo */}
        <div className="px-5 py-6 border-b border-white/5">
          <span className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#DEDBC8]"></span>
            ClassSense
          </span>
          <span className="text-[10px] text-white/30 uppercase tracking-widest font-semibold block mt-1">HOD Portal</span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-6 space-y-1">
          {HOD_NAV.map(({ label, href, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={label}
                href={href}
                className={`flex items-center gap-3 px-4 py-3 text-sm rounded-xl transition-all duration-200 ${
                  active
                    ? 'bg-white/10 text-white font-medium border-l-2 border-[#DEDBC8]'
                    : 'text-white/40 hover:text-white hover:bg-white/5 font-normal'
                }`}
              >
                <Icon size={16} />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Footer/Logout */}
        <div className="p-4 border-t border-white/5">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 text-sm text-white/40 hover:text-white hover:bg-white/5 rounded-xl transition-colors"
          >
            <LogOut size={16} />
            Log out
          </button>
        </div>
      </aside>

      {/* ── MAIN CONTENT AREA ── */}
      <main className="flex-1 p-8 overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
