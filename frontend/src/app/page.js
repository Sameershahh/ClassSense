'use client';

import { useRef } from 'react';
import Link from 'next/link';
import { motion, useInView } from 'framer-motion';
import { ArrowRight, Check } from 'lucide-react';

// ── SHARED ANIMATION COMPONENTS ──

// WordsPullUp
export function WordsPullUp({ text, className = '', showAsterisk = false }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });
  const words = text.split(' ');

  const containerVariants = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: 0.08,
      },
    },
  };

  const wordVariants = {
    hidden: { y: 40, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.8,
        ease: [0.16, 1, 0.3, 1],
      },
    },
  };

  return (
    <motion.span
      ref={ref}
      variants={containerVariants}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      className={`inline-flex flex-wrap justify-center md:justify-start ${className}`}
    >
      {words.map((word, idx) => {
        const isLast = idx === words.length - 1;
        const needsAsterisk = showAsterisk && isLast && (word.endsWith('a') || word.endsWith('e'));
        const lastChar = word.slice(-1);
        
        return (
          <span key={idx} className="relative inline-block mr-[0.25em] overflow-hidden py-1">
            <motion.span variants={wordVariants} className="inline-block">
              {needsAsterisk ? word.slice(0, -1) : word}
              {needsAsterisk && (
                <span className="relative inline-block">
                  {lastChar}
                  <span className="absolute top-[-0.3em] left-[100%] text-[0.45em] font-light font-sans tracking-normal select-none">
                    *
                  </span>
                </span>
              )}
            </motion.span>
          </span>
        );
      })}
    </motion.span>
  );
}

// WordsPullUpMultiStyle
export function WordsPullUpMultiStyle({ segments, className = '' }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  const containerVariants = {
    hidden: {},
    visible: {
      transition: {
        staggerChildren: 0.08,
      },
    },
  };

  const wordVariants = {
    hidden: { y: 30, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.8,
        ease: [0.16, 1, 0.3, 1],
      },
    },
  };

  // Flatten segments into list of words with corresponding styles
  const allWords = [];
  segments.forEach((seg, sIdx) => {
    const words = seg.text.split(' ');
    words.forEach((word, wIdx) => {
      if (word.trim() !== '') {
        allWords.push({
          text: word,
          className: seg.className,
          isLastInSegment: wIdx === words.length - 1,
        });
      }
    });
  });

  return (
    <motion.span
      ref={ref}
      variants={containerVariants}
      initial="hidden"
      animate={isInView ? 'visible' : 'hidden'}
      className={`inline-flex flex-wrap justify-center gap-x-[0.25em] ${className}`}
    >
      {allWords.map((wordObj, idx) => (
        <span key={idx} className="inline-block overflow-hidden py-1">
          <motion.span
            variants={wordVariants}
            className={`inline-block ${wordObj.className}`}
          >
            {wordObj.text}
          </motion.span>
        </span>
      ))}
    </motion.span>
  );
}

// About section feature data
const aboutFeatures = [
  {
    image: '/assets/about-image-1.jpg',
    heading: 'Real-Time Engagement Analysis',
    description: 'ClassSense continuously monitors student body language, facial cues, and micro-expressions using computer vision to provide live engagement scores enabling teachers to adapt their delivery instantly.',
  },
  {
    image: '/assets/about-image-2.jpg',
    heading: 'Attention Heatmaps',
    description: 'Visualize which parts of the lesson captivated students the most. Color-coded heatmaps overlay onto your classroom layout, revealing attention peaks and drop-off zones across every session.',
  },
  {
    image: '/assets/about-image-3.jpg',
    heading: 'Session Insights & Reports',
    description: 'After every class, receive a structured insights report complete with engagement trends, participation metrics for enhancing your next session.',
  },
  {
    image: '/assets/about-image-4.jpg',
    heading: 'Student Progress Tracking',
    description: 'Track individual and group engagement over time. Identify students who may be disengaging early and intervene proactively before their performance is affected.',
  },
  {
    image: '/assets/about-image-5.jpg',
    heading: 'Privacy-First Architecture',
    description: 'All visual processing is handled on-device with strict anonymization protocols. No raw footage is stored or transmitted. ClassSense is built on a foundation of student privacy and institutional trust.',
  },
];

// ── MAIN LANDING PAGE ──

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-black text-[#E1E0CC] selection:bg-[#E1E0CC]/30 selection:text-white overflow-x-hidden">
      
      {/* ── SECTION 1: HERO ── */}
      <section className="h-screen w-full p-4 md:p-6 relative">
        <div className="w-full h-full rounded-2xl md:rounded-[2rem] overflow-hidden relative bg-black">
          
          {/* Background Static Image */}
          <div 
            className="absolute inset-0 w-full h-full bg-cover bg-center z-0" 
            style={{ backgroundImage: 'url("/assets/hero-image.jpg")' }}
          />
          
          {/* Custom Noise overlay on top */}
          <div className="absolute inset-0 noise-overlay opacity-[0.7] mix-blend-overlay pointer-events-none z-10" />
          
          {/* Dark Gradient Overlay */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-black/40 to-black/90 z-10" />

          {/* Floating Pill Navbar */}
          <nav className="absolute top-0 left-1/2 -translate-x-1/2 z-30 pt-4 w-auto max-w-full px-4">
            <div className="bg-[#1A1A1A]/40 backdrop-blur-md rounded-full border border-white/5 shadow-2xl px-6 py-3 flex items-center justify-between gap-6 sm:gap-12 md:gap-14">
              <span className="text-[10px] sm:text-xs md:text-sm font-bold tracking-widest text-[#E1E0CC]/40 select-none uppercase">ClassSense</span>
              <div className="flex items-center gap-3 sm:gap-6 md:gap-8 lg:gap-10">
                <a href="#about" className="text-[10px] sm:text-xs md:text-sm font-medium tracking-tight hover:text-[#E1E0CC] transition-colors" style={{ color: 'rgba(225, 224, 204, 0.8)' }}>Features</a>
                <a href="#features" className="text-[10px] sm:text-xs md:text-sm font-medium tracking-tight hover:text-[#E1E0CC] transition-colors" style={{ color: 'rgba(225, 224, 204, 0.8)' }}>How it works</a>
                <a href="#contact" className="text-[10px] sm:text-xs md:text-sm font-medium tracking-tight hover:text-[#E1E0CC] transition-colors" style={{ color: 'rgba(225, 224, 204, 0.8)' }}>Contact</a>
                <Link href="/login" className="text-[10px] sm:text-xs md:text-sm font-semibold tracking-tight bg-[#DEDBC8] text-black px-4 py-1.5 rounded-full hover:bg-[#E1E0CC] transition-colors">Login</Link>
              </div>
            </div>
          </nav>

          {/* Hero Content (bottom-aligned) */}
          <div className="absolute bottom-0 left-0 right-0 p-8 md:p-12 z-20">
            <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8 items-end text-left">
              
              {/* Giant Heading */}
              <div className="lg:col-span-7 select-none text-left">
                <h1 className="relative font-medium tracking-tight leading-none text-[#E1E0CC]">
                  <WordsPullUp 
                    text="ClassSense" 
                    showAsterisk={true}
                    className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl xl:text-9xl text-left"
                  />
                </h1>
              </div>

              {/* Description + CTA Button */}
              <div className="lg:col-span-5 space-y-6 text-left">
                <motion.p
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                  className="text-[#DEDBC8]/70 text-xs sm:text-sm md:text-base leading-snug text-left"
                >
                  ClassSense leverages advanced computer vision to analyze student engagement in real-time, bridging the gap between traditional education and intelligent insights to unlock the true potential of modern classrooms.
                </motion.p>

                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7, duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                  className="text-left"
                >
                  <Link 
                    href="/"  
                    className="group inline-flex items-center gap-2.5 bg-[#DEDBC8] hover:gap-3 text-black font-semibold text-sm sm:text-base pl-6 pr-2 py-2 rounded-full transition-all duration-300"
                  >
                    Request Demo
                    <span className="bg-black text-white rounded-full w-9 h-9 sm:w-10 sm:h-10 flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                      <ArrowRight className="size-4" />
                    </span>
                  </Link>
                </motion.div>
              </div>

            </div>
          </div>

        </div>
      </section>

      {/* ── SECTION 2: ABOUT ── */}
      <section id="about" className="bg-black py-24 px-4 md:px-8">
        <div className="w-full max-w-6xl mx-auto space-y-12">

          {/* Section Header */}
          <div className="text-center space-y-4">
            <span className="text-[#DEDBC8] text-[10px] sm:text-xs font-semibold uppercase tracking-widest block">
              Core Modules &amp; Features
            </span>
            <h2 className="text-3xl sm:text-4xl md:text-5xl max-w-3xl mx-auto leading-tight text-white">
              <WordsPullUpMultiStyle
                segments={[
                  { text: "Everything you need to ", className: "font-normal text-[#E1E0CC]" },
                  { text: "understand your classroom.", className: "font-serif italic font-light text-[#DEDBC8]" },
                ]}
              />
            </h2>
          </div>

          {/* 5-Card Feature Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {aboutFeatures.map((feature, index) => (
              <AboutFeatureCard key={index} feature={feature} index={index} />
            ))}
          </div>

        </div>
      </section>

      {/* ── SECTION 3: SYSTEM WORKFLOW ── */}
      <section id="features" className="bg-black relative py-24 px-4 md:px-8 space-y-16">
        
        {/* Subtle background noise overlay */}
        <div className="absolute inset-0 bg-noise opacity-[0.15] pointer-events-none z-0" />

        {/* Section Header */}
        <div className="max-w-6xl mx-auto text-center space-y-3 relative z-10">
          <span className="text-[#DEDBC8] text-[10px] sm:text-xs font-semibold uppercase tracking-widest block">
            System Workflow
          </span>
          <h2>
            <WordsPullUpMultiStyle
              segments={[
                { text: "How ClassSense Works. ", className: "text-[#E1E0CC] font-normal" },
                { text: "Step-by-step intelligent classroom monitoring.", className: "text-gray-500 font-normal" },
              ]}
              className="text-xl sm:text-2xl md:text-3xl lg:text-4xl"
            />
          </h2>
        </div>

        {/* Workflow Cards Grid (4 columns) */}
        <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 relative z-10">
          
          
          {/* Step 01 — Instructor Authentication */}
          <FeatureCard index={0}>
             <div className="h-full bg-[#212121] border border-white/5 rounded-2xl md:rounded-[1.5rem] p-6 flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                {/* Step badge */}
                <div className="inline-flex items-center gap-2">
                  <span className="w-7 h-7 rounded-lg bg-[#DEDBC8]/10 border border-[#DEDBC8]/15 flex items-center justify-center text-[10px] font-mono font-semibold text-[#DEDBC8]">01</span>
                  <span className="text-[10px] uppercase tracking-widest text-gray-500 font-semibold">Step 01</span>
                </div>
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-gray-600 font-semibold mb-1">Instructor Authentication</p>
                  <h3 className="text-base sm:text-lg font-bold text-[#E1E0CC] leading-snug">Instructor Portal Access.</h3>
                </div>
                <div className="space-y-2.5 pt-1">
                  {[
                    'Secure portal session routing',
                    'Instructor authentication',
                    'Classroom profile configuration',
                    'Immediate dashboard pairing',
                  ].map((f) => (
                    <div key={f} className="flex items-start gap-2.5 text-xs">
                      <Check className="text-[#DEDBC8] size-4 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-400">{f}</span>
                    </div>
                  ))}
                </div>
              </div>
              <Link href="/login" className="inline-flex items-center gap-1.5 text-xs text-[#DEDBC8] hover:opacity-80 font-medium transition-opacity">
                Learn more <ArrowRight className="size-3.5 -rotate-45" />
              </Link>
            </div>
          </FeatureCard>


          {/* Card 2 - Project Storyboard */}
          <FeatureCard index={1}>
            <div className="h-full bg-[#212121] border border-white/5 rounded-2xl md:rounded-[1.5rem] p-6 flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                <div className="inline-flex items-center gap-2">
                  <span className="w-7 h-7 rounded-lg bg-[#DEDBC8]/10 border border-[#DEDBC8]/15 flex items-center justify-center text-[10px] font-mono font-semibold text-[#DEDBC8]">02</span>
                  <span className="text-[10px] uppercase tracking-widest text-gray-500 font-semibold">Step 02</span>
                </div>
                
                <div>
                  <p className="text-[10px] uppercase tracking-widest text-gray-600 font-semibold mb-1">Real-Time Capture</p>
                  <h3 className="text-base sm:text-lg font-bold text-[#E1E0CC] leading-snug">Session Initialization.</h3>
                </div>
                <div className="space-y-2.5 pt-1">
                  {[
                    'Live camera stream feed ingestion',
                    'Instant computer vision execution',
                    'Non-intrusive focus capture',
                    'Real-time engagement pipeline',
                  ].map((f) => (
                    <div key={f} className="flex items-start gap-2.5 text-xs">
                      <Check className="text-[#DEDBC8] size-4 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-400">{f}</span>
                    </div>
                  ))}
                </div>
              </div>
              <Link href="/login" className="inline-flex items-center gap-1.5 text-xs text-[#DEDBC8] hover:opacity-80 font-medium transition-opacity">
                Learn more <ArrowRight className="size-3.5 -rotate-45" />
              </Link>
            </div>
          </FeatureCard>

          {/* Step 03 — Processing & Logic */}
          <FeatureCard index={2}>
            <div className="h-full bg-[#212121] border border-white/5 rounded-2xl md:rounded-[1.5rem] p-6 flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                <div className="inline-flex items-center gap-2">
                  <span className="w-7 h-7 rounded-lg bg-[#DEDBC8]/10 border border-[#DEDBC8]/15 flex items-center justify-center text-[10px] font-mono font-semibold text-[#DEDBC8]">03</span>
                  <span className="text-[10px] uppercase tracking-widest text-gray-500 font-semibold">Step 03</span>
                </div>

                <div>
                  <p className="text-[10px] uppercase tracking-widest text-gray-600 font-semibold mb-1">Processing &amp; Logic</p>
                  <h3 className="text-base sm:text-lg font-bold text-[#E1E0CC] leading-snug">Behavioral Processing.</h3>
                </div>
                <div className="space-y-2.5 pt-1">
                  {[
                    'Facial cues & micro-expression mapping',
                    'Attentiveness metrics classification',
                    'On-device processing for privacy',
                    'Continuous synchronization hooks',
                  ].map((f) => (
                    <div key={f} className="flex items-start gap-2.5 text-xs">
                      <Check className="text-[#DEDBC8] size-4 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-400">{f}</span>
                    </div>
                  ))}
                </div>
              </div>

               <Link href="/login" className="inline-flex items-center gap-1.5 text-xs text-[#DEDBC8] hover:opacity-80 font-medium transition-opacity">
                Learn more <ArrowRight className="size-3.5 -rotate-45" />
              </Link>
            </div>
          </FeatureCard>

          {/* Step 04 — Insights & Analytics */}
          <FeatureCard index={3}>
            <div className="h-full bg-[#212121] border border-white/5 rounded-2xl md:rounded-[1.5rem] p-6 flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                <div className="inline-flex items-center gap-2">
                  <span className="w-7 h-7 rounded-lg bg-[#DEDBC8]/10 border border-[#DEDBC8]/15 flex items-center justify-center text-[10px] font-mono font-semibold text-[#DEDBC8]">04</span>
                  <span className="text-[10px] uppercase tracking-widest text-gray-500 font-semibold">Step 04</span>
                </div>

                <div>
                  <p className="text-[10px] uppercase tracking-widest text-gray-600 font-semibold mb-1">Insights &amp; Analytics</p>
                  <h3 className="text-base sm:text-lg font-bold text-[#E1E0CC] leading-snug">Automated Report Generation.</h3>
                </div>
                <div className="space-y-2.5 pt-1">
                  {[
                    'Session closing summary compile',
                    'Interactive graphical line graphs',
                    'Pie-chart engagement breakdowns',
                    'Instructor dashboard archiving',
                  ].map((f) => (
                    <div key={f} className="flex items-start gap-2.5 text-xs">
                      <Check className="text-[#DEDBC8] size-4 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-400">{f}</span>
                    </div>
                  ))}
                </div>
              </div>

              <Link href="/login" className="inline-flex items-center gap-1.5 text-xs text-[#DEDBC8] hover:opacity-80 font-medium transition-opacity">
                Learn more <ArrowRight className="size-3.5 -rotate-45" />
              </Link>
            </div>
          </FeatureCard>

        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-white/5 bg-black py-12 text-xs text-gray-500">
        <div className="max-w-6xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-6">
          <p>© 2026 ClassSense. All rights reserved.</p>
          <div className="flex gap-6">
            <a href="#" className="hover:text-white transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-white transition-colors">Terms of Use</a>
          </div>
        </div>
      </footer>

    </div>
  );
}

// Staggered Entrance Wrapper for Feature Cards
function FeatureCard({ children, index }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={isInView ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.95 }}
      transition={{
        duration: 0.8,
        delay: index * 0.15,
        ease: [0.22, 1, 0.36, 1]
      }}
      className="h-[480px] w-full"
    >
      {children}
    </motion.div>
  );
}

// About Feature Card with image on top
function AboutFeatureCard({ feature, index }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-60px' });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 30 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
      transition={{
        duration: 0.7,
        delay: (index % 3) * 0.12,
        ease: [0.22, 1, 0.36, 1],
      }}
      className="bg-[#101010] border border-white/5 rounded-3xl overflow-hidden flex flex-col"
    >
      {/* Image */}
      <div className="overflow-hidden">
        <img
          src={feature.image}
          alt={feature.heading}
          className="w-full h-48 object-cover rounded-2xl mb-0 transition-transform duration-500 hover:scale-105"
          onError={(e) => {
            e.target.style.background = '#1a1a1a';
            e.target.style.minHeight = '192px';
          }}
        />
      </div>

      {/* Text content */}
      <div className="p-6 flex flex-col gap-3 flex-1">
        <h3 className="text-base sm:text-lg font-semibold text-[#E1E0CC] leading-snug">
          {feature.heading}
        </h3>
        <p className="text-xs sm:text-sm text-gray-400 leading-relaxed flex-1">
          {feature.description}
        </p>
        <Link
          href="/login"
          className="inline-flex items-center gap-1.5 text-xs text-[#DEDBC8] hover:opacity-80 font-medium transition-opacity pt-2 border-t border-white/5 mt-auto"
        >
          Learn more <ArrowRight className="size-3.5 -rotate-45" />
        </Link>
      </div>
    </motion.div>
  );
}
