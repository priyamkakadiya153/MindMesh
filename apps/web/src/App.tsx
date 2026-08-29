import React, { useState, useEffect } from 'react';
import { EmptyState } from './shared/components/EmptyState';
import {
  LayoutDashboard,
  Briefcase,
  FolderOpen,
  Search as SearchIcon,
  MessageSquare,
  Bot,
  Settings as SettingsIcon,
  Sun,
  Moon,
  Bell,
  Plus,
  Loader2,
  CheckCircle,
  Clock,
  ArrowRight,
  Database,
  Send,
  LogOut,
  Shield,
  Building,
  UserPlus,
  Sparkles,
  BookOpen
} from 'lucide-react';
import { useAuth } from './features/auth/auth-provider';
import { LoginForm } from './components/auth/LoginForm';
import { RegisterForm } from './components/auth/RegisterForm';
import { OrganizationSwitcher } from './components/auth/OrganizationSwitcher';
import { DashboardLayout } from './layouts/DashboardLayout';
import { AuthLayout } from './layouts/AuthLayout';
import { Sidebar } from './navigation/Sidebar';
import { WorkspaceSwitcher } from './navigation/WorkspaceSwitcher';
import { CommandPalette } from './navigation/CommandPalette';
import { useWorkspaceStore } from './features/workspace/store';
import { useProjectStore } from './features/projects/store';
import * as dashboardApi from './features/dashboard/api';
import * as api from './features/auth/api';
import { DashboardPage } from './app/dashboard/page';
import { useNavigationStore } from './features/navigation/store';
import { useKeyboardShortcuts } from './features/navigation/hooks';
import { Topbar } from './features/navigation/components/Topbar';
import { UniversalSearchModal } from './features/search/UniversalSearchModal';
import { EmailVerificationBanner } from './components/auth/EmailVerificationBanner';
import { useNotificationStore } from './features/notifications/store';
import { NotificationDrawer } from './features/notifications/components/NotificationDrawer';

import { ErrorBoundary } from './shared/components/ErrorBoundary';
import { CognitiveAgentsPage } from './features/cognitive-agents/components/CognitiveAgentsPage';
import { SEO } from './shared/components/SEO';
import { LandingPage } from './components/landing/LandingPage';



const TAB_TITLES: Record<string, string> = {
  dashboard: 'Dashboard & Intelligence Briefing',
  workspaces: 'Workspace Management',
  projects: 'Projects Roster',
  messages: 'Direct Messages & Chat',
  files: 'Shared Files Repository',
  documents: 'Knowledge Documents Library',
  search: 'Semantic Knowledge Search',
  'action-inbox': 'Action Inbox & Intelligence Center',
  chat: 'AI Grounded Assistant',
  agents: 'AI Agents & Automation',
  organizations: 'Organization Configuration',
  members: 'Member Collaboration Directory',
  settings: 'Enterprise Administration & Settings'
};

// Lazy-loaded routes & feature modules for optimal code splitting
const WorkspacePage = React.lazy(() => import('./app/workspace/page'));
const ProjectsPage = React.lazy(() => import('./app/projects/page').then(m => ({ default: m.ProjectsPage })));
const DocumentsPage = React.lazy(() => import('./app/documents/page'));
const OrganizationSettingsPage = React.lazy(() => import('./app/settings/OrganizationSettingsPage').then(m => ({ default: m.OrganizationSettingsPage })));
const MembersPage = React.lazy(() => import('./app/members/page').then(m => ({ default: m.MembersPage })));
const SettingsPage = React.lazy(() => import('./app/settings/SettingsPage').then(m => ({ default: m.SettingsPage })));
const EnterpriseAIChat = React.lazy(() => import('./features/chat/EnterpriseAIChat').then(m => ({ default: m.EnterpriseAIChat })));
const DirectMessagesPage = React.lazy(() => import('./app/direct-messages/page').then(m => ({ default: m.DirectMessagesPage })));
const SharedFilesPage = React.lazy(() => import('./app/files/page').then(m => ({ default: m.SharedFilesPage })));
const ActionHistoryPage = React.lazy(() => import('./features/actions/ActionHistoryPage').then(m => ({ default: m.ActionHistoryPage })));
const ActionInboxPage = React.lazy(() => import('./app/action-inbox/page'));

const PageFallback = () => (
  <div className="flex items-center justify-center p-12 text-accentText text-xs font-semibold" role="status" aria-live="polite">
    <Loader2 className="w-5 h-5 animate-spin mr-2 text-accent" aria-hidden="true" />
    <span>Loading view...</span>
  </div>
);






interface Stats {
  users: number;
  organizations: number;
  workspaces: number;
  projects: number;
  documents: number;
  messages: number;
}

interface DashboardData {
  stats: Stats;
  recent_projects: Array<{ id: string; name: string; slug: string }>;
  recent_documents: Array<{ id: string; name: string; mime_type: string; size: number }>;
}

function App() {
  const {
    user,
    token,
    currentOrg,
    organizations,
    isAuthenticated,
    logout,
    createOrg
  } = useAuth();

  const {
    workspaces,
    currentWorkspace,
    selectWorkspace,
    fetchWorkspaces,
    createWorkspace
  } = useWorkspaceStore();

  const {
    projects,
    fetchProjects,
    createProject
  } = useProjectStore();

  const { activeTab, setActiveTab, theme, setTheme } = useNavigationStore();
  useKeyboardShortcuts(() => setActiveTab('documents'));

  const {
    isDrawerOpen,
    toggleDrawer,
    setDrawerOpen,
    unreadCount,
    fetchNotifications,
    fetchUserInvitations
  } = useNotificationStore();

  useEffect(() => {
    if (token) {
      fetchNotifications(token);
      fetchUserInvitations(token);
      const interval = setInterval(() => {
        fetchNotifications(token);
        fetchUserInvitations(token);
      }, 10000);
      return () => clearInterval(interval);
    }
  }, [token]);

  useEffect(() => {
    let effectiveTheme = theme;
    if (theme === 'system') {
      effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    if (effectiveTheme === 'dark') {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
      document.documentElement.style.colorScheme = 'dark';
    } else {
      document.documentElement.classList.remove('dark');
      document.documentElement.classList.add('light');
      document.documentElement.style.colorScheme = 'light';
    }
  }, [theme]);

  const [favorites, setFavorites] = useState<any[]>([]);
  const [recents, setRecents] = useState<any[]>([]);
  const [activities, setActivities] = useState<any[]>([]);

  const [dbConnected, setDbConnected] = useState<boolean | null>(null);
  const [backendStatus, setBackendStatus] = useState<'running' | 'offline'>('offline');
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [initTimeout, setInitTimeout] = useState(false);
  const [authMode, setAuthMode] = useState<'landing' | 'login' | 'register'>('landing');

  const [settingsSubTab, setSettingsSubTab] = useState<'profile' | 'security' | 'system'>('profile');

  // Create Org / Switch states
  const [newOrgName, setNewOrgName] = useState('');
  const [newOrgSlug, setNewOrgSlug] = useState('');
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('MEMBER');
  const [orgMessage, setOrgMessage] = useState('');
  const [orgLoading, setOrgLoading] = useState(false);

  // Form states (Project/Doc)
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectSlug, setNewProjectSlug] = useState('');
  const [newDocName, setNewDocName] = useState('');
  const [newDocType, setNewDocType] = useState('application/pdf');
  const [newDocSize, setNewDocSize] = useState('102400');
  


  // Semantic Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Array<{ title: string; snippet: string; score: number }>>([]);

  // Active Sessions State
  const [sessions, setSessions] = useState<any[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);

  const loadSessions = async () => {
    if (!token) return;
    try {
      setSessionsLoading(true);
      const res = await api.getSessions(token);
      setSessions(res);
    } catch (e) {
      console.error("Failed to load sessions:", e);
    } finally {
      setSessionsLoading(false);
    }
  };

  const handleRevokeSession = async (sessionId: string) => {
    if (!token) return;
    if (confirm("Are you sure you want to revoke this session?")) {
      try {
        await api.revokeSession(token, sessionId);
        loadSessions();
      } catch (err: any) {
        alert(err.message || "Failed to revoke session");
      }
    }
  };

  const handleLogoutAllDevices = async () => {
    if (!token) return;
    if (confirm("Are you sure you want to log out from all devices? This will invalidate all your active sessions.")) {
      try {
        await api.logoutAllDevices(token);
        logout();
      } catch (err: any) {
        alert(err.message || "Failed to revoke sessions");
      }
    }
  };

  useEffect(() => {
    if (token && activeTab === 'settings') {
      loadSessions();
    }
  }, [token, activeTab]);

  const API_URL = 'http://127.0.0.1:4000';

  useEffect(() => {
    checkHealth();
  }, [token]);

  useEffect(() => {
    if (loading) {
      const timer = setTimeout(() => {
        setInitTimeout(true);
      }, 5000);
      return () => clearTimeout(timer);
    } else {
      setInitTimeout(false);
    }
  }, [loading]);

  useEffect(() => {
    if (token && currentOrg) {
      fetchWorkspaces(token, currentOrg.id);
    }
  }, [token, currentOrg, fetchWorkspaces]);

  useEffect(() => {
    if (token && currentOrg && currentWorkspace) {
      fetchProjects(token, currentOrg.id, currentWorkspace.id);
      loadDashboardData();
    }
  }, [token, currentOrg, currentWorkspace, fetchProjects]);

  const loadDashboardData = async () => {
    if (!token || !currentOrg) return;
    try {
      const stats = await dashboardApi.getStats(token, currentOrg.id);
      setData(stats);
      
      const favs = await dashboardApi.getFavorites(token, currentOrg.id);
      setFavorites(favs);

      const rec = await dashboardApi.getRecents(token, currentOrg.id);
      setRecents(rec);

      const act = await dashboardApi.getActivityFeed(token, currentOrg.id);
      setActivities(act);
    } catch (e) {
      setData({
        stats: {
          users: user ? 1 : 0,
          organizations: organizations.length || 0,
          workspaces: workspaces.length || 1,
          projects: projects.length || 3,
          documents: 4,
          messages: 12
        },
        recent_projects: projects.length > 0 ? projects.slice(0, 5) : [
          { id: '1', name: 'Sample Project Alpha', slug: 'project-alpha' },
          { id: '2', name: 'Marketing Campaign', slug: 'marketing-camp' },
          { id: '3', name: 'Product Engineering Roadmap', slug: 'prod-eng' }
        ],
        recent_documents: [
          { id: '1', name: 'enterprise_operating_model.pdf', mime_type: 'application/pdf', size: 1048576 },
          { id: '2', name: 'system_architecture_spec.md', mime_type: 'text/markdown', size: 24576 },
          { id: '3', name: 'financial_projections_q3.xlsx', mime_type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', size: 512000 }
        ]
      });
    }
  };

  const checkHealth = async () => {
    try {
      const healthRes = await fetch(`${API_URL}/health`);
      if (healthRes.ok) {
        const healthData = await healthRes.json();
        setBackendStatus('running');
        setDbConnected(healthData.database === 'connected');
      } else {
        setBackendStatus('offline');
        setDbConnected(false);
      }
    } catch (e) {
      setBackendStatus('offline');
      setDbConnected(false);
    }
  };

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName || !newOrgSlug) return;
    setOrgLoading(true);
    setOrgMessage('');

    try {
      await createOrg(newOrgName, newOrgSlug);
      setOrgMessage(`Successfully created ${newOrgName}!`);
      setNewOrgName('');
      setNewOrgSlug('');
    } catch (err: any) {
      setOrgMessage(`Error: ${err.message || 'Failed to create organization'}`);
    } finally {
      setOrgLoading(false);
    }
  };

  const handleInviteMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail || !currentOrg || !token) return;
    setOrgLoading(true);
    setOrgMessage('');

    try {
      await api.inviteOrgMember(currentOrg.id, inviteEmail, inviteRole);
      setOrgMessage(`Successfully invited member to organization!`);
      setInviteEmail('');
    } catch (err: any) {
      setOrgMessage(`Error: ${err.message || 'Failed to invite member'}`);
    } finally {
      setOrgLoading(false);
    }
  };


  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newProjectName || !newProjectSlug || !currentWorkspace || !token || !currentOrg) return;

    try {
      await createProject(token, currentOrg.id, { name: newProjectName, slug: newProjectSlug, workspace_id: currentWorkspace.id });
      setNewProjectName('');
      setNewProjectSlug('');
      await loadDashboardData();
    } catch (err) {
      if (data) {
        setData({
          ...data,
          recent_projects: [
            ...data.recent_projects,
            { id: String(Date.now()), name: newProjectName, slug: newProjectSlug }
          ]
        });
        setNewProjectName('');
        setNewProjectSlug('');
      }
    }
  };


  const handleCreateDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDocName) return;

    try {
      const res = await fetch(`${API_URL}/api/v1/documents/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newDocName,
          mime_type: newDocType,
          size: parseInt(newDocSize),
          storage_path: `/uploads/${newDocName}`
        })
      });
      if (res.ok) {
        setNewDocName('');
        await loadDashboardData();
      }
    } catch (err) {
      if (data) {
        setData({
          ...data,
          recent_documents: [
            ...data.recent_documents,
            { id: String(Date.now()), name: newDocName, mime_type: newDocType, size: parseInt(newDocSize) }
          ]
        });
        setNewDocName('');
      }
    }
  };



  const [searchError, setSearchError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim() || !token) return;

    if (!currentOrg) {
      setSearchError("Please select an organization before searching.");
      return;
    }

    setSearchError(null);
    try {
      const params = new URLSearchParams({ q: searchQuery.trim() });
      if (currentOrg?.id) params.append('organization_id', currentOrg.id);
      if (currentWorkspace?.id) params.append('workspace_id', currentWorkspace.id);

      const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
      if (currentOrg?.id) headers['X-Organization-ID'] = currentOrg.id;

      const res = await fetch(`http://127.0.0.1:4000/api/v1/search?${params.toString()}`, {
        headers
      });
      if (res.ok) {
        const data = await res.json();
        const rawItems = data.items || data.results || [];
        setSearchResults(rawItems.map((item: any) => ({
          title: item.title,
          snippet: item.snippet || item.excerpt || '',
          score: item.score || 0.95
        })));
      } else {
        const errData = await res.json().catch(() => ({}));
        let errorMsg = 'Search failed. Please try again.';
        if (errData?.detail) {
          if (typeof errData.detail === 'string') errorMsg = errData.detail;
          else if (Array.isArray(errData.detail)) {
            errorMsg = errData.detail.map((d: any) => d.msg || d.detail).join('; ');
          }
        }
        setSearchError(errorMsg);
        setSearchResults([]);
      }
    } catch (err) {
      setSearchError('Search failed. Please check network connection.');
      setSearchResults([]);
    }
  };

  const toggleTheme = () => {
    setTheme(theme === 'dark' ? 'light' : 'dark');
  };

  if (!isAuthenticated) {
    if (authMode === 'landing') {
      return (
        <LandingPage
          onSignInClick={() => setAuthMode('login')}
          onGetStartedClick={() => setAuthMode('register')}
        />
      );
    }


    return (
      <AuthLayout
        theme={theme}
        toggleTheme={toggleTheme}
        sunIcon={<Sun size={16} />}
        moonIcon={<Moon size={16} />}
      >
        <div className="mb-4 flex justify-between items-center">
          <button
            onClick={() => setAuthMode('landing')}
            className="text-xs text-indigo-600 dark:text-indigo-400 font-semibold hover:underline flex items-center gap-1"
          >
            ← Back to MindMesh Landing
          </button>
        </div>
        {authMode === 'login' ? (
          <LoginForm onRegisterLink={() => setAuthMode('register')} />
        ) : (
          <RegisterForm onLoginLink={() => setAuthMode('login')} />
        )}
      </AuthLayout>
    );
  }




  return (
    <>
      <CommandPalette onNavigate={setActiveTab} />
      <DashboardLayout
        theme={theme}
        sidebar={
          <Sidebar
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            theme={theme}
            toggleTheme={toggleTheme}
            backendStatus={backendStatus}
            dbConnected={dbConnected}
          />
        }
      >
          <SEO title={TAB_TITLES[activeTab]} />
          <Topbar
            onNotificationsClick={toggleDrawer}
            unreadCount={unreadCount}
            hasUnreadNotifications={unreadCount > 0}
          />
          <EmailVerificationBanner />
          <NotificationDrawer
            isOpen={isDrawerOpen}
            onClose={() => setDrawerOpen(false)}
            onNavigate={setActiveTab}
          />

        {/* Lazy Loaded Tab Views */}
        <ErrorBoundary>
          <React.Suspense fallback={<PageFallback />}>
            {/* Dashboard Tab Content */}
            {activeTab === 'dashboard' && (
              <DashboardPage
                onNavigate={setActiveTab}
                onNewProject={() => setActiveTab('projects')}
                onUploadDoc={() => setActiveTab('documents')}
                onNewChat={() => setActiveTab('chat')}
                onInviteMember={() => setActiveTab('organizations')}
                onCreateWorkspace={() => setActiveTab('workspaces')}
              />
            )}

            {/* Workspaces Tab Content */}
            {activeTab === 'workspaces' && (
              <WorkspacePage />
            )}

            {/* Projects Tab */}
            {activeTab === 'projects' && (
              <ProjectsPage />
            )}

            {/* Direct Messages Tab */}
            {activeTab === 'messages' && (
              <DirectMessagesPage />
            )}

            {/* Shared Files Tab */}
            {activeTab === 'files' && (
              <SharedFilesPage />
            )}

            {/* Documents Tab */}
            {activeTab === 'documents' && (
              <DocumentsPage />
            )}

            {/* Action Inbox Tab */}
            {activeTab === 'action-inbox' && (
              <ActionInboxPage />
            )}

            {/* AI Chat Tab */}
            {activeTab === 'chat' && (
              <EnterpriseAIChat />
            )}


            {/* Action History & Memory Tab */}
            {activeTab === 'action-history' && (
              <ActionHistoryPage />
            )}

            {/* Organizations Tab */}
            {(activeTab === 'organizations' || activeTab === 'organization') && (
              <OrganizationSettingsPage />
            )}

            {/* Members & Directory Tab */}
            {activeTab === 'members' && (
              <MembersPage />
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
              <SettingsPage />
            )}
          </React.Suspense>
        </ErrorBoundary>

        {/* Semantic Search Tab */}
        {activeTab === 'search' && (
          <div className="space-y-3.5">
            <div className="rounded-2xl border border-borderColor bg-bgCard p-3.5 sm:p-4 shadow-sm">
              <h4 className="title-display font-semibold mb-2.5 text-xs text-textPrimary">Semantic Knowledge Discovery</h4>
              <form onSubmit={handleSearch} className="flex gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Ask a question (e.g. 'architecture model', 'financial projections')..."
                  className="flex-1 px-3.5 py-1.5 bg-bgInput border border-borderColor rounded-xl text-xs text-textPrimary placeholder-textMuted focus:outline-none focus:border-accent"
                />
                <button type="submit" className="px-3.5 bg-accent hover:bg-accentHover text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-md shadow-accent/10">
                  <SearchIcon size={14} /> Search
                </button>
              </form>
              {searchError && (
                <div className="mt-2.5 p-2.5 rounded-xl bg-dangerBg border border-dangerBorder text-dangerText text-xs flex items-center gap-2">
                  <span>{searchError}</span>
                </div>
              )}
            </div>

            {/* Results or Empty State */}
            {searchResults.length > 0 ? (
              <div className="space-y-2.5">
                <h5 className="text-[10px] text-textMuted uppercase tracking-widest px-1">Search Results</h5>
                {searchResults.map((result, idx) => (
                  <div key={idx} className="p-3 bg-bgCard border border-borderColor rounded-xl shadow-sm space-y-1.5">
                    <div className="flex items-center justify-between mb-1">
                      <h6 className="text-xs font-semibold text-accentText">{result.title}</h6>
                      <span className="text-[9px] bg-successBg text-successText border border-successBorder px-2 py-0.2 rounded-full font-mono">
                        Relevance: {(result.score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-xs text-textSecondary leading-relaxed">{result.snippet}</p>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState
                title="Search your organization's knowledge"
                description="Ask questions or search conversations, files, and projects using intelligent search."
                icon={Sparkles}
                variant="card"
                primaryAction={{
                  label: "Start Searching",
                  onClick: () => {
                    const input = document.querySelector('input[placeholder*="Ask a question"]') as HTMLInputElement;
                    if (input) input.focus();
                  },
                  icon: SearchIcon
                }}
                secondaryAction={{
                  label: "View Examples",
                  onClick: () => setSearchQuery("architecture model"),
                  icon: BookOpen
                }}
              />
            )}
          </div>
        )}

        {/* AI Agents Tab */}
        {activeTab === 'agents' && (
          <CognitiveAgentsPage />
        )}


      <UniversalSearchModal />
    </DashboardLayout>
    </>
  );
}

export default App;

