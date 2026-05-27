'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { GoogleLogin, GoogleOAuthProvider, type CredentialResponse } from '@react-oauth/google';
import { saveTokens } from '@/lib/auth';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
// Read once at module level so the value is stable and doesn't change on re-renders
const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? '';

interface GoogleButtonProps {
  onError?: (msg: string) => void;
}

function GoogleLoginInner({ onError }: GoogleButtonProps) {
  const router = useRouter();

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
      router.push('/');
      router.refresh();
    } catch {
      onError?.('Google sign-in failed. Please try again.');
    }
  }, [router, onError]);

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
 * Self-contained Google Sign-In button.
 * GoogleOAuthProvider is scoped here so its <script> tag is only rendered
 * by this client component — avoids the root-layout hydration mismatch.
 */
export default function GoogleButton({ onError }: GoogleButtonProps) {
  return (
    <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <GoogleLoginInner onError={onError} />
    </GoogleOAuthProvider>
  );
}
