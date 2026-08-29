import { useAuth } from '../../auth/auth-provider';
import { Building, Loader2, Plus } from 'lucide-react';
import { useNavigationStore } from '../store';

export function OrganizationSwitcher() {
  const { organizations, currentOrg, switchOrganization, loading } = useAuth();
  const { setActiveTab } = useNavigationStore();

  if (loading) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-borderColor bg-bgCard px-2.5 sm:px-3 min-h-[44px] sm:min-h-[38px] text-xs text-textMuted shrink-0">
        <Loader2 className="h-3.5 w-3.5 animate-spin text-accent" />
        <span className="hidden sm:inline">Loading Orgs...</span>
      </div>
    );
  }

  if (organizations.length === 0) {
    return (
      <button
        onClick={() => setActiveTab('organizations')}
        className="flex items-center gap-1.5 rounded-xl border border-dashed border-accent/30 bg-accentSubtle hover:bg-accent/20 px-3 min-h-[44px] sm:min-h-[38px] text-xs font-semibold text-accentText transition-all shrink-0 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
      >
        <Plus size={14} />
        <span className="truncate max-w-[130px] sm:max-w-none">Create Organization</span>
      </button>
    );
  }

  return (
    <div className="relative flex items-center gap-1.5 sm:gap-2 rounded-xl border border-borderColor bg-bgCard px-2.5 sm:px-3 min-h-[44px] sm:min-h-[38px] backdrop-blur-md transition-all duration-150 hover:bg-bgHover focus-within:ring-2 focus-within:ring-accent shrink-0 max-w-[150px] sm:max-w-[210px] md:max-w-[250px]">
      {currentOrg?.logo_url ? (
        <img 
          src={currentOrg.logo_url} 
          alt={currentOrg?.name ? `${currentOrg.name} logo` : "Organization logo"} 
          className="h-4 w-4 rounded-md object-cover shrink-0"
          onError={(e) => {
            (e.target as HTMLElement).style.display = 'none';
          }}
        />
      ) : (
        <Building size={14} className="text-accent shrink-0" aria-hidden="true" />
      )}
      
      <select
        value={currentOrg?.id || ''}
        onChange={(e) => {
          const org = organizations.find((o) => o.id === e.target.value);
          if (org) switchOrganization(org);
        }}
        aria-label="Select organization"
        title="Select organization"
        className="bg-transparent text-xs font-semibold text-textPrimary outline-none cursor-pointer pr-1 truncate max-w-[100px] sm:max-w-[150px] md:max-w-[180px] focus-visible:ring-2 focus-visible:ring-accent rounded-md"
      >
        {organizations.map((org) => (
          <option key={org.id} value={org.id} className="bg-bgDialog text-textPrimary">
            {org.name}
          </option>
        ))}
      </select>
    </div>
  );
}
export default OrganizationSwitcher;


