import React, { useState } from 'react';
import { useAuth } from '../../features/auth/auth-provider';
import { useNavigationStore } from '../../features/navigation/store';
import { updateProfile } from '../../features/auth/api';
import { User, Mail, ShieldCheck, Phone, CheckCircle2, AlertCircle, Loader2, Camera, Globe, Clock, Moon } from 'lucide-react';

const AVATAR_PRESETS = [
  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80',
  'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=150&q=80',
  'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=150&q=80',
  'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=150&q=80'
];

export const ProfileSettingsPage: React.FC = () => {
  const { user } = useAuth();
  const { theme, setTheme } = useNavigationStore();

  const [username, setUsername] = useState(user?.username || '');
  const [firstName, setFirstName] = useState(user?.first_name || '');
  const [lastName, setLastName] = useState(user?.last_name || '');
  const [bio, setBio] = useState(user?.bio || '');
  const [timezone, setTimezone] = useState(user?.timezone || 'UTC');
  const [language, setLanguage] = useState(user?.language || 'en');
  const [avatarUrl, setAvatarUrl] = useState<string | null>(user?.avatar_url || null);

  useEffect(() => {
    if (user) {
      setUsername(user.username || '');
      setFirstName(user.first_name || '');
      setLastName(user.last_name || '');
      setBio(user.bio || '');
      if (user.timezone) setTimezone(user.timezone);
      if (user.language) setLanguage(user.language);
      if (user.avatar_url) setAvatarUrl(user.avatar_url);
    }
  }, [user?.id]);

  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleSelectAvatar = (url: string) => {
    setAvatarUrl(url);
  };

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      await updateProfile({
        username,
        first_name: firstName,
        last_name: lastName,
        bio,
        timezone,
        language,
        theme
      });
      setSuccessMsg('Profile updated successfully.');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update profile.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-3.5">
      <div className="border-b border-borderColor pb-2.5">
        <h1 className="text-lg font-bold text-textPrimary flex items-center gap-2">
          <User className="w-5 h-5 text-accentText" />
          Profile Settings
        </h1>
        <p className="text-xs text-textMuted mt-0.5">
          Manage your personal identity, display name, preferences, and organization persona.
        </p>
      </div>

      {successMsg && (
        <div className="flex items-center gap-2 p-2.5 bg-successBg border border-successBorder rounded-lg text-successText text-xs">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="flex items-center gap-2 p-2.5 bg-dangerBg border border-dangerBorder rounded-lg text-dangerText text-xs">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <div className="bg-bgCard border border-borderColor rounded-xl p-3.5 sm:p-4 space-y-4">
        {/* Avatar Section */}
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-3">
            Profile Avatar
          </label>
          <div className="flex items-center gap-4">
            <div className="relative w-16 h-16 rounded-full overflow-hidden border-2 border-accent/40 bg-bgTertiary flex items-center justify-center shrink-0">
              {avatarUrl ? (
                <img src={avatarUrl} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <User className="w-8 h-8 text-textMuted" />
              )}
            </div>

            <div>
              <p className="text-xs text-textMuted mb-2">Select a default avatar preset:</p>
              <div className="flex flex-wrap items-center gap-2">
                {AVATAR_PRESETS.map((preset, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleSelectAvatar(preset)}
                    className={`w-9 h-9 rounded-full overflow-hidden border-2 transition-all ${
                      avatarUrl === preset ? 'border-accent scale-105 shadow-md shadow-accent/30' : 'border-borderMuted hover:border-borderColor'
                    }`}
                  >
                    <img src={preset} alt={`Preset ${idx + 1}`} className="w-full h-full object-cover" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Profile Form */}
        <form onSubmit={handleSaveProfile} className="space-y-4 pt-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full bg-bgInput border border-borderColor rounded-lg px-4 py-2.5 text-sm text-textPrimary focus:outline-none focus:border-accent transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5">
                Email (Primary Identity)
              </label>
              <div className="relative">
                <input
                  type="email"
                  value={user?.email || ''}
                  disabled
                  className="w-full bg-bgTertiary border border-borderMuted rounded-lg px-4 py-2.5 text-sm text-textMuted cursor-not-allowed"
                />
                {user?.is_verified && (
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs bg-successBg text-successText border border-successBorder px-2 py-0.5 rounded flex items-center gap-1">
                    <ShieldCheck className="w-3 h-3" /> Verified
                  </span>
                )}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5">
                First Name
              </label>
              <input
                type="text"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="Jane"
                className="w-full bg-bgInput border border-borderColor rounded-lg px-4 py-2.5 text-sm text-textPrimary focus:outline-none focus:border-accent transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5">
                Last Name
              </label>
              <input
                type="text"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Doe"
                className="w-full bg-bgInput border border-borderColor rounded-lg px-4 py-2.5 text-sm text-textPrimary focus:outline-none focus:border-accent transition-colors"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5">
              Bio / About Me
            </label>
            <textarea
              rows={3}
              value={bio}
              onChange={(e) => setBio(e.target.value)}
              placeholder="Enterprise Architect & Knowledge Engineer..."
              className="w-full bg-bgInput border border-borderColor rounded-lg px-4 py-2.5 text-sm text-textPrimary focus:outline-none focus:border-accent transition-colors resize-none"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5 flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" /> Timezone
              </label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="w-full bg-bgInput border border-borderColor rounded-lg px-3 py-2 text-sm text-textPrimary focus:outline-none focus:border-accent"
              >
                <option value="UTC">UTC (Coordinated Universal Time)</option>
                <option value="America/New_York">America/New_York (EST)</option>
                <option value="America/Los_Angeles">America/Los_Angeles (PST)</option>
                <option value="Europe/London">Europe/London (GMT)</option>
                <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                <option value="Asia/Tokyo">Asia/Tokyo (JST)</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5 flex items-center gap-1">
                <Globe className="w-3.5 h-3.5" /> Preferred Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full bg-bgInput border border-borderColor rounded-lg px-3 py-2 text-sm text-textPrimary focus:outline-none focus:border-accent"
              >
                <option value="en">English (US)</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
                <option value="ja">日本語</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5 flex items-center gap-1">
                <Moon className="w-3.5 h-3.5 text-accentText" /> UI Theme
              </label>
              <select
                value={theme}
                onChange={(e) => setTheme(e.target.value as any)}
                className="w-full bg-bgInput border border-borderColor rounded-lg px-3 py-2 text-sm text-textPrimary focus:outline-none focus:border-accent"
              >
                <option value="dark">MindMesh Dark (Default)</option>
                <option value="light">MindMesh Light</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-borderMuted">
            <button
              type="submit"
              disabled={loading}
              className="flex items-center gap-2 bg-accent hover:bg-accentHover text-white font-medium px-6 py-2.5 rounded-lg text-sm transition-all shadow-lg shadow-accent/20"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save Profile Settings'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
