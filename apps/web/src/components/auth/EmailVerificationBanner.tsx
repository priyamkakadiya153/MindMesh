import React, { useState } from 'react';
import { Mail, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';
import { useAuth } from '../../features/auth/auth-provider';
import { sendEmailVerification, verifyEmailToken } from '../../features/auth/api';

export const EmailVerificationBanner: React.FC = () => {
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [tokenInput, setTokenInput] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!user || user.is_verified) return null;

  const handleSendVerification = async () => {
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const res = await sendEmailVerification();
      setMessage('Verification email sent! Check your inbox.');
      if (res.dev_token) {
        console.log('[DEV EMAIL TOKEN]', res.dev_token);
      }
      setShowModal(true);
    } catch (err: any) {
      setError(err.message || 'Failed to send verification email.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await verifyEmailToken(tokenInput.trim());
      setMessage('Email verified successfully!');
      setTimeout(() => {
        setShowModal(false);
        refreshUser();
      }, 1500);
    } catch (err: any) {
      setError(err.message || 'Invalid or expired token.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div role="status" aria-live="polite" className="w-full bg-amber-500/10 border-b border-amber-500/20 px-4 py-2.5 flex items-center justify-between text-xs text-amber-600 dark:text-amber-200">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" aria-hidden="true" />
          <span>Your email (<strong>{user.email}</strong>) is not verified yet. Please verify for full security access.</span>
        </div>
        <button
          type="button"
          onClick={handleSendVerification}
          disabled={loading}
          title="Resend verification email or enter token"
          aria-label="Resend verification email or enter token"
          className="flex items-center gap-1.5 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/40 text-amber-700 dark:text-amber-100 px-3 py-1 rounded font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-500"
        >
          {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" /> : <Mail className="w-3.5 h-3.5" aria-hidden="true" />}
          Resend / Enter Token
        </button>
      </div>

      {showModal && (
        <div 
          role="dialog"
          aria-modal="true"
          aria-labelledby="verify-email-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-bgOverlay backdrop-blur-sm p-4 animate-in fade-in duration-150"
        >
          <div className="w-full max-w-sm bg-bgDialog border border-borderColor rounded-xl p-5 space-y-4 shadow-2xl">
            <h3 id="verify-email-title" className="text-base font-semibold text-textPrimary flex items-center gap-2">
              <Mail className="w-5 h-5 text-accentText" aria-hidden="true" />
              Verify Email Address
            </h3>

            {message && (
              <div role="status" aria-live="polite" className="p-2.5 bg-successBg border border-successBorder rounded text-successText text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-successText" aria-hidden="true" />
                <span>{message}</span>
              </div>
            )}

            {error && (
              <div role="alert" className="p-2.5 bg-dangerBg border border-dangerBorder rounded text-dangerText text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleVerify} className="space-y-3">
              <div>
                <label htmlFor="verification-token-input" className="block text-xs font-medium text-textMuted mb-1">
                  Enter Verification Code / Token
                </label>
                <input
                  id="verification-token-input"
                  type="text"
                  value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                  placeholder="Paste token or code"
                  required
                  className="w-full bg-bgInput border border-borderColor rounded-lg px-3 py-2 text-sm text-textPrimary focus:outline-none focus:border-accent focus-visible:ring-2 focus-visible:ring-accent"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-3 py-1.5 text-xs text-textMuted hover:text-textPrimary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent rounded"
                >
                  Close
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-accent hover:bg-accentHover text-white px-4 py-1.5 rounded-lg text-xs font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                >
                  {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" aria-hidden="true" /> : 'Confirm Verification'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  );
};
