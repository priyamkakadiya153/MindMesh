import React, { useState, useEffect } from 'react';
import { Shield, KeyRound, Smartphone, Laptop, Trash2, Download, LogOut, Loader2, CheckCircle2, AlertCircle, RefreshCw, Lock, AlertTriangle } from 'lucide-react';
import { useAuth } from '../../features/auth/auth-provider';
import { changePassword, getSessions, revokeSession, logoutAllDevices, exportUserData, deleteAccount } from '../../features/auth/api';
import { DeviceSession } from '../../features/auth/types';

export const SecuritySettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [pwdLoading, setPwdLoading] = useState(false);
  const [pwdSuccess, setPwdSuccess] = useState<string | null>(null);
  const [pwdError, setPwdError] = useState<string | null>(null);

  const [devices, setDevices] = useState<DeviceSession[]>([]);
  const [devicesLoading, setDevicesLoading] = useState(false);
  const [deviceError, setDeviceError] = useState<string | null>(null);

  const [exportLoading, setExportLoading] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState('');

  const fetchDevicesList = async () => {
    setDevicesLoading(true);
    setDeviceError(null);
    try {
      const data = await getSessions();
      setDevices(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setDeviceError('Failed to load active devices.');
    } finally {
      setDevicesLoading(false);
    }
  };

  useEffect(() => {
    fetchDevicesList();
  }, []);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      setPwdError('New passwords do not match.');
      return;
    }

    setPwdLoading(true);
    setPwdSuccess(null);
    setPwdError(null);

    try {
      await changePassword(currentPassword, newPassword);
      setPwdSuccess('Password changed successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setPwdError(err.message || 'Failed to change password.');
    } finally {
      setPwdLoading(false);
    }
  };

  const handleRevokeDevice = async (sessionId: string) => {
    try {
      await revokeSession(undefined, sessionId);
      fetchDevicesList();
    } catch (err: any) {
      alert('Failed to revoke session.');
    }
  };

  const handleLogoutAll = async () => {
    if (!window.confirm('Are you sure you want to log out from all devices? You will need to sign in again.')) return;
    try {
      await logoutAllDevices();
      logout();
    } catch (err: any) {
      alert('Failed to execute Logout All Devices.');
    }
  };

  const handleExportData = async () => {
    setExportLoading(true);
    try {
      const data = await exportUserData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `mindmesh_account_export_${user?.id}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: any) {
      alert('Failed to export account data.');
    } finally {
      setExportLoading(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== 'DELETE') return;
    try {
      await deleteAccount();
      logout();
    } catch (err: any) {
      alert('Failed to delete account.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-3.5">
      <div className="border-b border-borderColor pb-2.5">
        <h1 className="text-lg font-bold text-textPrimary flex items-center gap-2">
          <Shield className="w-5 h-5 text-accentText" />
          Security & Active Devices
        </h1>
        <p className="text-xs text-textMuted mt-0.5">
          Manage your credentials, active device sessions, security tokens, and account compliance.
        </p>
      </div>

      {/* Change Password Card */}
      <div className="bg-bgCard border border-borderColor rounded-xl p-3.5 sm:p-4 space-y-3">
        <h2 className="text-base font-semibold text-textPrimary flex items-center gap-2">
          <KeyRound className="w-5 h-5 text-accentText" />
          Change Password
        </h2>

        {pwdSuccess && (
          <div className="flex items-center gap-2 p-3 bg-successBg border border-successBorder rounded-lg text-successText text-sm">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{pwdSuccess}</span>
          </div>
        )}

        {pwdError && (
          <div className="flex items-center gap-2 p-3 bg-dangerBg border border-dangerBorder rounded-lg text-dangerText text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{pwdError}</span>
          </div>
        )}

        <form onSubmit={handleChangePassword} className="space-y-4 max-w-md">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5">
              Current Password
            </label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              required
              className="w-full bg-bgInput border border-borderColor rounded-lg px-4 py-2.5 text-sm text-textPrimary focus:outline-none focus:border-accent"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5">
              New Password
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              className="w-full bg-bgInput border border-borderColor rounded-lg px-4 py-2.5 text-sm text-textPrimary focus:outline-none focus:border-accent"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-textMuted mb-1.5">
              Confirm New Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="w-full bg-bgInput border border-borderColor rounded-lg px-4 py-2.5 text-sm text-textPrimary focus:outline-none focus:border-accent"
            />
          </div>

          <button
            type="submit"
            disabled={pwdLoading}
            className="flex items-center gap-2 bg-accent hover:bg-accentHover text-white font-medium px-5 py-2.5 rounded-lg text-sm transition-all shadow-lg shadow-accent/20"
          >
            {pwdLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Update Password'}
          </button>
        </form>
      </div>

      {/* Active Devices & Sessions Manager Card */}
      <div className="bg-bgCard border border-borderColor rounded-xl p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-textPrimary flex items-center gap-2">
              <Laptop className="w-5 h-5 text-accentText" />
              Active Devices & Connected Sessions
            </h2>
            <p className="text-xs text-textMuted mt-1">
              Devices currently authorized to access your MindMesh account.
            </p>
          </div>

          <button
            onClick={handleLogoutAll}
            className="flex items-center gap-1.5 bg-dangerBg hover:bg-dangerBg/80 text-dangerText border border-dangerBorder px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all"
          >
            <LogOut className="w-3.5 h-3.5" /> Logout All Devices
          </button>
        </div>

        {devicesLoading ? (
          <div className="py-8 flex justify-center text-textMuted">
            <Loader2 className="w-6 h-6 animate-spin" />
          </div>
        ) : (
          <div className="space-y-3">
            {devices.map((device) => (
              <div
                key={device.id}
                className="flex items-center justify-between p-4 bg-bgTertiary border border-borderMuted rounded-lg text-sm"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2.5 bg-bgCard rounded-lg text-accentText">
                    {device.device.toLowerCase().includes('mobile') ? (
                      <Smartphone className="w-5 h-5" />
                    ) : (
                      <Laptop className="w-5 h-5" />
                    )}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-textPrimary">{device.device}</span>
                      {device.is_current && (
                        <span className="text-[10px] uppercase font-bold bg-accentSubtle text-accentText border border-accent/30 px-2 py-0.5 rounded">
                          Current Device
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-textMuted mt-0.5">
                      IP: {device.ip_address || 'Unknown'} • Last Active: {new Date(device.last_activity).toLocaleString()}
                    </p>
                  </div>
                </div>

                {!device.is_current && (
                  <button
                    onClick={() => handleRevokeDevice(device.id)}
                    className="text-xs text-dangerText hover:underline border border-dangerBorder hover:bg-dangerBg px-3 py-1.5 rounded transition-all"
                  >
                    Revoke Access
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Compliance & Danger Zone */}
      <div className="bg-bgCard border border-borderColor rounded-xl p-6 space-y-6">
        <h2 className="text-base font-semibold text-textPrimary flex items-center gap-2">
          <Download className="w-5 h-5 text-accentText" />
          Account Data & Compliance
        </h2>

        <div className="flex items-center justify-between p-4 bg-bgTertiary border border-borderMuted rounded-lg">
          <div>
            <h3 className="font-medium text-textPrimary text-sm">Export Account Data</h3>
            <p className="text-xs text-textMuted mt-0.5">
              Download a complete JSON export of your personal profile, workspace memberships, and active sessions.
            </p>
          </div>
          <button
            onClick={handleExportData}
            disabled={exportLoading}
            className="flex items-center gap-1.5 bg-bgHover hover:bg-bgActive text-textPrimary px-4 py-2 rounded-lg text-xs font-medium transition-all"
          >
            {exportLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Download className="w-4 h-4" /> Export Data</>}
          </button>
        </div>

        <div className="border-t border-borderMuted pt-6">
          <div className="flex items-center justify-between p-4 bg-dangerBg/40 border border-dangerBorder rounded-lg">
            <div>
              <h3 className="font-medium text-dangerText text-sm flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" /> Delete Account
              </h3>
              <p className="text-xs text-textMuted mt-0.5">
                Permanently revoke your account credentials and anonymize profile data. This operation cannot be undone.
              </p>
            </div>
            <button
              onClick={() => setDeleteModalOpen(true)}
              className="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded-lg text-xs font-medium transition-all shadow-lg shadow-red-600/20"
            >
              Delete Account
            </button>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-bgOverlay backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-md bg-bgDialog border border-dangerBorder rounded-xl p-6 space-y-4 shadow-2xl">
            <h3 className="text-lg font-bold text-dangerText flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" /> Confirm Account Deletion
            </h3>
            <p className="text-xs text-textSecondary">
              Type <strong>DELETE</strong> below to confirm permanent deactivation of your MindMesh account.
            </p>
            <input
              type="text"
              value={deleteConfirmText}
              onChange={(e) => setDeleteConfirmText(e.target.value)}
              placeholder="Type DELETE"
              className="w-full bg-bgInput border border-borderColor rounded-lg px-4 py-2.5 text-sm text-textPrimary focus:outline-none focus:border-dangerText"
            />
            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setDeleteModalOpen(false)}
                className="px-4 py-2 text-xs text-textMuted hover:text-textPrimary"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleteConfirmText !== 'DELETE'}
                className="bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white px-5 py-2 rounded-lg text-xs font-medium transition-all"
              >
                Confirm Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
