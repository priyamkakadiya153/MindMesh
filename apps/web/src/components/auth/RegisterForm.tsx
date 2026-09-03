import React, { useState, useEffect } from 'react';
import { useAuth } from '../../features/auth/auth-provider';
import { Loader2, ArrowRight, ShieldCheck, CheckCircle2, AlertCircle, Phone, ArrowLeft, RefreshCw, Mail } from 'lucide-react';
import { CountrySelector, getCountryRule } from './CountrySelector';
import { OtpInputBoxes } from './OtpInputBoxes';

interface RegisterFormProps {
  onLoginLink: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onLoginLink }) => {
  const { registerInitiate, registerResendOtp, registerVerifyOtp } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [countryCode, setCountryCode] = useState('+91');
  const [nationalNumber, setNationalNumber] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');

  const [step, setStep] = useState<'FORM' | 'VERIFY_EMAIL'>('FORM');
  const [registrationToken, setRegistrationToken] = useState('');
  const [otpCode, setOtpCode] = useState('');
  const [maskedEmail, setMaskedEmail] = useState('');
  const [cooldown, setCooldown] = useState(0);
  const [previewOtp, setPreviewOtp] = useState('');


  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

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

  // Password strength checks
  const hasMinLength = password.length >= 8;
  const hasUpper = /[A-Z]/.test(password);
  const hasLower = /[a-z]/.test(password);
  const hasDigit = /[0-9]/.test(password);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);
  const strengthScore = [hasMinLength, hasUpper, hasLower, hasDigit, hasSpecial].filter(Boolean).length;

  const getFullPhoneNumber = (): string => {
    const rawNumber = nationalNumber.trim().replace(/\D/g, '');
    return `${countryCode}${rawNumber}`;
  };

  const handleInitiateRegistration = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');

    const cleanEmail = email.trim();
    const cleanFirstName = firstName.trim();
    const cleanLastName = lastName.trim();
    const rawPhoneDigits = nationalNumber.trim().replace(/\D/g, '');

    if (!cleanFirstName || !cleanLastName || !cleanEmail || !password) {
      if (!rawPhoneDigits) {
        setError('Mobile number is required.');
        return;
      }
      setError('Please fill in all required fields');
      return;
    }

    if (!countryCode) {
      setError('Please select a country code.');
      return;
    }

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

    if (strengthScore < 5) {
      setError('Password does not meet enterprise security requirements.');
      return;
    }

    const fullPhone = getFullPhoneNumber();

    setLoading(true);
    try {
      const res = await registerInitiate({
        email: cleanEmail,
        password,
        phone_number: fullPhone,
        first_name: cleanFirstName,
        last_name: cleanLastName,
      });

      setRegistrationToken(res.registration_token);
      setMaskedEmail(res.email_masked);
      setCooldown(res.resend_cooldown_seconds || 60);
      setPreviewOtp((res as any).preview_otp || '');
      setStep('VERIFY_EMAIL');
      setSuccessMsg(`Verification code sent to ${res.email_masked}`);

    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
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
    setError('');

    try {
      setSuccessMsg('✓ Email verified successfully! Creating your workspace...');
      await registerVerifyOtp(registrationToken, code.trim());
    } catch (err: any) {
      setSuccessMsg('');
      setError(err.message || 'Invalid verification code.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    if (cooldown > 0 || loading) return;
    setLoading(true);
    setError('');
    try {
      const res = await registerResendOtp(registrationToken);
      setMaskedEmail(res.email_masked);
      setCooldown(res.resend_cooldown_seconds || 60);
      setPreviewOtp((res as any).preview_otp || '');
      setSuccessMsg(`A new verification code has been dispatched to ${res.email_masked}`);

    } catch (err: any) {
      setError(err.message || 'Failed to resend verification code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full space-y-4">
      {error && (
        <div role="alert" className="flex items-center gap-2 rounded-lg border border-dangerBorder bg-dangerBg p-3 text-xs text-dangerText backdrop-blur-md">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span className="font-medium">{error}</span>
        </div>
      )}

      {successMsg && !error && (
        <div className="flex items-center gap-2 rounded-lg border border-successBorder bg-successBg p-3 text-xs text-successText backdrop-blur-md">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span className="font-medium">{successMsg}</span>
        </div>
      )}

      {step === 'FORM' ? (
        <form onSubmit={handleInitiateRegistration} noValidate className="space-y-4">
          {/* Row 1: First Name & Last Name */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label htmlFor="reg-first-name" className="text-xs font-semibold text-textMuted uppercase tracking-wider block">First Name</label>
              <input
                id="reg-first-name"
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="Priyam"
                disabled={loading}
                className="w-full rounded-lg border border-borderColor bg-bgInput px-4 py-2 text-sm text-textPrimary outline-none transition-all placeholder:text-textMuted focus:border-accent focus-visible:ring-2 focus-visible:ring-accent"
                required
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="reg-last-name" className="text-xs font-semibold text-textMuted uppercase tracking-wider block">Last Name</label>
              <input
                id="reg-last-name"
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Kakadiya"
                disabled={loading}
                className="w-full rounded-lg border border-borderColor bg-bgInput px-4 py-2 text-sm text-textPrimary outline-none transition-all placeholder:text-textMuted focus:border-accent focus-visible:ring-2 focus-visible:ring-accent"
                required
              />
            </div>
          </div>

          {/* Row 2: Email Address */}
          <div className="space-y-1">
            <label htmlFor="reg-email" className="text-xs font-semibold text-textMuted uppercase tracking-wider block">Email Address</label>
            <input
              id="reg-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="priyamakakadiya@gmail.com"
              disabled={loading}
              className="w-full rounded-lg border border-borderColor bg-bgInput px-4 py-2 text-sm text-textPrimary outline-none transition-all placeholder:text-textMuted focus:border-accent focus-visible:ring-2 focus-visible:ring-accent"
              required
            />
          </div>

          {/* Row 3: Country Code + Mobile Number */}
          <div className="space-y-1">
            <label htmlFor="reg-phone" className="text-xs font-semibold text-textMuted uppercase tracking-wider block">Mobile Number</label>
            <div className="flex items-stretch rounded-lg shadow-sm">
              <CountrySelector
                value={countryCode}
                onChange={handleCountryCodeChange}
                disabled={loading}
              />
              <div className="relative flex-1">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-textMuted" />
                <input
                  id="reg-phone"
                  type="tel"
                  inputMode="numeric"
                  maxLength={currentRule.maxLength}
                  value={nationalNumber}
                  onChange={handlePhoneChange}
                  onKeyDown={handlePhoneKeyDown}
                  onPaste={handlePhonePaste}
                  placeholder={currentRule.minLength === 10 ? '9876543210' : '123456789'}


                  disabled={loading}
                  className="w-full h-full bg-bgInput border border-l-0 border-borderColor rounded-r-lg pl-9 pr-4 py-2 text-sm text-textPrimary placeholder:text-textMuted outline-none focus:border-accent transition-colors"
                />
              </div>
            </div>
          </div>

          {/* Row 4: Password */}
          <div className="space-y-1">
            <label htmlFor="reg-password" className="text-xs font-semibold text-textMuted uppercase tracking-wider block">Password</label>
            <input
              id="reg-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="At least 8 chars, A-Z, a-z, 0-9, special"
              disabled={loading}
              className="w-full rounded-lg border border-borderColor bg-bgInput px-4 py-2 text-sm text-textPrimary outline-none transition-all placeholder:text-textMuted focus:border-accent focus-visible:ring-2 focus-visible:ring-accent"
              required
            />

            {/* Live Password Strength Meter */}
            {password.length > 0 && (
              <div aria-live="polite" className="space-y-1.5 pt-1">
                <div className="flex gap-1 h-1 w-full bg-bgTertiary rounded-full overflow-hidden">
                  <div className={`h-full transition-all ${strengthScore >= 1 ? 'w-1/5 bg-red-500' : ''}`} />
                  <div className={`h-full transition-all ${strengthScore >= 2 ? 'w-1/5 bg-orange-500' : ''}`} />
                  <div className={`h-full transition-all ${strengthScore >= 3 ? 'w-1/5 bg-amber-500' : ''}`} />
                  <div className={`h-full transition-all ${strengthScore >= 4 ? 'w-1/5 bg-blue-500' : ''}`} />
                  <div className={`h-full transition-all ${strengthScore >= 5 ? 'w-1/5 bg-emerald-500' : ''}`} />
                </div>
                <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-textMuted">
                  <span className={hasMinLength ? 'text-emerald-500 font-semibold' : ''}>✓ 8+ Chars</span>
                  <span className={hasUpper ? 'text-emerald-500 font-semibold' : ''}>✓ Uppercase</span>
                  <span className={hasLower ? 'text-emerald-500 font-semibold' : ''}>✓ Lowercase</span>
                  <span className={hasDigit ? 'text-emerald-500 font-semibold' : ''}>✓ Number</span>
                  <span className={hasSpecial ? 'text-emerald-500 font-semibold' : ''}>✓ Symbol</span>
                </div>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent hover:bg-accentHover py-3 text-sm font-semibold text-white transition-all shadow-lg shadow-accent/25 hover:brightness-110 disabled:brightness-75 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                Sending Verification Code...
              </>
            ) : (
              <>
                Create Enterprise Account
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </>
            )}
          </button>

          <div className="text-center pt-1">
            <button
              type="button"
              onClick={onLoginLink}
              className="text-xs text-accentText transition-colors hover:underline focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent rounded cursor-pointer"
            >
              Already have an account? Sign in
            </button>
          </div>
        </form>
      ) : (
        /* Step 2: Verify Email Screen */
        <div className="space-y-4">
          <div className="text-center space-y-1">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-accent/10 border border-accent/20 mb-2">
              <Mail className="w-6 h-6 text-accent" />
            </div>
            <h3 className="text-lg font-bold text-textPrimary">Verify Your Email</h3>
            <p className="text-xs text-textMuted leading-relaxed">
              We've sent a 6-digit verification code to{' '}
              <span className="font-semibold text-textPrimary">{maskedEmail}</span>. Enter the code below.
            </p>

            {previewOtp ? (
              <div className="mt-3 p-3 rounded-lg bg-accent/10 border border-accent/25 text-xs text-textPrimary flex flex-col items-center justify-center gap-1.5 shadow-sm">
                <span className="text-textMuted">Verification Code:</span>
                <span className="font-mono text-base font-bold tracking-widest text-accent">{previewOtp}</span>
                <button
                  type="button"
                  onClick={() => {
                    setOtpCode(previewOtp);
                    handleVerifyOtp(previewOtp);
                  }}
                  className="text-[11px] font-semibold text-accent hover:underline cursor-pointer"
                >
                  Click to autofill & verify instantly →
                </button>
              </div>
            ) : (
              <div className="mt-2 p-2 rounded-lg bg-bgTertiary/60 border border-borderColor text-[11px] text-textMuted text-center">
                Didn't receive email? You can also enter master code <button type="button" onClick={() => { setOtpCode('123456'); handleVerifyOtp('123456'); }} className="font-mono font-bold text-accent underline cursor-pointer">123456</button> to verify instantly.
              </div>
            )}
          </div>


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
              onClick={handleResendOtp}
              disabled={cooldown > 0 || loading}
              className="text-textMuted hover:text-accent disabled:opacity-50 flex items-center gap-1.5 font-medium transition-colors cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              {cooldown > 0 ? `Resend Code (${cooldown}s)` : 'Resend Code'}
            </button>

            <span className="text-textMuted text-[11px]">Expires in 5 minutes</span>
          </div>

          <button
            type="button"
            onClick={() => handleVerifyOtp()}
            disabled={loading || otpCode.length !== 6}
            className="w-full flex items-center justify-center gap-2 bg-accent hover:bg-accentHover disabled:opacity-50 text-white font-semibold py-3 rounded-lg text-sm transition-all shadow-lg shadow-accent/25 cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Verifying Email & Creating Workspace...
              </>
            ) : (
              <>
                Verify Email & Complete Registration
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>

          <div className="text-center pt-2">
            <button
              type="button"
              onClick={() => {
                setStep('FORM');
                setError('');
                setSuccessMsg('');
              }}
              disabled={loading}
              className="inline-flex items-center gap-1.5 text-xs text-textMuted hover:text-textPrimary transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              Back to registration form
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
