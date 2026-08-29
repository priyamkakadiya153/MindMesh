import React, { useState } from 'react';
import { useAuth } from '../../features/auth/auth-provider';
import { Loader2, ArrowRight, Mail, Phone, Lock } from 'lucide-react';
import { MobileOtpForm } from './MobileOtpForm';
import { ForgotPasswordModal } from './ForgotPasswordModal';

interface LoginFormProps {
  onRegisterLink: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onRegisterLink }) => {
  const { login } = useAuth();
  const [authMethod, setAuthMethod] = useState<'EMAIL' | 'MOBILE'>('EMAIL');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [forgotModalOpen, setForgotModalOpen] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }
    setError('');
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.message || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      {/* Auth Method Tabs */}
      <div role="tablist" aria-label="Authentication Method" className="grid grid-cols-2 p-1 bg-bgTertiary border border-borderColor rounded-xl">
        <button
          type="button"
          role="tab"
          aria-selected={authMethod === 'EMAIL'}
          onClick={() => { setAuthMethod('EMAIL'); setError(''); }}
          className={`flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
            authMethod === 'EMAIL'
              ? 'bg-accent text-white shadow-md shadow-accent/30'
              : 'text-textSecondary hover:text-textPrimary'
          }`}
        >
          <Mail className="w-3.5 h-3.5" aria-hidden="true" /> Email & Password
        </button>

        <button
          type="button"
          role="tab"
          aria-selected={authMethod === 'MOBILE'}
          onClick={() => { setAuthMethod('MOBILE'); setError(''); }}
          className={`flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent ${
            authMethod === 'MOBILE'
              ? 'bg-accent text-white shadow-md shadow-accent/30'
              : 'text-textSecondary hover:text-textPrimary'
          }`}
        >
          <Phone className="w-3.5 h-3.5" aria-hidden="true" /> Mobile OTP
        </button>
      </div>

      {authMethod === 'EMAIL' ? (
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div role="alert" className="rounded-lg border border-dangerBorder bg-dangerBg p-3 text-xs text-dangerText backdrop-blur-md">
              {error}
            </div>
          )}

          <div className="space-y-1">
            <label htmlFor="login-email-input" className="text-xs font-semibold text-textMuted uppercase tracking-wider block">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" aria-hidden="true" />
              <input
                id="login-email-input"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@mindmesh.com"
                className="w-full rounded-lg border border-borderColor bg-bgInput pl-9 pr-4 py-2.5 text-sm text-textPrimary outline-none transition-all placeholder:text-textMuted focus:border-accent focus:ring-1 focus:ring-accent focus-visible:ring-2 focus-visible:ring-accent"
                required
              />
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex justify-between items-center">
              <label htmlFor="login-password-input" className="text-xs font-semibold text-textMuted uppercase tracking-wider">Password</label>
              <button
                type="button"
                onClick={() => setForgotModalOpen(true)}
                className="text-xs text-accentText hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent rounded"
              >
                Forgot password?
              </button>
            </div>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" aria-hidden="true" />
              <input
                id="login-password-input"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-borderColor bg-bgInput pl-9 pr-4 py-2.5 text-sm text-textPrimary outline-none transition-all placeholder:text-textMuted focus:border-accent focus:ring-1 focus:ring-accent focus-visible:ring-2 focus-visible:ring-accent"
                required
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-1">
            <label className="flex items-center gap-2 text-xs text-textSecondary cursor-pointer select-none">
              <input
                type="checkbox"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                className="rounded border-borderColor bg-bgInput text-accent focus:ring-2 focus:ring-accent"
              />
              Remember this device
            </label>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent hover:bg-accentHover py-3 text-sm font-semibold text-white transition-all shadow-lg shadow-accent/25 hover:brightness-110 disabled:brightness-75 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                Authenticating...
              </>
            ) : (
              <>
                Sign In
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </>
            )}
          </button>

          <div className="text-center pt-2">
            <button
              type="button"
              onClick={onRegisterLink}
              className="text-xs text-accentText transition-colors hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent rounded"
            >
              Don't have an account? Create an Account
            </button>
          </div>
        </form>
      ) : (
        <div className="space-y-4">
          <MobileOtpForm onRegisterLink={onRegisterLink} />
          <div className="text-center pt-2">
            <button
              type="button"
              onClick={onRegisterLink}
              className="text-xs text-accentText transition-colors hover:underline"
            >
              Don't have an account? Create an Account
            </button>
          </div>
        </div>
      )}

      <ForgotPasswordModal
        isOpen={forgotModalOpen}
        onClose={() => setForgotModalOpen(false)}
      />
    </div>
  );
};
