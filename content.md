const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
  LevelFormat, PageBreak, VerticalAlign
} = require('docx');
const fs = require('fs');

// ── helpers ──────────────────────────────────────────────────────────────────
const border = { style: BorderStyle.SINGLE, size: 1, color: 'CCCCCC' };
const borders = { top: border, bottom: border, left: border, right: border };
const thBorder = { style: BorderStyle.SINGLE, size: 1, color: '1A3C6B' };
const thBorders = { top: thBorder, bottom: thBorder, left: thBorder, right: thBorder };

const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 360, after: 160 },
  children: [new TextRun({ text, bold: true, size: 32, font: 'Arial', color: '1A3C6B' })]
});

const h2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 280, after: 120 },
  children: [new TextRun({ text, bold: true, size: 26, font: 'Arial', color: '1E5F8E' })]
});

const h3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  spacing: { before: 200, after: 80 },
  children: [new TextRun({ text, bold: true, size: 22, font: 'Arial', color: '2E7D6B' })]
});

const p = (text, opts = {}) => new Paragraph({
  spacing: { before: 60, after: 120 },
  children: [new TextRun({ text, size: 22, font: 'Arial', ...opts })]
});

const bold = (text) => new TextRun({ text, bold: true, size: 22, font: 'Arial' });
const normal = (text) => new TextRun({ text, size: 22, font: 'Arial' });

const bullet = (text, ref = 'bullets') => new Paragraph({
  numbering: { reference: ref, level: 0 },
  spacing: { before: 40, after: 60 },
  children: [new TextRun({ text, size: 22, font: 'Arial' })]
});

const bullet2 = (label, desc) => new Paragraph({
  numbering: { reference: 'bullets', level: 1 },
  spacing: { before: 40, after: 60 },
  children: [
    new TextRun({ text: label + ': ', bold: true, size: 22, font: 'Arial' }),
    new TextRun({ text: desc, size: 22, font: 'Arial' })
  ]
});

const divider = () => new Paragraph({
  spacing: { before: 160, after: 160 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 3, color: 'CCDDEE', space: 1 } },
  children: []
});

const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

const badge = (label, color) => new Paragraph({
  spacing: { before: 40, after: 80 },
  children: [
    new TextRun({ text: `  ${label}  `, bold: true, size: 18, font: 'Arial', color: 'FFFFFF',
      highlight: color === 'blue' ? 'darkBlue' : color === 'green' ? 'darkGreen' : 'darkRed' })
  ]
});

const mkTable = (headers, rows, colWidths) => {
  const totalWidth = colWidths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((h, i) => new TableCell({
          borders: thBorders,
          width: { size: colWidths[i], type: WidthType.DXA },
          shading: { fill: '1A3C6B', type: ShadingType.CLEAR },
          margins: { top: 100, bottom: 100, left: 140, right: 140 },
          children: [new Paragraph({
            alignment: AlignmentType.LEFT,
            children: [new TextRun({ text: h, bold: true, size: 20, font: 'Arial', color: 'FFFFFF' })]
          })]
        }))
      }),
      ...rows.map((row, ri) => new TableRow({
        children: row.map((cell, ci) => new TableCell({
          borders,
          width: { size: colWidths[ci], type: WidthType.DXA },
          shading: { fill: ri % 2 === 0 ? 'F4F8FB' : 'FFFFFF', type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 140, right: 140 },
          children: [new Paragraph({
            children: [new TextRun({ text: cell, size: 20, font: 'Arial' })]
          })]
        }))
      }))
    ]
  });
};

// ── DOCUMENT ─────────────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      {
        reference: 'bullets',
        levels: [
          { level: 0, format: LevelFormat.BULLET, text: '\u2022', alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
          { level: 1, format: LevelFormat.BULLET, text: '\u25E6', alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 1080, hanging: 360 } } } }
        ]
      }
    ]
  },
  styles: {
    default: { document: { run: { font: 'Arial', size: 22 } } },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 32, bold: true, font: 'Arial', color: '1A3C6B' },
        paragraph: { spacing: { before: 360, after: 160 }, outlineLevel: 0 } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 26, bold: true, font: 'Arial', color: '1E5F8E' },
        paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 22, bold: true, font: 'Arial', color: '2E7D6B' },
        paragraph: { spacing: { before: 200, after: 80 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1260, bottom: 1440, left: 1260 }
      }
    },
    children: [

      // ── COVER ──────────────────────────────────────────────────────────────
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 1440, after: 80 },
        children: [new TextRun({ text: 'ClassSense', bold: true, size: 64, font: 'Arial', color: '1A3C6B' })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 80 },
        children: [new TextRun({ text: 'Class Monitoring System', size: 32, font: 'Arial', color: '1E5F8E' })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 120, after: 480 },
        children: [new TextRun({ text: 'Frontend Content & UX Specification', bold: true, size: 28, font: 'Arial', color: '555555' })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 80, after: 80 },
        children: [new TextRun({ text: 'Prepared by: Sameer Shah & Ismail Haroon', size: 22, font: 'Arial', color: '666666' })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 40, after: 80 },
        children: [new TextRun({ text: 'FYDP-1 \u2014 Fall 2025 | Iqra University', size: 22, font: 'Arial', color: '666666' })]
      }),
      divider(),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 120, after: 80 },
        children: [new TextRun({ text: 'Document Scope', bold: true, size: 24, font: 'Arial', color: '333333' })]
      }),
      p('This document defines every piece of content that goes on each screen of ClassSense \u2014 the landing/marketing page, the login screen, the instructor dashboard, the admin dashboard, and all supporting pages. It covers copy (headlines, body text, labels, CTAs), structural components (navbar, footer, sidebar), color guidance, and placeholder data.'),
      pageBreak(),

      // ── SECTION 1: GLOBAL COMPONENTS ──────────────────────────────────────
      h1('1.  Global Components'),
      p('These components appear on every page (or almost every page) of ClassSense. Define them once and reuse them consistently.'),

      // 1.1 NAVBAR
      h2('1.1  Navigation Bar (Navbar)'),
      p('The navbar is the top-level persistent bar present on the landing page and all authenticated pages. It adapts based on whether the user is logged in or not.'),

      h3('1.1.1  Pre-Login Navbar (Landing Page)'),
      new Paragraph({ spacing: { before: 60, after: 80 }, children: [bold('Left side \u2014 Brand Logo & Name'), normal(':')]  }),
      bullet2('Logo', 'A simple eye / camera icon in teal (#2E9E8A) representing classroom observation.'),
      bullet2('App Name', '"ClassSense" in bold dark-blue (#1A3C6B), font size 22px.'),
      new Paragraph({ spacing: { before: 100, after: 80 }, children: [bold('Center \u2014 Navigation Links'), normal(':')]  }),
      bullet2('Home', 'Scrolls to the Hero section.'),
      bullet2('Features', 'Scrolls to the Features section.'),
      bullet2('How It Works', 'Scrolls to the How It Works section.'),
      bullet2('Pricing', 'Scrolls to the Pricing section.'),
      bullet2('About', 'Scrolls to the About / Team section.'),
      bullet2('Contact', 'Scrolls to the Contact section.'),
      new Paragraph({ spacing: { before: 100, after: 80 }, children: [bold('Right side \u2014 Action Buttons'), normal(':')]  }),
      bullet2('Log In', 'Outlined button \u2014 takes the user to /login.'),
      bullet2('Request Demo', 'Filled teal button \u2014 opens a demo-request modal / mailto link.'),

      h3('1.1.2  Post-Login Navbar (Authenticated)'),
      bullet2('Left', '"ClassSense" logo + name (links back to dashboard home).'),
      bullet2('Center links', 'Dashboard | Sessions | Reports | Analytics | Settings.'),
      bullet2('Right', 'Notification bell icon (with badge count) + Avatar / Name dropdown (Profile, Settings, Log Out).'),
      bullet2('Active state', 'Currently active link underlined in teal.'),
      bullet2('Mobile', 'Hamburger menu collapses all links into a slide-in drawer.'),

      // 1.2 SIDEBAR
      h2('1.2  Sidebar (Authenticated Pages Only)'),
      p('A collapsible left-side navigation panel used inside the app (instructor / admin dashboards).'),
      new Paragraph({ spacing: { before: 60, after: 60 }, children: [bold('Instructor Sidebar links:')]  }),
      bullet('\uD83D\uDCCA  Dashboard \u2014 Overview & quick stats'),
      bullet('\uD83C\uDFEB  Start New Session'),
      bullet('\u23F1\uFE0F  Live Monitor \u2014 Active when a session is running'),
      bullet('\uD83D\uDCC3  Session History'),
      bullet('\uD83D\uDCC8  Course Analytics'),
      bullet('\uD83D\uDCE5  Download Reports'),
      bullet('\u2699\uFE0F  Settings'),
      bullet('\u2753  Help & Support'),
      new Paragraph({ spacing: { before: 100, after: 60 }, children: [bold('Admin Sidebar links:')]  }),
      bullet('\uD83D\uDCCA  Admin Dashboard'),
      bullet('\uD83D\uDC65  Manage Users'),
      bullet('\uD83C\uDFEB  Manage Classrooms'),
      bullet('\uD83D\uDD0D  Audit Logs'),
      bullet('\uD83E\uDDE0  Model Calibration'),
      bullet('\uD83D\uDEE1\uFE0F  Privacy & Retention Policies'),
      bullet('\uD83D\uDCB0  Budget / Billing'),
      bullet('\u2699\uFE0F  System Settings'),

      // 1.3 FOOTER
      h2('1.3  Footer'),
      p('Present on the landing page and all static pages (About, Privacy Policy, Help).'),
      new Paragraph({ spacing: { before: 60, after: 80 }, children: [bold('Column 1 \u2014 Brand:')]  }),
      bullet2('Logo + ClassSense', '"Intelligent Classroom Analytics"'),
      bullet2('Tagline', '"Know your class. Teach with clarity."'),
      bullet2('Social icons', 'LinkedIn, GitHub (project repo).'),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [bold('Column 2 \u2014 Product:')]  }),
      bullet('Features'),
      bullet('How It Works'),
      bullet('Pricing'),
      bullet('Request a Demo'),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [bold('Column 3 \u2014 Company:')]  }),
      bullet('About Us'),
      bullet('Team'),
      bullet('FYP Project \u2014 Iqra University'),
      bullet('Contact'),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [bold('Column 4 \u2014 Legal:')]  }),
      bullet('Privacy Policy'),
      bullet('Terms of Use'),
      bullet('Data Retention Policy'),
      new Paragraph({ spacing: { before: 80, after: 100 }, children: [bold('Bottom bar:'), normal(' \u00A9 2026 ClassSense \u2014 FYDP-1, Iqra University. All rights reserved.')]  }),
      divider(),

      pageBreak(),

      // ── SECTION 2: LANDING PAGE ──────────────────────────────────────────
      h1('2.  Landing Page  (/  or  /home)'),
      p('The public-facing marketing page. Its goal is to explain what ClassSense does, build trust, and convert visitors (institutions / instructors) to request a demo or log in.'),

      h2('2.1  Hero Section'),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [bold('Background:'), normal(' Full-width dark-blue (#0D1F3C) with a subtle diagonal grid pattern and a teal glow behind the headline.')]  }),
      new Paragraph({ spacing: { before: 60, after: 80 }, children: [bold('Badge / eyebrow tag \u2014 small pill above the headline:'), normal('"AI-Powered Classroom Insights"')]  }),
      new Paragraph({ spacing: { before: 60, after: 80 }, children: [bold('Main Headline (H1):'), new TextRun({ text: '"See Your Classroom.\nTeach Smarter."', bold: true, size: 22, font: 'Arial', color: '2E9E8A' })]  }),
      new Paragraph({ spacing: { before: 60, after: 80 }, children: [bold('Sub-headline:'), normal(' "ClassSense uses AI-powered video analytics to give instructors real-time visibility into student engagement, attention, and emotion \u2014 without ever storing a face."')]  }),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [bold('CTA Buttons:')]  }),
      bullet2('Primary (teal, filled)', '"Request a Demo \u2192"'),
      bullet2('Secondary (white, outlined)', '"Log In to ClassSense"'),
      new Paragraph({ spacing: { before: 80, after: 60 }, children: [bold('Trust badges below buttons:')]  }),
      bullet('\uD83D\uDD12  Privacy-First \u2014 No Raw Video Stored'),
      bullet('\u26A1  Real-Time Analytics'),
      bullet('\uD83C\uDFEB  Built for Classrooms'),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [bold('Right-side visual:'), normal(' A mockup/screenshot of the Live Monitoring Dashboard with live engagement gauge and emotion bars.')]  }),

      h2('2.2  Stats / Social Proof Bar'),
      p('A full-width light-grey bar below the hero with 3\u20134 numbers:'),
      new Paragraph({ spacing: { before: 60, after: 80 }, children: [normal('\u2764\uFE0F  Use placeholder data for FYP purposes:')]  }),
      mkTable(
        ['Stat Label', 'Value', 'Note'],
        [
          ['Engagement Insights Per Session', '500+', 'Estimated data points per 1-hour class'],
          ['Analytics Latency', '<2 sec', 'Real-time update speed'],
          ['Anonymized Tracking', '100%', 'No PII stored ever'],
          ['Supported Classroom Types', '10+', 'Lab, lecture hall, seminar room, etc.'],
        ],
        [3000, 2000, 3360]
      ),

      h2('2.3  Features Section'),
      p('Headline: "Everything You Need to Monitor Engagement \u2014 Instantly"'),
      p('Sub-headline: "ClassSense brings together AI, privacy-by-design, and real-time analytics in one dashboard built for educators."'),
      p('Layout: 3-column card grid. Each card has an icon, title, and 2\u20133 sentence description.'),
      new Paragraph({ spacing: { before: 100, after: 80 }, children: [bold('Feature Cards:')]  }),
      mkTable(
        ['Icon', 'Card Title', 'Card Body Text'],
        [
          ['\uD83D\uDC41\uFE0F', 'Live Engagement Monitoring', 'See a live class-level engagement score, attention breakdown (attentive / confused / distracted), and face-count \u2014 all updated every 2 seconds.'],
          ['\uD83E\uDDE0', 'Emotion Analytics', 'AI classifies dominant facial expressions into 7 categories. Aggregated emotion distribution helps instructors understand the mood of the room.'],
          ['\uD83D\uDDFA\uFE0F', 'Attention Heatmaps', 'Gaze estimation shows which zones of the room are paying attention and which are drifting, so you know when and where to re-engage.'],
          ['\uD83D\uDD14', 'Smart Alerts', 'Configure engagement or attention thresholds. ClassSense notifies you when the class dips below your defined level so you can intervene in time.'],
          ['\uD83D\uDCC8', 'Course Analytics & Trends', 'Compare engagement across sessions for a course. Spot patterns over weeks and get AI-generated insights to improve your teaching.'],
          ['\uD83D\uDEE1\uFE0F', 'Privacy-by-Design', 'Faces are never stored. Every student gets a session-scoped anonymized ID. Raw frames are discarded after inference \u2014 no video files, ever.'],
          ['\uD83D\uDCCB', 'Exportable Reports', 'Download session summaries and course-level analytics as PDF or CSV. Perfect for institutional reviews and teaching portfolios.'],
          ['\u26A1', 'Pre-flight Hardware Checks', 'Run a quick camera, FPS, and permission check before every session so nothing breaks mid-lecture.'],
          ['\uD83D\uDCBB', 'Works on Standard Hardware', 'Optimized lightweight models run in real-time on a standard classroom laptop or dedicated camera setup \u2014 no GPU required.'],
        ],
        [700, 2200, 5460]
      ),

      h2('2.4  How It Works Section'),
      p('Headline: "Get Insights in 3 Simple Steps"'),
      p('Layout: Numbered step cards in a horizontal row (or vertical on mobile).'),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [bold('Step 1 \u2014 Set Up Your Session')]  }),
      bullet('Icon: \uD83C\uDFEB'),
      bullet('Title: "Configure & Check"'),
      bullet('Body: "Select your course, classroom, and privacy mode. Run a quick pre-flight check to confirm your camera and permissions are ready."'),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [bold('Step 2 \u2014 Monitor in Real Time')]  }),
      bullet('Icon: \uD83D\uDC41\uFE0F'),
      bullet('Title: "Watch & React"'),
      bullet('Body: "ClassSense processes the live camera feed, assigns anonymized IDs to detected faces, and streams engagement, attention, and emotion metrics to your dashboard."'),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [bold('Step 3 \u2014 Review & Improve')]  }),
      bullet('Icon: \uD83D\uDCC8'),
      bullet('Title: "Analyze & Export"'),
      bullet('Body: "When the session ends, generate a detailed report. Review trends over time, compare sessions, and download data for your records."'),

      h2('2.5  Privacy Promise Section'),
      p('Headline: "\uD83D\uDD12  Built to Protect Students"'),
      p('Sub-headline: "ClassSense was designed with privacy as a requirement, not an afterthought."'),
      new Paragraph({ spacing: { before: 60, after: 80 }, children: [bold('Promise Cards (3 wide):')]  }),
      bullet2('No Raw Video Storage', 'Frames are processed in memory and discarded immediately after inference. No video files are ever written to disk or uploaded to a server.'),
      bullet2('Anonymized Identities', 'Every detected face is assigned a temporary, session-scoped ID. Names, biometric data, and personal identifiers are never linked or stored.'),
      bullet2('Configurable Retention', 'Administrators control how long session analytics data is retained and can purge records at any time from the admin panel.'),

      h2('2.6  Pricing Section'),
      p('Headline: "Simple, Institution-Friendly Pricing"'),
      p('Sub-headline: "Designed to fit academic procurement processes. Flexible tiers for small departments to entire universities."'),
      p('Note for FYP: Use placeholder / "Coming Soon" pricing. You can show the tier structure without real prices.'),
      mkTable(
        ['Plan', 'Target', 'Features', 'Price'],
        [
          ['Pilot', 'Single department / trial', 'Up to 5 classrooms, basic reports, email support', 'Free (30-day pilot)'],
          ['Institutional', 'University / college', 'Unlimited classrooms, full analytics, CSV/PDF export, audit logs, admin panel', 'Contact for pricing'],
          ['Enterprise', 'Multi-campus / large org', 'Everything in Institutional + SLA, custom integrations, LMS API, on-site deployment', 'Custom quote'],
        ],
        [1500, 2000, 3400, 1460]
      ),

      h2('2.7  About / Team Section'),
      p('Headline: "Meet the Team Behind ClassSense"'),
      p('Sub-headline: "ClassSense is a Final Year Design Project (FYDP-1) developed at Iqra University, Faculty of Engineering, Sciences & Technology."'),
      new Paragraph({ spacing: { before: 80, after: 60 }, children: [bold('Team Cards:')]  }),
      bullet2('Sameer Shah (62662)', 'Co-developer \u2014 AI / CV pipeline, backend architecture.'),
      bullet2('Ismail Haroon (63188)', 'Co-developer \u2014 frontend, system integration, API design.'),
      bullet2('Supervisor', 'Ms. Zuha Soomro'),
      bullet2('FYDP Coordinator', 'Ms. Saira Khurram Arbab'),
      bullet2('Institution', 'Iqra University, BS Computer Science, Fall 2025'),

      h2('2.8  Contact / CTA Section'),
      p('Headline: "Ready to Transform Your Classroom?"'),
      p('Sub-headline: "Reach out to schedule a live demo or learn more about piloting ClassSense at your institution."'),
      new Paragraph({ spacing: { before: 60, after: 80 }, children: [bold('Contact Form Fields:')]  }),
      bullet('Full Name'),
      bullet('Institution / University Name'),
      bullet('Email Address'),
      bullet('Role (Instructor / Department Head / IT / Other)'),
      bullet('Message / What are you looking for?'),
      bullet('Button: "Send Message \u2192" (teal, filled)'),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [bold('Alternative contact line:'), normal(' \u201COr email us at: classsense@iqra.edu.pk\u201D')]  }),
      divider(),
      pageBreak(),

      // ── SECTION 3: LOGIN PAGE ─────────────────────────────────────────────
      h1('3.  Login Page  (/login)'),
      h2('3.1  Layout'),
      p('Split-screen layout: left half is a dark-blue panel with branding, right half is the login form on white.'),
      new Paragraph({ spacing: { before: 60, after: 80 }, children: [bold('Left panel content:')]  }),
      bullet2('Logo + App Name', '"ClassSense"'),
      bullet2('Tagline', '"Know your class. Teach with clarity."'),
      bullet2('Visual', 'Subtle illustration or screenshot mockup of the dashboard.'),
      bullet2('Bottom note', '"Trusted by instructors at Iqra University"'),

      h2('3.2  Login Form'),
      new Paragraph({ spacing: { before: 60, after: 80 }, children: [bold('Page title (H2):'), normal(' "Welcome Back"')]  }),
      new Paragraph({ spacing: { before: 40, after: 80 }, children: [bold('Subtitle:'), normal(' "Log in to your ClassSense account"')]  }),
      new Paragraph({ spacing: { before: 80, after: 60 }, children: [bold('Form Fields:')]  }),
      bullet2('Email Address', 'Placeholder: "you@institution.edu"  |  Icon: envelope'),
      bullet2('Password', 'Placeholder: "\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022"  |  Show/hide toggle  |  Icon: padlock'),
      new Paragraph({ spacing: { before: 80, after: 60 }, children: [bold('Form Actions:')]  }),
      bullet2('Remember me', 'Checkbox \u2014 left-aligned below password field'),
      bullet2('Forgot Password?', 'Right-aligned link \u2014 opens the password reset flow'),
      bullet2('Log In Button', 'Full-width, teal (#2E9E8A), rounded, text: "Log In \u2192"'),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [bold('MFA Prompt (if enabled):'), normal(' After successful password validation, a second screen appears: "Enter the 6-digit code sent to your email."')]  }),
      new Paragraph({ spacing: { before: 60, after: 80 }, children: [bold('Role routing after login:')]  }),
      bullet2('Instructor', 'Redirected to /dashboard (Instructor Dashboard)'),
      bullet2('Admin', 'Redirected to /admin (Admin Dashboard)'),

      h2('3.3  Forgot Password Flow'),
      new Paragraph({ spacing: { before: 60, after: 80 }, children: [bold('Step 1 \u2014 Enter Email:'), normal(' Prompt: "Enter your registered email and we\u2019ll send you a reset link." Field + "Send Reset Link" button.')]  }),
      new Paragraph({ spacing: { before: 40, after: 80 }, children: [bold('Step 2 \u2014 Confirmation:'), normal(' "Check your inbox! A password reset link has been sent to [email]. Link expires in 30 minutes."')]  }),
      new Paragraph({ spacing: { before: 40, after: 80 }, children: [bold('Step 3 \u2014 Reset Form:'), normal(' New Password + Confirm Password fields. Validation: min 8 chars, 1 uppercase, 1 number. Button: "Reset Password"')]  }),
      divider(),
      pageBreak(),

      // ── SECTION 4: INSTRUCTOR DASHBOARD ──────────────────────────────────
      h1('4.  Instructor Dashboard  (/dashboard)'),
      p('The main home screen that an instructor sees after logging in. It shows an overview of their activity without a live session running.'),

      h2('4.1  Page Header'),
      bullet2('Greeting', '"Good morning, [Instructor Name] \uD83D\uDC4B" (personalized, time-aware)'),
      bullet2('Subtitle', '"Here\u2019s an overview of your recent teaching activity."'),
      bullet2('Quick action button', '"+ Start New Session" \u2014 teal, top-right corner'),

      h2('4.2  Stats Summary Cards (Top Row)'),
      p('4 horizontal stat cards, each with icon, number, and label:'),
      mkTable(
        ['Card', 'Icon', 'Value (placeholder)', 'Label'],
        [
          ['Total Sessions', '\uD83C\uDFEB', '24', 'Sessions This Semester'],
          ['Avg. Engagement', '\uD83D\uDCAF', '74%', 'Average Engagement Rate'],
          ['Reports Exported', '\uD83D\uDCCB', '18', 'Reports Downloaded'],
          ['Alerts Triggered', '\uD83D\uDD14', '6', 'Low-Engagement Alerts'],
        ],
        [2000, 1000, 2000, 3360]
      ),

      h2('4.3  Recent Sessions Table'),
      p('Headline: "Recent Sessions"'),
      p('Show the last 5 sessions with a "View All" link to /sessions.'),
      mkTable(
        ['Date', 'Course', 'Duration', 'Avg Engagement', 'Status', 'Action'],
        [
          ['14 Jun 2026', 'CS-401 \u2014 AI & ML', '1h 10m', '81%', 'Completed', 'View Report'],
          ['12 Jun 2026', 'CS-301 \u2014 DSA', '55m', '67%', 'Completed', 'View Report'],
          ['10 Jun 2026', 'CS-401 \u2014 AI & ML', '1h 00m', '72%', 'Completed', 'View Report'],
          ['7 Jun 2026', 'CS-201 \u2014 OOP', '50m', '59%', 'Alert Triggered', 'View Report'],
          ['5 Jun 2026', 'CS-301 \u2014 DSA', '1h 05m', '76%', 'Completed', 'View Report'],
        ],
        [1400, 2200, 1100, 1600, 1700, 1360]
      ),

      h2('4.4  Engagement Trend Chart'),
      bullet2('Title', '"Engagement Over the Last 10 Sessions"'),
      bullet2('Chart type', 'Line chart \u2014 X axis: session date, Y axis: avg engagement %'),
      bullet2('Color', 'Teal line with dots; shaded area below the line'),
      bullet2('Placeholder note', 'Use dummy data: 68, 74, 71, 80, 77, 65, 70, 73, 81, 76'),

      h2('4.5  Upcoming / Scheduled Sessions'),
      p('Small card on the right side (or below chart):'),
      bullet2('Title', '"Upcoming Sessions"'),
      bullet2('Content', 'Show next 2\u20133 scheduled classes (course name, date, time) if scheduling is implemented. Otherwise show: "No sessions scheduled. Start a new session whenever you\u2019re ready."'),
      bullet2('Button', '"+ Schedule Session"'),

      h2('4.6  Notification Panel'),
      p('A bell icon in the navbar expands a dropdown:'),
      bullet('\uD83D\uDD14  "CS-201 session on Jun 7: Engagement dropped below 60% at 10:42 AM" (unread)'),
      bullet('\u2705  "Session report for Jun 12 is ready for download." (read)'),
      bullet('\uD83D\uDD27  "System update: Model v1.2 calibrated successfully." (read)'),
      divider(),
      pageBreak(),

      // ── SECTION 5: START NEW SESSION SETUP ───────────────────────────────
      h1('5.  Start New Session Setup  (/session/new)'),
      p('This is the 2-step flow before a live monitoring session begins.'),

      h2('5.1  Step 1 \u2014 Session Configuration Form'),
      p('Headline: "Configure Your Session"'),
      p('Sub-headline: "Set up your course details and privacy preferences before starting."'),
      new Paragraph({ spacing: { before: 80, after: 80 }, children: [bold('Form Fields:')]  }),
      mkTable(
        ['Field', 'Type', 'Placeholder / Options', 'Required'],
        [
          ['Select Course', 'Dropdown', 'CS-401 AI & ML | CS-301 DSA | CS-201 OOP | + Add New', 'Yes'],
          ['Select Classroom / Camera', 'Dropdown', 'Room 301 \u2014 Cam A | Room 205 \u2014 Cam B | Laptop Webcam', 'Yes'],
          ['Session Date', 'Date Picker', 'Today\'s date pre-filled', 'Yes'],
          ['Start Time', 'Time Picker', 'Current time pre-filled', 'Yes'],
          ['Expected Duration', 'Dropdown', '30 min | 45 min | 1 hour | 1.5 hours | 2 hours', 'Yes'],
          ['Privacy Mode', 'Toggle', 'Anonymized Tracking ON (default, cannot be disabled)', 'Always On'],
          ['Alert Threshold', 'Slider (0\u2013100%)', 'Default: 60% \u2014 Alert if engagement drops below this value', 'Optional'],
          ['Notes (optional)', 'Text area', 'E.g., "Guest lecture today \u2014 larger class than usual"', 'No'],
        ],
        [2000, 1400, 3400, 1560]
      ),
      new Paragraph({ spacing: { before: 100, after: 80 }, children: [bold('Buttons:')]  }),
      bullet2('Next: Run Pre-flight Checks \u2192', 'Proceeds to Step 2 (teal, filled)'),
      bullet2('Save as Draft', 'Saves form state without proceeding (outlined)'),

      h2('5.2  Step 2 \u2014 Pre-flight Checks'),
      p('Headline: "System Readiness Check"'),
      p('Sub-headline: "Running quick checks before your session starts. This takes a few seconds."'),
      mkTable(
        ['Check Item', 'Status Options', 'Fail Message'],
        [
          ['Camera Access', '\u2705 Pass | \u274C Fail | \u23F3 Checking\u2026', '"Camera not detected or permission denied. Please allow access in browser settings."'],
          ['Camera FPS', '\u2705 Pass (>15 FPS) | \u26A0\uFE0F Warn (<15 FPS) | \u274C Fail', '"Low frame rate detected. Analytics quality may be reduced."'],
          ['Browser Permissions', '\u2705 Pass | \u274C Fail', '"Microphone/camera permissions denied. Please review site permissions."'],
          ['Server Connection', '\u2705 Pass | \u274C Fail', '"Cannot reach the ClassSense analytics server. Check your internet connection."'],
          ['Analytics Pipeline', '\u2705 Ready | \u23F3 Initializing', '"Pipeline could not initialize. Please refresh and try again."'],
        ],
        [2400, 2000, 3960]
      ),
      new Paragraph({ spacing: { before: 100, after: 80 }, children: [bold('Buttons after checks complete:')]  }),
      bullet2('Start Session \u2192', 'Enabled only when all checks pass. Teal, filled.'),
      bullet2('Re-run Checks', 'Outlined button.'),
      bullet2('\u2190 Back to Configuration', 'Grey text link.'),
      divider(),
      pageBreak(),

      // ── SECTION 6: LIVE MONITORING DASHBOARD ────────────────────────────
      h1('6.  Live Classroom Monitoring Dashboard  (/session/live)'),
      p('The most important screen in ClassSense. Active during a live session. Must be scannable at a glance while the instructor is teaching.'),

      h2('6.1  Page Header Bar'),
      bullet2('Left', '"LIVE \u2022" badge (red pulsing dot) + Course Name + Classroom'),
      bullet2('Center', 'Session timer: "00:32:14 elapsed"'),
      bullet2('Right', '"Pause Session" | "End Session" buttons'),

      h2('6.2  Primary Metrics Row (Top)'),
      p('4 large stat widgets displayed in a horizontal row:'),
      mkTable(
        ['Widget', 'Metric Displayed', 'Visual'],
        [
          ['Engagement Score', 'Class-level engagement % \u2014 e.g. "74%"', 'Circular gauge (arc chart), teal fill'],
          ['Students Detected', 'Anonymized face count \u2014 e.g. "28 students"', 'Person icon + number'],
          ['Attention Level', 'Attention % \u2014 e.g. "69% Attentive"', 'Horizontal progress bar (green/amber/red)'],
          ['Active Alerts', 'Count of threshold breaches \u2014 e.g. "2 alerts"', 'Bell icon + badge, orange if >0'],
        ],
        [2000, 3500, 2860]
      ),

      h2('6.3  Attention Breakdown Panel'),
      p('Title: "Attention Breakdown"'),
      p('Horizontal stacked bar or 3 mini progress bars:'),
      bullet2('Attentive', 'e.g. 69% \u2014 green bar'),
      bullet2('Confused', 'e.g. 18% \u2014 amber bar'),
      bullet2('Distracted', 'e.g. 13% \u2014 red bar'),
      p('Updated every 2\u20133 seconds in real time.'),

      h2('6.4  Emotion Distribution Panel'),
      p('Title: "Emotion Summary (Last 30 sec)"'),
      p('A horizontal bar chart or donut chart showing % distribution across 7 emotion categories:'),
      bullet('Neutral \u2014 Most common in classrooms'),
      bullet('Happy'),
      bullet('Confused'),
      bullet('Surprised'),
      bullet('Bored / Sad'),
      bullet('Focused (derived from neutral + gaze)'),
      bullet('Disengaged'),
      p('Note: Labels use classroom-friendly terms. All values are anonymized and aggregated.'),

      h2('6.5  Engagement Timeline (Mini Chart)'),
      p('Title: "Engagement Over This Session"'),
      p('A real-time updating line chart showing engagement % on the Y-axis and time elapsed on the X-axis. New data points added every 30 seconds.'),
      bullet2('Color', 'Teal line'),
      bullet2('Threshold line', 'Dashed red line at the configured alert threshold (e.g. 60%)'),
      bullet2('Alert markers', 'Red dot on the timeline where engagement dropped below threshold'),

      h2('6.6  Attention Heatmap'),
      p('Title: "Classroom Attention Zones"'),
      p('A top-down grid representation of the classroom (configurable based on classroom layout). Cells are colored by attention level:'),
      bullet2('Green cells', 'High attention zone'),
      bullet2('Amber cells', 'Medium attention'),
      bullet2('Red cells', 'Low attention / distracted cluster'),
      p('Privacy note below the heatmap: "\uD83D\uDD12 No identifiable information is shown. Zones are based on gaze estimation only."'),

      h2('6.7  Alerts Panel'),
      p('Title: "Session Alerts"'),
      p('A vertical scrollable list of alerts triggered during this session:'),
      bullet('\uD83D\uDD14  10:42 AM \u2014 Engagement dropped below 60% (Class avg: 54%) \u2014 [Dismiss]'),
      bullet('\uD83D\uDD14  10:28 AM \u2014 High distraction detected in Zones B & C \u2014 [Dismiss]'),
      p('Empty state: "\u2705 No alerts yet. Engagement is above your configured threshold."'),

      h2('6.8  Session Controls'),
      p('A fixed bottom bar or floating action area:'),
      bullet2('\u23F8 Pause Session', 'Suspends analytics, pauses timer. Stream continues but metrics stop.'),
      bullet2('\u25B6 Resume Session', 'Visible only when paused.'),
      bullet2('\uD83D\uDCF8 Take Snapshot', 'Saves current metrics summary to session log.'),
      bullet2('\u23F9 End Session', 'Stops session, finalizes data, prompts "Generate Report?" dialog.'),

      h2('6.9  End Session Confirmation Dialog'),
      p('Modal title: "End This Session?"'),
      p('Body: "Are you sure you want to end the session? All analytics will be finalized and a session report will be generated."'),
      bullet2('Confirm & Generate Report', 'Ends session and navigates to /session/report/[id] \u2014 teal, filled'),
      bullet2('End Without Report', 'Ends session with no report generated \u2014 outlined'),
      bullet2('Cancel', 'Returns to live session'),
      divider(),
      pageBreak(),

      // ── SECTION 7: SESSION REPORT ─────────────────────────────────────────
      h1('7.  Session Report Page  (/session/report/:id)'),
      p('The post-session summary. Shown immediately after ending a session, and also accessible from Session History.'),

      h2('7.1  Report Header'),
      bullet2('Title', '"Session Report \u2014 [Course Name]"'),
      bullet2('Subtitle', '"[Date] \u2014 [Classroom] \u2014 [Duration]"'),
      bullet2('Status badge', '"Completed \u2705" or "Alert Triggered \uD83D\uDD14"'),
      bullet2('Export buttons (top-right)', '"Download PDF" | "Download CSV"'),

      h2('7.2  Summary Stat Cards'),
      mkTable(
        ['Metric', 'Placeholder Value', 'Description'],
        [
          ['Overall Engagement', '74%', 'Session-wide average engagement score'],
          ['Peak Engagement Time', '10:28 AM \u2014 88%', 'Highest engagement moment in the session'],
          ['Lowest Engagement Time', '10:42 AM \u2014 54%', 'Lowest point, alert triggered here'],
          ['Avg. Students Detected', '27', 'Average anonymized face count per frame'],
          ['Total Alerts', '2', 'Number of threshold breaches'],
          ['Session Duration', '1h 04m', 'Total time from start to end'],
        ],
        [2500, 2000, 3860]
      ),

      h2('7.3  Engagement Timeline Chart'),
      p('Full-width line chart showing engagement % across the full session timeline. Same as the live chart but now complete.'),

      h2('7.4  Attention & Emotion Summary'),
      p('Side-by-side panels:'),
      bullet2('Left', 'Attention Breakdown (Attentive / Confused / Distracted) \u2014 pie chart or stacked bar'),
      bullet2('Right', 'Emotion Distribution \u2014 horizontal bar chart showing 7 emotion categories'),

      h2('7.5  Alert Log'),
      p('Table of all alerts triggered during the session:'),
      mkTable(
        ['Time', 'Alert Type', 'Metric Value', 'Threshold', 'Resolved'],
        [
          ['10:28 AM', 'Low Engagement', '54%', '60%', 'Auto-dismissed after 5 min'],
          ['10:42 AM', 'High Distraction', '41% Attentive', '50%', 'Manual dismiss'],
        ],
        [1400, 2000, 1800, 1500, 2660]
      ),

      h2('7.6  Privacy & Audit Footer in Report'),
      p('"This report contains no personally identifiable information. All student faces were tracked using session-scoped anonymized IDs. No raw video was stored."'),
      p('"Report generated: [timestamp]. Generated by: [Instructor Name]. Data retained for: 90 days (per institutional policy)."'),
      divider(),
      pageBreak(),

      // ── SECTION 8: COURSE ANALYTICS DASHBOARD ───────────────────────────
      h1('8.  Course Analytics Dashboard  (/analytics)'),
      p('Aggregates data across multiple sessions for a single course. Accessible from the sidebar under "Course Analytics".'),

      h2('8.1  Page Header & Filters'),
      bullet2('Title', '"Course Analytics"'),
      bullet2('Course selector dropdown', 'CS-401 AI & ML | CS-301 DSA | CS-201 OOP'),
      bullet2('Date range picker', '"Last 30 days / Last semester / Custom"'),
      bullet2('Session type filter', 'All | Lectures | Labs'),

      h2('8.2  Summary Cards'),
      mkTable(
        ['Card', 'Metric', 'Placeholder'],
        [
          ['Course Avg Engagement', 'Avg across all sessions', '74%'],
          ['Sessions Analyzed', 'Total session count', '12 sessions'],
          ['Best Session', 'Highest avg engagement', '14 Jun \u2014 88%'],
          ['Worst Session', 'Lowest avg engagement', '7 Jun \u2014 58%'],
        ],
        [2400, 2800, 3160]
      ),

      h2('8.3  Engagement Trend Chart'),
      p('Title: "Session-by-Session Engagement Trend"'),
      p('Line chart: X axis = sessions (by date), Y axis = avg engagement %. Shows the trajectory over the semester.'),
      bullet2('Trendline', 'Optional polynomial trendline to show overall direction'),
      bullet2('Color coding', 'Green if trending up, red if trending down, grey if flat'),

      h2('8.4  Distraction Heatmap (Cross-Session)'),
      p('Title: "Distraction Comparison by Session"'),
      p('Bar chart or heatmap grid. X axis = sessions, Y axis = distraction %. Quickly shows which sessions had the most disengagement.'),

      h2('8.5  AI Insights Panel'),
      p('Title: "Automated Insights"'),
      p('A card with 3\u20135 AI-generated text insights (static copy for FYP prototype):'),
      bullet('"Engagement consistently drops in the last 15 minutes of class. Consider introducing a quiz or activity near the end."'),
      bullet('"Sessions after 2 PM show 12% lower engagement on average. Morning slots appear more effective."'),
      bullet('"Confusion spikes were detected during sessions covering Algorithm Complexity. Students may need supplementary materials."'),
      bullet('"Your best-performing session was June 14 \u2014 the interactive coding demo drove 88% engagement."'),
      divider(),
      pageBreak(),

      // ── SECTION 9: SESSION HISTORY PAGE ────────────────────────────────
      h1('9.  Session History  (/sessions)'),

      h2('9.1  Page Header'),
      bullet2('Title', '"Session History"'),
      bullet2('Subtitle', '"Browse, search, and export your past classroom sessions."'),
      bullet2('Top-right button', '"+ Start New Session"'),

      h2('9.2  Filters & Search Bar'),
      bullet2('Search', 'Search by course name or date'),
      bullet2('Course filter', 'Dropdown \u2014 All Courses | CS-401 | CS-301 | CS-201'),
      bullet2('Date range', 'Date picker'),
      bullet2('Engagement filter', '"Below 60% only" checkbox'),
      bullet2('Export Selected', '"Export as CSV" or "Export as PDF" (multi-select)'),

      h2('9.3  Sessions Table'),
      mkTable(
        ['#', 'Date', 'Course', 'Duration', 'Avg Engagement', 'Alerts', 'Privacy', 'Actions'],
        [
          ['1', '14 Jun 2026', 'CS-401 AI & ML', '1h 10m', '81%', '0', '\uD83D\uDD12 Anon', 'View | Export'],
          ['2', '12 Jun 2026', 'CS-301 DSA', '55m', '67%', '1', '\uD83D\uDD12 Anon', 'View | Export'],
          ['3', '10 Jun 2026', 'CS-401 AI & ML', '1h 00m', '72%', '0', '\uD83D\uDD12 Anon', 'View | Export'],
          ['4', '7 Jun 2026', 'CS-201 OOP', '50m', '59%', '2', '\uD83D\uDD12 Anon', 'View | Export'],
          ['5', '5 Jun 2026', 'CS-301 DSA', '1h 05m', '76%', '0', '\uD83D\uDD12 Anon', 'View | Export'],
        ],
        [500, 1200, 1700, 900, 1600, 800, 1100, 1560]
      ),
      p('Below table: "Showing 1\u201310 of 24 sessions. Load more \u2193"'),
      divider(),
      pageBreak(),

      // ── SECTION 10: ADMIN DASHBOARD ──────────────────────────────────────
      h1('10.  Admin Dashboard  (/admin)'),
      p('Accessible only to administrator accounts. Covers system-wide monitoring, user management, policy configuration, and audit logs.'),

      h2('10.1  Page Header'),
      bullet2('Title', '"Admin Control Panel"'),
      bullet2('Subtitle', '"System-wide overview and management for ClassSense."'),

      h2('10.2  System Stats Cards'),
      mkTable(
        ['Card', 'Icon', 'Value', 'Label'],
        [
          ['Total Instructors', '\uD83D\uDC65', '14', 'Registered Instructors'],
          ['Active Sessions Now', '\uD83D\uDFE2', '3', 'Live Sessions Running'],
          ['Classrooms Configured', '\uD83C\uDFEB', '8', 'Camera-Equipped Rooms'],
          ['Audit Events Today', '\uD83D\uDD0D', '42', 'System Events Logged'],
        ],
        [2000, 900, 1500, 3960]
      ),

      h2('10.3  Manage Users'),
      p('Title: "Instructor Accounts"'),
      mkTable(
        ['Name', 'Email', 'Role', 'Status', 'Last Login', 'Actions'],
        [
          ['Dr. Ali Hassan', 'ali.hassan@iqra.edu.pk', 'Instructor', 'Active', '14 Jun 2026', 'Edit | Suspend'],
          ['Ms. Nadia Khan', 'nadia.khan@iqra.edu.pk', 'Instructor', 'Active', '12 Jun 2026', 'Edit | Suspend'],
          ['Mr. Bilal Ahmed', 'bilal.ahmed@iqra.edu.pk', 'Instructor', 'Suspended', '5 May 2026', 'Edit | Reactivate'],
          ['Admin User', 'admin@classsense.edu', 'Admin', 'Active', '14 Jun 2026', 'Edit'],
        ],
        [1700, 2200, 1200, 1100, 1500, 1660]
      ),
      p('Above table: "+ Add New Instructor" button (teal).'),

      h2('10.4  Platform-Wide Analytics'),
      p('Title: "Platform Overview"'),
      bullet2('Total sessions across all instructors', 'Line chart by month'),
      bullet2('Average engagement across all courses', 'Gauge or number card'),
      bullet2('Most active instructors', 'Bar chart \u2014 sessions per instructor'),
      bullet2('Classrooms by utilization', 'Heatmap or table'),

      h2('10.5  Audit Logs'),
      p('Title: "Audit Log"'),
      p('Filters: Date range | Event type | User'),
      mkTable(
        ['Timestamp', 'User', 'Event Type', 'Details'],
        [
          ['14 Jun 2026  09:41', 'ali.hassan', 'Session Export', 'Exported PDF report for CS-401 session'],
          ['14 Jun 2026  08:30', 'admin', 'Config Change', 'Updated retention policy: 90 \u2192 60 days'],
          ['12 Jun 2026  14:20', 'nadia.khan', 'Login', 'Successful login from IP 192.168.1.22'],
          ['10 Jun 2026  11:00', 'admin', 'Model Calibration', 'Triggered recalibration for Room 301 Cam A'],
        ],
        [1800, 1500, 1700, 4360]
      ),

      h2('10.6  Privacy & Retention Policy Settings'),
      p('Title: "Privacy & Data Retention Configuration"'),
      mkTable(
        ['Setting', 'Current Value', 'Options'],
        [
          ['Default Privacy Mode', 'Anonymized (Forced)', 'Anonymized (cannot be disabled)'],
          ['Session Data Retention Period', '90 days', '30 / 60 / 90 / 180 days / Custom'],
          ['Auto-Purge After Retention Period', 'Enabled', 'Enabled / Disabled'],
          ['Raw Video Storage', 'Disabled (always)', 'Cannot be enabled by policy'],
          ['Export Audit Logging', 'Enabled', 'Enabled / Disabled'],
        ],
        [2700, 2000, 3660]
      ),
      p('Save Settings button + confirmation dialog: "Changing retention policy will affect all future session data. Confirm?"'),

      h2('10.7  Model Calibration'),
      p('Title: "AI Model Calibration"'),
      bullet2('Last calibrated', '"Room 301 Cam A \u2014 June 10, 2026  |  Status: \u2705 Calibrated"'),
      bullet2('Button', '"Run Calibration for [Room/Camera]" \u2014 triggers a 30-second test run'),
      bullet2('Results', 'Shows FPS, detection confidence, FER accuracy (placeholder: 87%)'),
      bullet2('Manual override', '"Force full recalibration" link for admin'),
      divider(),
      pageBreak(),

      // ── SECTION 11: SETTINGS ────────────────────────────────────────────
      h1('11.  Settings Page  (/settings)'),

      h2('11.1  Profile Settings'),
      bullet2('Full Name', 'Editable text field'),
      bullet2('Email', 'Read-only (contact admin to change)'),
      bullet2('Department / Institution', 'Editable'),
      bullet2('Profile Picture', 'Upload avatar'),
      bullet2('Save Changes button', 'Teal'),

      h2('11.2  Alert Preferences'),
      bullet2('Default Alert Threshold', 'Slider \u2014 default 60%'),
      bullet2('Alert Delivery', 'In-app only | Email | Both'),
      bullet2('Alert Frequency', '"Notify once per threshold breach" or "Every 5 minutes while below threshold"'),

      h2('11.3  Notification Settings'),
      bullet2('Session complete notification', 'Toggle ON/OFF'),
      bullet2('Report ready notification', 'Toggle ON/OFF'),
      bullet2('Weekly summary email', 'Toggle ON/OFF'),

      h2('11.4  Security'),
      bullet2('Change Password', '"Current Password" + "New Password" + "Confirm" fields'),
      bullet2('MFA', '"Enable Two-Factor Authentication" toggle'),
      bullet2('Active Sessions', 'Table of logged-in sessions with "Log Out All Other Devices" button'),
      divider(),
      pageBreak(),

      // ── SECTION 12: COLORS & TYPOGRAPHY ──────────────────────────────────
      h1('12.  Color Palette & Typography Reference'),
      p('Use this table as the single source of truth for all UI colors.'),

      h2('12.1  Color Palette'),
      mkTable(
        ['Name', 'Hex', 'Use Case'],
        [
          ['Primary Blue (Dark)', '#1A3C6B', 'Headings, sidebar background, navbar background'],
          ['Primary Blue (Mid)', '#1E5F8E', 'Section headings, card borders, active links'],
          ['Teal / CTA', '#2E9E8A', 'Primary buttons, active states, badges, live indicator'],
          ['Teal Light', '#D0F0EB', 'Success banners, card highlights'],
          ['Amber / Warning', '#F5A623', 'Warning alerts, below-threshold indicators'],
          ['Red / Danger', '#D94F4F', 'Engagement drops, error states, end session button'],
          ['Green / Good', '#3DBE7A', 'Positive metrics, pass states, improvements'],
          ['Background (light)', '#F4F8FB', 'Alternate table rows, card backgrounds'],
          ['White', '#FFFFFF', 'Main page background, form fields, cards'],
          ['Grey (border)', '#CCCCCC', 'Table borders, dividers, inactive elements'],
          ['Dark Text', '#1C1C2E', 'Body text, labels'],
          ['Muted Text', '#6B7280', 'Sub-labels, help text, timestamps'],
        ],
        [2200, 1500, 4660]
      ),

      h2('12.2  Typography'),
      mkTable(
        ['Element', 'Font', 'Size', 'Weight', 'Color'],
        [
          ['Page Title (H1)', 'Inter / Arial', '32px', 'Bold', '#1A3C6B'],
          ['Section Heading (H2)', 'Inter / Arial', '24px', 'Semi-bold', '#1E5F8E'],
          ['Card Title (H3)', 'Inter / Arial', '18px', 'Semi-bold', '#2E7D6B'],
          ['Body Text', 'Inter / Arial', '15px', 'Regular', '#1C1C2E'],
          ['Label / Caption', 'Inter / Arial', '13px', 'Regular', '#6B7280'],
          ['Button Text', 'Inter / Arial', '15px', 'Semi-bold', 'White (on filled)'],
          ['Stat Numbers', 'Inter / Arial', '28\u201336px', 'Bold', '#1A3C6B'],
          ['Alert Text', 'Inter / Arial', '14px', 'Regular', '#D94F4F'],
        ],
        [2200, 1500, 1000, 1500, 3160]
      ),

      pageBreak(),

      // ── SECTION 13: ERROR STATES & EMPTY STATES ─────────────────────────
      h1('13.  Error States & Empty States'),
      p('Every page should have defined content for when data is missing, loading, or an error occurs.'),

      h2('13.1  Empty States'),
      mkTable(
        ['Page / Section', 'Empty State Message', 'Action'],
        [
          ['Session History', '"\uD83C\uDFEB No sessions yet. Start your first ClassSense session to see data here."', '"+ Start New Session" button'],
          ['Course Analytics', '"No sessions found for this course in the selected date range."', '"Adjust filters" or "Start a session"'],
          ['Notifications', '"\u2705 You\'re all caught up! No new notifications."', 'None'],
          ['Audit Logs (Admin)', '"No audit events found for the selected filters."', '"Clear filters"'],
          ['Reports', '"No report available for this session. This may be because the session ended without generating one."', '"Generate Report" button'],
        ],
        [2000, 4000, 2360]
      ),

      h2('13.2  Error States'),
      mkTable(
        ['Error', 'Message Shown to User'],
        [
          ['Camera not found', '"\u274C We couldn\'t detect a camera. Please connect a webcam and refresh, or grant camera permissions in your browser settings."'],
          ['Server disconnected', '"\uD83D\uDEA8 Connection to ClassSense analytics server lost. Attempting to reconnect... (Attempt 2/5)"'],
          ['Session data unavailable', '"\u26A0\uFE0F This session\'s data could not be loaded. It may have been purged per your institution\'s retention policy."'],
          ['Export failed', '"Something went wrong while generating your report. Please try again. If the problem persists, contact your administrator."'],
          ['Login failed', '"Incorrect email or password. Please try again. Forgot your password?"'],
          ['MFA code expired', '"Your verification code has expired. Please request a new one."'],
        ],
        [2500, 5860]
      ),
      divider(),
      pageBreak(),

      // ── SECTION 14: MOBILE CONSIDERATIONS ───────────────────────────────
      h1('14.  Mobile / Responsive Considerations'),
      p('ClassSense is primarily used on a laptop or desktop during class, but the dashboard should be usable on a tablet for instructors moving around the room.'),

      bullet2('Navbar', 'Collapses to hamburger menu at \u2264768px. Sidebar becomes a bottom tab bar or slide-in drawer.'),
      bullet2('Stat cards', 'Stack vertically on mobile (1-column grid).'),
      bullet2('Session table', 'Horizontal scroll or condensed card view.'),
      bullet2('Live dashboard', 'Prioritize Engagement Gauge and Attention Breakdown. Charts collapse below the fold. Controls stick to bottom as a fixed bar.'),
      bullet2('Landing page', 'Hero section stacks vertically. Feature cards become single-column. CTA buttons are full-width.'),
      bullet2('Login page', 'Left branding panel hides on mobile. Only the form is shown.'),

      divider(),
      new Paragraph({ spacing: { before: 240, after: 80 }, children: [new TextRun({ text: 'End of Document', bold: true, size: 22, font: 'Arial', color: '888888', italics: true })] }),
      p('ClassSense \u2014 FYDP-1, Fall 2025 \u2014 Iqra University'),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('/mnt/user-data/outputs/ClassSense_Frontend_Content_Guide.docx', buf);
  console.log('Done!');
}).catch(e => { console.error(e); process.exit(1); });