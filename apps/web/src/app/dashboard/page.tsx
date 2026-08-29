import React from 'react';
import { useAuth } from '../../features/auth/auth-provider';
import { useWorkspaceStore } from '../../features/workspace/store';
import { useDashboard } from '../../features/dashboard/hooks';
import { WelcomeBanner } from '../../features/dashboard/components/WelcomeBanner';
import { QuickActions } from '../../features/dashboard/components/QuickActions';
import { DashboardStats } from '../../features/dashboard/components/DashboardStats';
import { DashboardGrid } from '../../features/dashboard/components/DashboardGrid';
import { RecentProjects } from '../../features/dashboard/components/RecentProjects';
import { RecentDocuments } from '../../features/dashboard/components/RecentDocuments';
import { RecentChats } from '../../features/dashboard/components/RecentChats';
import { NotificationPanel } from '../../features/dashboard/components/NotificationPanel';
import { ActivityTimeline } from '../../features/dashboard/components/ActivityTimeline';
import { FavoriteList } from '../../features/dashboard/components/FavoriteList';
import { AIInsights } from '../../features/dashboard/components/AIInsights';
import { StorageUsage } from '../../features/dashboard/components/StorageUsage';
import { PendingInvitationsBanner } from '../../features/dashboard/components/PendingInvitationsBanner';
import { EmptyState } from '../../shared/components/EmptyState';
import { WidgetErrorBoundary } from '../../shared/components/WidgetErrorBoundary';
import { Plus, Upload, Sparkles } from 'lucide-react';

interface DashboardPageProps {
  onNavigate: (tab: string) => void;
  onNewProject: () => void;
  onUploadDoc: () => void;
  onNewChat: () => void;
  onInviteMember: () => void;
  onCreateWorkspace: () => void;
}

export function DashboardPage({
  onNavigate,
  onNewProject,
  onUploadDoc,
  onNewChat,
  onInviteMember,
  onCreateWorkspace
}: DashboardPageProps) {
  const { user, token, currentOrg } = useAuth();
  const { currentWorkspace, workspaces } = useWorkspaceStore();
  
  const {
    statisticsState,
    recentProjectsState,
    recentDocumentsState,
    recentChatsState,
    notificationsState,
    activityState,
    favoritesState,
    aiSummaryState,
    refresh,
    retrySection,
    toggleFavorite,
    markAsRead,
    markAllAsRead,
    deleteNotification
  } = useDashboard(token, currentOrg?.id || null, currentWorkspace?.id);

  const favorites = favoritesState.data || [];
  const favoriteIds = favorites.map(f => f.item_id);
  
  const stats = statisticsState.data || {
    workspaces_count: workspaces.length || 0,
    projects_count: recentProjectsState.data?.length || 0,
    documents_count: recentDocumentsState.data?.length || 0,
    chats_count: recentChatsState.data?.length || 0,
    storage_used: 0,
    members_count: 1
  };

  const isNewUserWithoutWorkspace = workspaces.length === 0 && !currentWorkspace;

  const displayName = user?.username || (user?.email ? user.email.split('@')[0] : 'Member');
  const displayWorkspace = currentWorkspace?.name || currentOrg?.name || 'Workspace';

  return (
    <div className="space-y-3.5">
      <WidgetErrorBoundary title="Unable to load invitations banner">
        <PendingInvitationsBanner onNavigate={onNavigate} />
      </WidgetErrorBoundary>

      {isNewUserWithoutWorkspace && (
        <EmptyState
          title="Welcome to MindMesh"
          description="Start by creating a workspace, inviting teammates, or uploading your first document."
          icon={Sparkles}
          badge="Getting Started"
          variant="page"
          primaryAction={{
            label: "Create Workspace",
            onClick: onCreateWorkspace,
            icon: Plus
          }}
          secondaryAction={{
            label: "Upload Document",
            onClick: onUploadDoc,
            icon: Upload
          }}
        />
      )}

      <WidgetErrorBoundary title="Unable to load welcome banner">
        <WelcomeBanner
          userName={displayName}
          workspaceName={displayWorkspace}
          projectsCount={stats.projects_count}
          documentsCount={stats.documents_count}
          membersCount={stats.members_count}
        />
      </WidgetErrorBoundary>

      <WidgetErrorBoundary title="Unable to load quick actions">
        <QuickActions
          onNewProject={onNewProject}
          onUploadDoc={onUploadDoc}
          onNewChat={onNewChat}
          onInviteMember={onInviteMember}
          onCreateWorkspace={onCreateWorkspace}
        />
      </WidgetErrorBoundary>

      <WidgetErrorBoundary title="Unable to load dashboard statistics" onRetry={() => retrySection('stats')}>
        <DashboardStats 
          stats={stats} 
          loading={statisticsState.loading && !statisticsState.data}
          error={statisticsState.error}
          onRetry={() => retrySection('stats')}
        />
      </WidgetErrorBoundary>

      <DashboardGrid>
        <WidgetErrorBoundary title="Unable to load recent projects" onRetry={() => retrySection('recent_projects')}>
          <RecentProjects
            projects={recentProjectsState.data || []}
            favorites={favoriteIds}
            loading={recentProjectsState.loading && !recentProjectsState.data}
            error={recentProjectsState.error}
            onRetry={() => retrySection('recent_projects')}
            onToggleFavorite={(id, name, slug) => toggleFavorite('project', id, name, slug)}
            onNavigateToProjects={() => onNavigate('projects')}
          />
        </WidgetErrorBoundary>
        
        <WidgetErrorBoundary title="Unable to load recent documents" onRetry={() => retrySection('recent_documents')}>
          <RecentDocuments
            documents={recentDocumentsState.data || []}
            loading={recentDocumentsState.loading && !recentDocumentsState.data}
            error={recentDocumentsState.error}
            onRetry={() => retrySection('recent_documents')}
            onNavigateToDocuments={() => onNavigate('documents')}
          />
        </WidgetErrorBoundary>

        <WidgetErrorBoundary title="Unable to load AI conversations" onRetry={() => retrySection('recent_chats')}>
          <RecentChats
            chats={recentChatsState.data || []}
            loading={recentChatsState.loading && !recentChatsState.data}
            error={recentChatsState.error}
            onRetry={() => retrySection('recent_chats')}
            onNavigateToChat={() => onNavigate('chat')}
          />
        </WidgetErrorBoundary>
      </DashboardGrid>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-3.5">
        <div className="lg:col-span-1">
          <WidgetErrorBoundary title="Unable to load AI insights" onRetry={() => retrySection('ai_summary')}>
            <AIInsights
              insights={aiSummaryState.data?.insights}
              status={aiSummaryState.data?.status}
              loading={aiSummaryState.loading && !aiSummaryState.data}
              error={aiSummaryState.error}
              onRetry={() => retrySection('ai_summary')}
              onNavigateToChat={() => onNavigate('chat')}
            />
          </WidgetErrorBoundary>
        </div>
        <div className="lg:col-span-1">
          <WidgetErrorBoundary title="Unable to load storage metrics">
            <StorageUsage usedBytes={stats.storage_used} />
          </WidgetErrorBoundary>
        </div>
        <div className="lg:col-span-1">
          <WidgetErrorBoundary title="Unable to load starred items" onRetry={() => retrySection('favorites')}>
            <FavoriteList 
              favorites={favorites}
              loading={favoritesState.loading && !favoritesState.data}
              error={favoritesState.error}
              onRetry={() => retrySection('favorites')}
            />
          </WidgetErrorBoundary>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3.5">
        <WidgetErrorBoundary title="Unable to load activity feed" onRetry={() => retrySection('activity')}>
          <ActivityTimeline
            activity={activityState.data || []}
            loading={activityState.loading && !activityState.data}
            error={activityState.error}
            onRetry={() => retrySection('activity')}
            onRefresh={refresh}
          />
        </WidgetErrorBoundary>

        <WidgetErrorBoundary title="Unable to load notifications" onRetry={() => retrySection('notifications')}>
          <NotificationPanel
            notifications={notificationsState.data || []}
            loading={notificationsState.loading && !notificationsState.data}
            error={notificationsState.error}
            onRetry={() => retrySection('notifications')}
            onMarkAsRead={markAsRead}
            onMarkAllRead={markAllAsRead}
            onDelete={deleteNotification}
          />
        </WidgetErrorBoundary>
      </div>
    </div>
  );
}
export default DashboardPage;
