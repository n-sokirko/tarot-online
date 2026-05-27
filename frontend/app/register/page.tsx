'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { useTranslations } from 'next-intl';
import { saveTokens } from '@/lib/auth';
import GoogleButton from '@/components/auth/GoogleButton';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export default function RegisterPage() {
  const t = useTranslations('auth');
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, display_name: displayName }),
      });
      if (res.status === 400) {
        const data = await res.json() as Record<string, string[]>;
        const emailError = data.email?.[0];
        setError(emailError?.includes('already') || emailError?.includes('exists')
          ? t('error_exists')
          : t('error_generic'));
        return;
      }
      if (!res.ok) { setError(t('error_generic')); return; }
      const data = await res.json() as { access: string; refresh: string };
      saveTokens(data.access, data.refresh);
      router.push('/');
      router.refresh();
    } catch {
      setError(t('error_generic'));
    } finally {
      setLoading(false);
    }
  }, [email, password, displayName, router, t]);

  return (
    <main
      className="min-h-screen flex flex-col items-center justify-center px-4"
      style={{ background: 'radial-gradient(ellipse at 50% 0%, rgba(28,24,64,0.8) 0%, #0b0b1f 60%)' }}
    >
      <motion.div
        className="w-full max-w-sm flex flex-col gap-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="font-serif text-3xl text-center" style={{ color: '#d4af37' }}>
          {t('register_title')}
        </h1>

        <form onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-4">
          <input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder={t('display_name')}
            className="w-full px-4 py-3 rounded-xl font-sans text-sm outline-none"
            style={{
              border: '1px solid rgba(212,175,55,0.3)',
              color: 'rgba(201,194,224,0.9)',
              background: 'rgba(212,175,55,0.04)',
            }}
          />
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={t('email')}
            required
            className="w-full px-4 py-3 rounded-xl font-sans text-sm outline-none"
            style={{
              border: '1px solid rgba(212,175,55,0.3)',
              color: 'rgba(201,194,224,0.9)',
              background: 'rgba(212,175,55,0.04)',
            }}
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder={t('password')}
            required
            className="w-full px-4 py-3 rounded-xl font-sans text-sm outline-none"
            style={{
              border: '1px solid rgba(212,175,55,0.3)',
              color: 'rgba(201,194,224,0.9)',
              background: 'rgba(212,175,55,0.04)',
            }}
          />

          {error && (
            <p className="text-xs text-center" style={{ color: 'rgba(200,80,80,0.9)' }}>
              {error}
            </p>
          )}

          <motion.button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-full font-serif text-sm tracking-widest uppercase"
            style={{
              background: loading ? 'rgba(212,175,55,0.05)' : 'rgba(212,175,55,0.1)',
              border: '1px solid #d4af37',
              color: '#d4af37',
              letterSpacing: '0.15em',
              opacity: loading ? 0.6 : 1,
            }}
            whileHover={loading ? {} : { backgroundColor: 'rgba(212,175,55,0.2)' }}
          >
            {loading ? '...' : t('register_btn')}
          </motion.button>
        </form>

        {/* Divider */}
        <div className="flex items-center gap-3">
          <div className="flex-1 h-px" style={{ background: 'rgba(212,175,55,0.15)' }} />
          <span className="text-xs font-sans" style={{ color: 'rgba(201,194,224,0.3)', letterSpacing: '0.1em' }}>
            {t('or')}
          </span>
          <div className="flex-1 h-px" style={{ background: 'rgba(212,175,55,0.15)' }} />
        </div>

        <GoogleButton onError={setError} />

        <p className="text-xs text-center" style={{ color: 'rgba(201,194,224,0.4)' }}>
          <Link href="/login" style={{ color: 'rgba(212,175,55,0.6)' }}>
            {t('login_link')}
          </Link>
        </p>
      </motion.div>
    </main>
  );
}
