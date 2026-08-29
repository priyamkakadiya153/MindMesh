import { User, Organization, DeviceSession } from './types';
import { apiClient } from '../../lib/api-client';

async function wrapRequest<T>(fn: () => Promise<{ data: T }>): Promise<T> {
  try {
    const res = await fn();
    return res.data;
  } catch (err: any) {
    if (err.response) {
      const data = err.response.data;
      let errorDetail = '';
      if (err.response.status === 422 && data && Array.isArray(data.detail)) {
        errorDetail = data.detail.map((e: any) => {
          const loc = e.loc.filter((l: any) => l !== 'body').join('.');
          return `${loc ? loc + ': ' : ''}${e.msg}`;
        }).join(', ');
      } else if (data && data.detail) {
        errorDetail = data.detail;
      }
      
      if (errorDetail) {
        throw new Error(errorDetail);
      }
      throw new Error(err.response.statusText || `HTTP error ${err.response.status}`);
    }
    throw new Error(err.message || 'Cannot connect to server.');
  }
}

export async function login(email: string, password: string) {
  return wrapRequest(() => apiClient.post('/auth/login', { email, password }));
}

export async function loginWithFirebaseToken(idToken: string) {
  return wrapRequest(() => apiClient.post('/auth/firebase-login', { idToken }));
}

export async function sendPhoneOtp(phoneNumber: string) {
  return wrapRequest<{ status: string; message: string; email_masked: string; expires_in_seconds: number; resend_cooldown_seconds: number }>(
    () => apiClient.post('/auth/phone/send-otp', { phone_number: phoneNumber })
  );
}

export async function resendPhoneOtp(phoneNumber: string) {
  return wrapRequest<{ status: string; message: string; email_masked: string; expires_in_seconds: number; resend_cooldown_seconds: number }>(
    () => apiClient.post('/auth/phone/resend-otp', { phone_number: phoneNumber })
  );
}

export async function verifyPhoneOtp(phoneNumber: string, code: string) {
  return wrapRequest<{ access_token: string; refresh_token: string; token_type: string; user: User }>(
    () => apiClient.post('/auth/phone/verify-otp', { phone_number: phoneNumber, code })
  );
}

export async function register(user_in: any) {
  return wrapRequest<{ status: string; message: string; email_masked: string; registration_token: string; expires_in_seconds: number; resend_cooldown_seconds: number }>(
    () => apiClient.post('/auth/register', user_in)
  );
}

export async function registerInitiate(user_in: any) {
  return wrapRequest<{ status: string; message: string; email_masked: string; registration_token: string; expires_in_seconds: number; resend_cooldown_seconds: number }>(
    () => apiClient.post('/auth/register', user_in)
  );
}

export async function registerResendOtp(registrationToken: string) {
  return wrapRequest<{ status: string; message: string; email_masked: string; registration_token: string; resend_cooldown_seconds: number }>(
    () => apiClient.post('/auth/register/resend-otp', { registration_token: registrationToken })
  );
}

export async function registerVerifyOtp(registrationToken: string, code: string) {
  return wrapRequest<{ access_token: string; refresh_token: string; token_type: string; user: User }>(
    () => apiClient.post('/auth/register/verify-otp', { registration_token: registrationToken, code })
  );
}

export async function logout(refreshToken: string) {
  try {
    await apiClient.post('/auth/logout', { refresh_token: refreshToken });
    return true;
  } catch (e) {
    return false;
  }
}

export async function refresh(refreshToken: string) {
  return wrapRequest(() => apiClient.post('/auth/refresh', { refresh_token: refreshToken }));
}

export async function getCurrentUser(token?: string, orgId?: string): Promise<User> {
  return wrapRequest(() => apiClient.get('/users/me'));
}

export async function updateProfile(profileData: Partial<User>): Promise<any> {
  return wrapRequest(() => apiClient.patch('/users/me', profileData));
}

export const updateUserProfile = updateProfile;

export async function updateUserAvatar(avatarUrl: string): Promise<any> {
  return wrapRequest(() => apiClient.patch('/users/avatar', { avatar_url: avatarUrl }));
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<any> {
  return wrapRequest(() => apiClient.post('/users/change-password', { current_password: currentPassword, new_password: newPassword }));
}

export async function sendEmailVerification(): Promise<any> {
  return wrapRequest(() => apiClient.post('/auth/email/send-verification'));
}

export async function verifyEmailToken(token: string): Promise<any> {
  return wrapRequest(() => apiClient.post('/auth/email/verify', { token }));
}

export async function requestPasswordReset(email: string): Promise<any> {
  return wrapRequest(() => apiClient.post('/auth/password/forgot', { email }));
}

export async function resetPasswordWithToken(tokenOrCode: string, newPassword: string): Promise<any> {
  return wrapRequest(() => apiClient.post('/auth/password/reset', { token_or_code: tokenOrCode, new_password: newPassword }));
}

export async function exportUserData(): Promise<any> {
  return wrapRequest(() => apiClient.get('/users/export-data'));
}

export async function deleteAccount(): Promise<any> {
  return wrapRequest(() => apiClient.delete('/users/me'));
}

export async function getOrganizations(token?: string): Promise<Organization[]> {
  return wrapRequest(() => apiClient.get('/organizations/'));
}

export async function getCurrentOrganization(): Promise<Organization> {
  return wrapRequest(() => apiClient.get('/organizations/current'));
}

export async function createOrganization(token?: string, name?: string, slug?: string, description = ''): Promise<any> {
  return wrapRequest(() => apiClient.post('/organizations/', { name, slug, description }));
}

export async function updateOrganization(orgId: string, data: Partial<Organization>): Promise<Organization> {
  return wrapRequest(() => apiClient.patch(`/organizations/${orgId}`, data));
}

export async function deleteOrganization(orgId: string): Promise<any> {
  return wrapRequest(() => apiClient.delete(`/organizations/${orgId}`));
}

export async function switchOrganization(orgId: string): Promise<Organization> {
  return wrapRequest(() => apiClient.post(`/organizations/${orgId}/switch`));
}

export async function leaveOrganization(orgId: string): Promise<any> {
  return wrapRequest(() => apiClient.post(`/organizations/${orgId}/leave`));
}

export async function getOrgSettings(orgId: string): Promise<any> {
  return wrapRequest(() => apiClient.get(`/organizations/${orgId}/settings`));
}

export async function updateOrgSettings(orgId: string, settingsData: any): Promise<any> {
  return wrapRequest(() => apiClient.patch(`/organizations/${orgId}/settings`, settingsData));
}

export async function getOrgMembers(orgId: string): Promise<any[]> {
  return wrapRequest(() => apiClient.get(`/organizations/${orgId}/members`));
}

export async function inviteOrgMember(orgId: string, email: string, role = 'member'): Promise<any> {
  return wrapRequest(() => apiClient.post(`/organizations/${orgId}/invite`, { email, role }));
}

export async function getOrgInvitations(orgId: string): Promise<any[]> {
  return wrapRequest(() => apiClient.get(`/organizations/${orgId}/invitations`));
}

export async function updateOrgMemberRole(orgId: string, memberId: string, role: string): Promise<any> {
  return wrapRequest(() => apiClient.patch(`/organizations/${orgId}/members/${memberId}`, { role }));
}

export async function removeOrgMember(orgId: string, memberId: string): Promise<any> {
  return wrapRequest(() => apiClient.delete(`/organizations/${orgId}/members/${memberId}`));
}

export async function getUserInvitations(): Promise<any[]> {
  return wrapRequest(() => apiClient.get('/invitations/'));
}

export async function acceptInvitation(tokenOrId: string): Promise<any> {
  return wrapRequest(() => apiClient.post(`/invitations/${tokenOrId}/accept`));
}

export async function rejectInvitation(inviteId: string): Promise<any> {
  return wrapRequest(() => apiClient.post(`/invitations/${inviteId}/reject`));
}

export async function updateCurrentOrganization(token?: string, orgId?: string): Promise<any> {
  return switchOrganization(orgId || '');
}

export async function updateCurrentWorkspace(token?: string, workspaceId?: string): Promise<any> {
  return wrapRequest(() => apiClient.post(`/workspaces/${workspaceId}/switch`));
}

export async function getSessions(token?: string): Promise<DeviceSession[]> {
  return wrapRequest(() => apiClient.get('/devices'));
}

export async function getSessionDetail(token?: string): Promise<any> {
  return wrapRequest(() => apiClient.get('/auth/session'));
}

export async function revokeSession(token?: string, sessionId?: string): Promise<any> {
  const sId = sessionId || token;
  return wrapRequest(() => apiClient.delete(`/devices/${sId}`));
}

export async function logoutAllDevices(token?: string): Promise<any> {
  return wrapRequest(() => apiClient.post('/auth/logout-all'));
}



