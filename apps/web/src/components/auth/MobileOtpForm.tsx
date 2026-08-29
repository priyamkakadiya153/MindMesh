import React, { useState, useEffect } from 'react';
import { Phone, KeyRound, Loader2, ArrowRight, RefreshCw, AlertCircle, CheckCircle2, Mail, UserPlus, ArrowLeft } from 'lucide-react';
import { useAuth } from '../../features/auth/auth-provider';
import { CountrySelector, getCountryRule } from './CountrySelector';
import { OtpInputBoxes } from './OtpInputBoxes';

interface MobileOtpFormProps {
  onSuccess?: () => void;
  onRegisterLink?: () => void;
}

export const MobileOtpForm: React.FC<MobileOtpFormProps> = ({ onSuccess, onRegisterLink }) => {
  const { sendPhoneOtp, resendPhoneOtp, verifyPhoneOtp } = useAuth();
  
  const [countryCode, setCountryCode] = useState('+91');
  const [nationalNumber, setNationalNumber] = useState('');
  const [otpCode, setOtpCode] = useState('');

  const [maskedEmail, setMaskedEmail] = useState('');
  
  const [step, setStep] = useState<'PHONE' | 'OTP'>('PHONE');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [accountNotFound, setAccountNotFound] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [cooldown, setCooldown] = useState(0);

  const currentRule = getCountryRule(countryCode);

  useEffect(() => {
    let timer: any;
    if (cooldown > 0) {
      timer = setInterval(() => setCooldown((prev) => prev - 1), 1000);
    }
    return () => clearInterval(timer);
  }, [cooldown]);

  const handleCountryCodeChange = (newCode: string) => {
    setCountryCode(newCode);
    const rule = getCountryRule(newCode);
    setNationalNumber((prev) => prev.replace(/\D/g, '').slice(0, rule.maxLength));
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const rawVal = e.target.value;
    const digitsOnly = rawVal.replace(/\D/g, '').slice(0, currentRule.maxLength);
    setNationalNumber(digitsOnly);
  };

  const handlePhoneKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (
      e.key === 'Backspace' ||
      e.key === 'Delete' ||
      e.key === 'Tab' ||
      e.key === 'Escape' ||
      e.key === 'Enter' ||
      e.key === 'ArrowLeft' ||
      e.key === 'ArrowRight' ||
      e.key === 'Home' ||
      e.key === 'End' ||
      e.ctrlKey ||
      e.metaKey
    ) {
      return;
    }
    if (!/^[0-9]$/.test(e.key)) {
      e.preventDefault();
    }
  };

  const handlePhonePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text');
    const digitsOnly = pastedData.replace(/\D/g, '').slice(0, currentRule.maxLength);
    setNationalNumber(digitsOnly);
  };

  const getFullPhoneNumber = (): string => {
    const rawNumber = nationalNumber.trim().replace(/\D/g, '');
    return `${countryCode}${rawNumber}`;
  };

  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    const rawPhoneDigits = nationalNumber.trim().replace(/\D/g, '');
    if (!rawPhoneDigits) {
      setError('Mobile number is required.');
      return;
    }

    if (currentRule.minLength === currentRule.maxLength) {
      if (rawPhoneDigits.length !== currentRule.minLength) {
        setError(`Please enter a valid ${currentRule.minLength}-digit mobile number.`);
        return;
      }
    } else {
      if (rawPhoneDigits.length < currentRule.minLength || rawPhoneDigits.length > currentRule.maxLength) {
        setError(`Please enter a valid mobile number (${currentRule.minLength}-${currentRule.maxLength} digits).`);
        return;
      }
    }

    const fullPhone = getFullPhoneNumber();

    setLoading(true);
    setError(null);
    setAccountNotFound(false);
    setSuccessMsg(null);

    try {
      const res = await sendPhoneOtp(fullPhone);
      setMaskedEmail(res.email_masked);
      setStep('OTP');
      setCooldown(res.resend_cooldown_seconds || 60);
      setSuccessMsg(`Verification code sent to registered email: ${res.email_masked}`);
    } catch (err: any) {
      const msg = err.message || 'Failed to send OTP.';
      if (msg.toLowerCase().includes('no account found') || msg.toLowerCase().includes('not registered')) {
        setAccountNotFound(true);
        setError('No account found associated with this mobile number.');
      } else {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async (codeToVerify?: string) => {
    const code = codeToVerify || otpCode;
    if (!code || code.trim().length !== 6) {
      setError('Please enter the 6-digit numeric verification code.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const fullPhone = getFullPhoneNumber();
      await verifyPhoneOtp(fullPhone, code.trim());
      setSuccessMsg('OTP verified successfully! Redirecting...');
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setError(err.message || 'Invalid verification code.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || loading) return;
    setLoading(true);
    setError(null);
    try {
      const fullPhone = getFullPhoneNumber();
      const res = await resendPhoneOtp(fullPhone);
      setMaskedEmail(res.email_masked);
      setCooldown(res.resend_cooldown_seconds || 60);
      setSuccessMsg(`A new verification code has been dispatched to ${res.email_masked}`);
    } catch (err: any) {
      setError(err.message || 'Failed to resend verification code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* Header Info */}
      <div className="flex items-center gap-2.5 p-3 bg-accent/10 border border-accent/20 rounded-xl text-xs text-textSecondary">
        <Mail className="w-4 h-4 shrink-0 text-accent" />
        <div>
          <span className="font-semibold text-textPrimary block">Mobile Login + Registered Email OTP</span>
          <span>OTP code is sent to your registered email address. No SMS carrier fees required.</span>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="flex flex-col gap-2 p-3 bg-dangerBg border border-dangerBorder rounded-xl text-dangerText text-xs">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span className="font-medium">{error}</span>
          </div>
          {accountNotFound && onRegisterLink && (
            <button
              type="button"
              onClick={onRegisterLink}
              className="mt-1 flex items-center justify-center gap-1.5 w-full py-2 bg-accent hover:bg-accentHover text-white font-semibold rounded-lg text-xs transition-colors shadow-sm"
            >
              <UserPlus className="w-3.5 h-3.5" />
              Create Account Now
            </button>
          )}
        </div>
      )}

      {/* Success Alert */}
      {successMsg && !error && (
        <div className="flex items-center gap-2 p-3 bg-successBg border border-successBorder rounded-xl text-successText text-xs">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span className="font-medium">{successMsg}</span>
        </div>
      )}

      {step === 'PHONE' ? (
        <form onSubmit={handleSendOtp} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5">
              Mobile Number
            </label>
            <div className="flex items-stretch rounded-lg shadow-sm">
              <CountrySelector
                value={countryCode}
                onChange={handleCountryCodeChange}
                disabled={loading}
              />
              <div className="relative flex-1">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                <input
                  type="tel"
                  inputMode="numeric"
                  maxLength={currentRule.maxLength}
                  value={nationalNumber}
                  onChange={handlePhoneChange}
                  onKeyDown={handlePhoneKeyDown}
                  onPaste={handlePhonePaste}
                  placeholder={currentRule.minLength === 10 ? '9876543210' : '123456789'}


                  disabled={loading}
                  className="w-full h-full bg-bgInput border border-l-0 border-borderColor rounded-r-lg pl-9 pr-4 py-2.5 text-sm text-textPrimary placeholder-textMuted outline-none focus:border-accent transition-colors"
                />
              </div>
            </div>
            <p className="text-[11px] text-textMuted mt-1.5">
              Enter your registered phone number. OTP will be sent to your email.
            </p>
          </div>

          <button
            type="submit"
            disabled={loading || !nationalNumber.trim()}
            className="w-full flex items-center justify-center gap-2 bg-accent hover:bg-accentHover disabled:opacity-50 text-white font-semibold py-3 rounded-lg text-sm transition-all shadow-lg shadow-accent/25"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Sending OTP...
              </>
            ) : (
              <>
                Send Verification Code
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </form>
      ) : (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-textMuted">
              Enter 6-Digit OTP
            </span>
            <button
              type="button"
              onClick={() => {
                setStep('PHONE');
                setError(null);
                setSuccessMsg(null);
              }}
              className="text-xs text-accent hover:underline flex items-center gap-1 font-medium"
            >
              <ArrowLeft className="w-3 h-3" />
              Change Number ({getFullPhoneNumber()})
            </button>
          </div>

          {/* Masked Email Badge */}
          {maskedEmail && (
            <div className="p-2.5 bg-bgTertiary border border-borderColor rounded-lg text-center text-xs text-textSecondary">
              Code sent to: <span className="font-mono font-semibold text-textPrimary">{maskedEmail}</span>
            </div>
          )}

          {/* 6 Individual OTP Boxes */}
          <OtpInputBoxes
            value={otpCode}
            onChange={(val) => setOtpCode(val)}
            disabled={loading}
            onComplete={(code) => handleVerifyOtp(code)}
          />

          <div className="flex items-center justify-between text-xs pt-1">
            <button
              type="button"
              onClick={handleResend}
              disabled={cooldown > 0 || loading}
              className="text-textMuted hover:text-accent disabled:opacity-50 flex items-center gap-1.5 font-medium transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              {cooldown > 0 ? `Resend code in ${cooldown}s` : 'Resend Code'}
            </button>

            <span className="text-textMuted text-[11px]">Expires in 5 minutes</span>
          </div>

          <button
            type="button"
            onClick={() => handleVerifyOtp()}
            disabled={loading || otpCode.length !== 6}
            className="w-full flex items-center justify-center gap-2 bg-accent hover:bg-accentHover disabled:opacity-50 text-white font-semibold py-3 rounded-lg text-sm transition-all shadow-lg shadow-accent/25"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Verifying OTP...
              </>
            ) : (
              <>
                <KeyRound className="w-4 h-4" />
                Verify & Sign In
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
};
