import * as api from './api';
import { useAuthStore } from './auth-store';

export class SessionManager {
  private static intervalId: any = null;

  static startAutoRefresh() {
    if (this.intervalId) return;

    // Refresh token every 12 minutes (since Access Token lives 15 mins)
    this.intervalId = setInterval(async () => {
      const store = useAuthStore.getState();
      if (store.refreshToken && store.isAuthenticated) {
        try {
          const res: any = await api.refresh(store.refreshToken);
          const user = await api.getCurrentUser(res.access_token);
          store.setSession(res.access_token, res.refresh_token, user);
        } catch (err) {
          console.error('[SessionManager] Session expired or refresh failed:', err);
          store.clearSession();
          this.stopAutoRefresh();
        }
      }
    }, 12 * 60 * 1000);
  }

  static stopAutoRefresh() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }
}
