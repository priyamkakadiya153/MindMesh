import React, { useState } from 'react';
import { X, Mail, KeyRound, CheckCircle2, AlertCircle, Loader2, Lock } from 'lucide-react';
import { requestPasswordReset, resetPasswordWithToken } from '../../features/auth/api';

interface ForgotPasswordModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ForgotPasswordModal: React.FC<ForgotPasswordModalProps> = ({ isOpen, onClose }) => {
  const [step, setStep] = useState<'REQUEST' | 'RESET'>('REQUEST');
  const [email, setEmail] = useState('');
  const [tokenOrCode, setTokenOrCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      await requestPasswordReset(email);
      setMessage('Password reset instructions have been dispatched to your email.');
      setStep('RESET');
    } catch (err: any) {
      setError(err.message || 'Failed to request password reset.');
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    setLoading(true);
    setError(null);

    try {
      await resetPasswordWithToken(tokenOrCode, newPassword);
      setMessage('Password reset successfully! You may now sign in.');
      setTimeout(() => {
        onClose();
        setStep('REQUEST');
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Failed to reset password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-bgOverlay backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-bgDialog border border-borderColor text-textPrimary rounded-xl shadow-2xl p-6 space-y-5">
        <div className="flex items-center justify-between border-b border-borderColor pb-4">
          <div className="flex items-center gap-2 text-accentText font-semibold text-lg">
            <Lock className="w-5 h-5" />
            <span>Reset Password</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-textMuted hover:text-textPrimary hover:bg-bgHover transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-3 bg-dangerBg border border-dangerBorder rounded-lg text-dangerText text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {message && (
          <div className="flex items-center gap-2 p-3 bg-successBg border border-successBorder rounded-lg text-successText text-sm">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{message}</span>
          </div>
        )}

        {step === 'REQUEST' ? (
          <form onSubmit={handleRequestReset} className="space-y-4">
            <p className="text-sm text-textSecondary">
              Enter your registered email address and we will send you a password reset code or link.
            </p>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="user@example.com"
                  required
                  className="w-full bg-bgInput border border-borderColor rounded-lg pl-9 pr-4 py-2.5 text-sm text-textPrimary placeholder:text-textMuted focus:outline-none focus:border-accent transition-colors"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm text-textSecondary hover:text-textPrimary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-2 bg-accent hover:bg-accentHover text-white px-5 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-all shadow-lg shadow-accent/20"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Send Reset Link'}
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleExecuteReset} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5">
                Verification Code / Token
              </label>
              <div className="relative">
                <KeyRound className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                <input
                  type="text"
                  value={tokenOrCode}
                  onChange={(e) => setTokenOrCode(e.target.value)}
                  placeholder="Enter code or token"
                  required
                  className="w-full bg-bgInput border border-borderColor rounded-lg pl-9 pr-4 py-2.5 text-sm text-textPrimary placeholder:text-textMuted focus:outline-none focus:border-accent transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5">
                New Password
              </label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="At least 8 chars, uppercase, digit, special"
                required
                className="w-full bg-bgInput border border-borderColor rounded-lg px-4 py-2.5 text-sm text-textPrimary placeholder:text-textMuted focus:outline-none focus:border-accent transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5">
                Confirm Password
              </label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter new password"
                required
                className="w-full bg-bgInput border border-borderColor rounded-lg px-4 py-2.5 text-sm text-textPrimary placeholder:text-textMuted focus:outline-none focus:border-accent transition-colors"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setStep('REQUEST')}
                className="px-4 py-2 text-sm text-textSecondary hover:text-textPrimary"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex items-center gap-2 bg-accent hover:bg-accentHover text-white px-5 py-2 rounded-lg text-sm font-medium disabled:opacity-50 transition-all shadow-lg shadow-accent/20"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Set New Password'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
