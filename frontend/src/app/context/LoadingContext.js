'use client';

import { createContext, useContext, useRef, useState, useCallback, useEffect } from 'react';
import axios from 'axios';

const LoadingContext = createContext({
  isGlobalLoading: false,
  startLoading: () => {},
  stopLoading: () => {},
});

export function useGlobalLoading() {
  return useContext(LoadingContext);
}

export function LoadingProvider({ children }) {
  const [isGlobalLoading, setIsGlobalLoading] = useState(false);
  const activeRequests = useRef(0);

  const startLoading = useCallback(() => {
    activeRequests.current += 1;
    setIsGlobalLoading(true);
  }, []);

  const stopLoading = useCallback(() => {
    activeRequests.current = Math.max(0, activeRequests.current - 1);
    if (activeRequests.current === 0) setIsGlobalLoading(false);
  }, []);

  // Global Axios Interceptors setup inside standard useEffect
  useEffect(() => {
    const reqId = axios.interceptors.request.use(
      (config) => { 
        startLoading(); 
        return config; 
      },
      (error) => { 
        stopLoading(); 
        return Promise.reject(error); 
      }
    );

    const resId = axios.interceptors.response.use(
      (response) => { 
        stopLoading(); 
        return response; 
      },
      (error) => { 
        stopLoading(); 
        return Promise.reject(error); 
      }
    );

    return () => {
      axios.interceptors.request.eject(reqId);
      axios.interceptors.response.eject(resId);
    };
  }, [startLoading, stopLoading]);

  return (
    <LoadingContext.Provider value={{ isGlobalLoading, startLoading, stopLoading }}>
      {children}
      
      {/* ── AESTHETIC GLOBAL "C" LOADER OVERLAY ── */}
      {isGlobalLoading && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[9999] pointer-events-auto">
          <div className="relative flex items-center justify-center w-20 h-20 bg-[#101010] border border-white/5 rounded-2xl shadow-2xl">
            <div className="absolute w-12 h-12 rounded-full border-2 border-white/10 border-t-[#DEDBC8] animate-spin" />
            <span className="text-xl font-bold tracking-tight text-[#E1E0CC] select-none">C</span>
          </div>
        </div>
      )}
    </LoadingContext.Provider>
  );
}