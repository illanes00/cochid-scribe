import type { Metadata } from 'next';
import '@/styles/globals.css';
import { AuthProvider } from '@/lib/auth';

export const metadata: Metadata = {
  title: 'Scribe - Academic Writing Platform',
  description:
    'Write, edit and compile academic documents with claim verification',
  alternates: {
    canonical: 'https://scribe.illanes00.cl',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="es">
      <head>
        <link rel="privacy-policy" href="https://scribe.illanes00.cl/privacy" />
        <link
          rel="terms-of-service"
          href="https://scribe.illanes00.cl/terms"
        />
      </head>
      <body className="min-h-screen">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
