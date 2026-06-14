'use client';

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { motion } from 'framer-motion';

const TransitionContext = createContext({
  startTransition: (href, navigateCallback) => {},
});

export function useTransition() {
  return useContext(TransitionContext);
}

export function TransitionProvider({ children }) {
  const router = useRouter();
  const pathname = usePathname();
  const [status, setStatus] = useState('idle'); // 'idle' | 'exiting' | 'entering'

  // Trigger exit animation, then perform navigation
  const startTransition = useCallback((href, navigateCallback) => {
    setStatus('exiting');
    
    const timer = setTimeout(() => {
      if (navigateCallback) {
        navigateCallback();
      } else {
        router.push(href);
      }
    }, 500); // 500ms matches the animation duration

    return () => clearTimeout(timer);
  }, [router]);

  // When pathname changes, start the entry (fade-in from black) animation
  useEffect(() => {
    setStatus('entering');
    
    const timer = setTimeout(() => {
      setStatus('idle');
    }, 500); // 500ms matches the animation duration

    return () => clearTimeout(timer);
  }, [pathname]);

  // Intercept all internal Link / anchor clicks globally
  useEffect(() => {
    const handleGlobalClick = (e) => {
      const target = e.target.closest('a');
      if (!target) return;

      const href = target.getAttribute('href');
      if (!href) return;

      // Check if it's an internal relative link
      const isInternal =
        href.startsWith('/') &&
        !href.startsWith('//') &&
        !target.getAttribute('target') &&
        !target.getAttribute('download') &&
        !e.metaKey &&
        !e.ctrlKey &&
        !e.shiftKey &&
        !e.altKey;

      if (isInternal) {
        // If it's a hash link on the same page, do not intercept
        try {
          const currentPath = window.location.pathname;
          const url = new URL(href, window.location.origin);
          if (url.pathname === currentPath && url.hash) {
            return;
          }
        } catch (err) {
          // Fallback if URL parsing fails
        }

        e.preventDefault();
        startTransition(href);
      }
    };

    document.addEventListener('click', handleGlobalClick, { capture: true });
    return () => {
      document.removeEventListener('click', handleGlobalClick, { capture: true });
    };
  }, [startTransition]);

  return (
    <TransitionContext.Provider value={{ startTransition }}>
      {children}

      {/* ── PREMIUM FADE-TO-BLACK/FROM-BLACK TRANSITION OVERLAY ── */}
      {status !== 'idle' && (
        <motion.div
          initial={{ opacity: status === 'exiting' ? 0 : 1 }}
          animate={{ opacity: status === 'exiting' ? 1 : 0 }}
          transition={{ duration: 0.5, ease: [0.4, 0, 0.2, 1] }}
          className="fixed inset-0 bg-black z-[99999] pointer-events-none"
        />
      )}
    </TransitionContext.Provider>
  );
}

// Custom hook to replace useRouter inside client components
export function useTransitionRouter() {
  const router = useRouter();
  const { startTransition } = useTransition();

  return {
    ...router,
    push: useCallback((href, options) => {
      startTransition(href, () => router.push(href, options));
    }, [router, startTransition]),
    replace: useCallback((href, options) => {
      startTransition(href, () => router.replace(href, options));
    }, [router, startTransition]),
  };
}
