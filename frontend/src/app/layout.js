import './globals.css';
import { LoadingProvider } from './context/LoadingContext';
import { TransitionProvider } from './context/TransitionContext';

export const metadata = {
  title: 'ClassSense — Classroom Engagement Monitoring',
  description: 'AI-powered real-time student engagement and emotion monitoring system for university instructors.',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="bg-black text-white antialiased font-sans" suppressHydrationWarning>
        <LoadingProvider>
          <TransitionProvider>
            {children}
          </TransitionProvider>
        </LoadingProvider>
      </body>
    </html>
  );
}