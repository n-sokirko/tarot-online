'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { GoogleLogin, GoogleOAuthProvider, type CredentialResponse } from '@react-oauth/google';
import { saveTokens } from '@/lib/auth';
import { useAuth } from '@/lib/auth-context';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? '';

interface GoogleButtonProps {
  onError?: (msg: string) => void;
}

function GoogleLoginInner({ onError }: GoogleButtonProps) {
  const router = useRouter();
  const { refetch } = useAuth();

  const handleSuccess = useCallback(async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) return;
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/google/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential: credentialResponse.credential }),
      });
      if (!res.ok) {
        onError?.('Google sign-in failed. Please try again.');
        return;
      }
      const data = await res.json() as { access: string; refresh: string };
      saveTokens(data.access, data.refresh);
      await refetch();
      router.push('/');
    } catch {
      onError?.('Google sign-in failed. Please try again.');
    }
  }, [router, onError, refetch]);

  return (
    <div className="flex justify-center">
      <GoogleLogin
        onSuccess={(cr) => void handleSuccess(cr)}
        onError={() => onError?.('Google sign-in failed. Please try again.')}
        theme="filled_black"
        shape="pill"
        size="large"
        text="continue_with"
      />
    </div>
  );
}

/**
 * Google Sign-In — rendered client-only (no SSR).
 *
 * GoogleOAuthProvider injects a <script> tag into <head>. When server-rendered,
 * this confuses React's hydration reconciler in Next.js 14 App Router and causes
 * "In HTML, <script> cannot be a child of <html>" errors. The fix: never render
 * this component on the server — the parent must import it via dynamic({ ssr: false }).
 *
 * If NEXT_PUBLIC_GOOGLE_CLIENT_ID is not configured, renders nothing (graceful degradation).
 */
export default function GoogleButton({ onError }: GoogleButtonProps) {
  if (!GOOGLE_CLIENT_ID) return null;

  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <GoogleLoginInner onError={onError} />
    </GoogleOAuthProvider>
  );
}
