import React, { useRef, useEffect } from 'react';

interface OtpInputBoxesProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  onComplete?: (code: string) => void;
}

export const OtpInputBoxes: React.FC<OtpInputBoxesProps> = ({
  value,
  onChange,
  disabled = false,
  onComplete
}) => {
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);

  const digits = Array.from({ length: 6 }, (_, i) => value[i] || '');

  useEffect(() => {
    // Auto-focus first empty input on mount
    const firstEmptyIndex = digits.findIndex(d => !d);
    const targetIndex = firstEmptyIndex !== -1 ? firstEmptyIndex : 0;
    if (inputsRef.current[targetIndex] && !disabled) {
      inputsRef.current[targetIndex]?.focus();
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>, index: number) => {
    const inputValue = e.target.value;
    const digit = inputValue.replace(/\D/g, '').slice(-1);

    const newDigits = [...digits];
    newDigits[index] = digit;
    const newCombined = newDigits.join('');
    onChange(newCombined);

    if (digit && index < 5) {
      inputsRef.current[index + 1]?.focus();
    }

    if (newCombined.length === 6 && onComplete) {
      onComplete(newCombined);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, index: number) => {
    if (e.key === 'Backspace') {
      if (!digits[index] && index > 0) {
        inputsRef.current[index - 1]?.focus();
        const newDigits = [...digits];
        newDigits[index - 1] = '';
        onChange(newDigits.join(''));
      }
    } else if (e.key === 'ArrowLeft' && index > 0) {
      inputsRef.current[index - 1]?.focus();
    } else if (e.key === 'ArrowRight' && index < 5) {
      inputsRef.current[index + 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text');
    const numericChars = pastedData.replace(/\D/g, '').slice(0, 6);
    
    if (numericChars) {
      onChange(numericChars);
      const nextIndex = Math.min(numericChars.length, 5);
      inputsRef.current[nextIndex]?.focus();
      
      if (numericChars.length === 6 && onComplete) {
        onComplete(numericChars);
      }
    }
  };

  return (
    <div className="flex items-center justify-between gap-2 sm:gap-3 my-4">
      {Array.from({ length: 6 }).map((_, index) => (
        <input
          key={index}
          ref={(el) => (inputsRef.current[index] = el)}
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={1}
          value={digits[index]}
          onChange={(e) => handleChange(e, index)}
          onKeyDown={(e) => handleKeyDown(e, index)}
          onPaste={handlePaste}
          disabled={disabled}
          autoComplete="one-time-code"
          className={`w-11 h-13 sm:w-12 sm:h-14 text-center font-mono text-xl sm:text-2xl font-bold rounded-xl border transition-all duration-200 outline-none ${
            digits[index]
              ? 'border-accent bg-accent/10 text-accent ring-2 ring-accent/30 shadow-sm'
              : 'border-borderColor bg-bgInput text-textPrimary hover:border-textMuted focus:border-accent focus:ring-2 focus:ring-accent/40'
          } disabled:opacity-50 cursor-text`}
        />
      ))}
    </div>
  );
};
