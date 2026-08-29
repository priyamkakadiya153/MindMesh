import React, { useState } from 'react';
import { useNotificationStore } from '../../notifications/store';
import { useAuth } from '../../auth/auth-provider';
import { useWorkspaceStore } from '../../workspace/store';
import { Building2, Check, X, Loader2, Sparkles, UserPlus } from 'lucide-react';

interface PendingInvitationsBannerProps {
  onNavigate?: (tab: string) => void;
}

export function PendingInvitationsBanner({ onNavigate }: PendingInvitationsBannerProps) {
  const { token, refreshUserOrganizations } = useAuth();
  const { fetchWorkspaces } = useWorkspaceStore();
  const { userInvitations, acceptInvitation, declineInvitation, fetchUserInvitations } = useNotificationStore();
  const [processingId, setProcessingId] = useState<string | null>(null);

  React.useEffect(() => {
    fetchUserInvitations(token || undefined);
  }, [token]);

  if (!userInvitations || userInvitations.length === 0) return null;

  const handleAccept = async (invitationIdOrToken: string) => {
    setProcessingId(invitationIdOrToken);
    try {
      await acceptInvitation(invitationIdOrToken, token || undefined);
      if (refreshUserOrganizations) await refreshUserOrganizations();
      await fetchWorkspaces(token || '', '');
      if (onNavigate) onNavigate('dashboard');
    } catch (err: any) {
      alert(err.message || 'Failed to accept invitation');
    } finally {
      setProcessingId(null);
    }
  };

  const handleDecline = async (invitationIdOrToken: string) => {
    setProcessingId(invitationIdOrToken);
    try {
      await declineInvitation(invitationIdOrToken, token || undefined);
    } catch (err: any) {
      alert(err.message || 'Failed to decline invitation');
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div className="space-y-3 mb-4 animate-fadeIn">
      {userInvitations.map(inv => (
        <div
          key={inv.id}
          className="p-4 rounded-2xl border border-accent/30 bg-gradient-to-r from-accent/10 via-bgCard to-bgCard shadow-lg flex flex-col md:flex-row md:items-center justify-between gap-4 transition-all hover:border-accent/50"
        >
          <div className="flex items-center gap-3.5 min-w-0">
            <div className="p-3 rounded-2xl bg-accent text-white shrink-0 shadow-md">
              <Building2 size={20} />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="bg-accent/20 text-accentText text-[10px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider">
                  Pending Invitation
                </span>
                <span className="text-xs text-textMuted font-mono">Role: {inv.role}</span>
              </div>
              <h3 className="font-bold text-textPrimary text-sm sm:text-base truncate mt-0.5">
                Join <span className="text-accentText">{inv.org_name || 'Organization'}</span>
              </h3>
              <p className="text-xs text-textSecondary mt-0.5 truncate">
                Invited for email: <span className="font-semibold text-textPrimary">{inv.email}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
            <button
              disabled={processingId === inv.id}
              onClick={() => handleDecline(inv.id || inv.token)}
              className="px-4 py-2 rounded-xl border border-borderColor bg-bgInput hover:bg-bgHover text-textSecondary text-xs font-semibold transition-all disabled:opacity-50 flex items-center gap-1.5"
            >
              <X size={14} />
              <span>Decline</span>
            </button>

            <button
              disabled={processingId === inv.id}
              onClick={() => handleAccept(inv.id || inv.token)}
              className="px-5 py-2 rounded-xl bg-accent hover:bg-accentHover text-white text-xs font-bold transition-all shadow-md hover:shadow-lg flex items-center gap-1.5 disabled:opacity-50 active:scale-95"
            >
              {processingId === inv.id ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Check size={14} />
              )}
              <span>Accept Invitation</span>
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
