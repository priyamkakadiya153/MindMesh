'use client';

import React from 'react';
import { useParams } from 'next/navigation';
import { ProjectIntelligence } from '@/features/projects/components/ProjectIntelligence';

export default function ProjectIntelligencePage() {
  const params = useParams();
  const projectId = (params?.id as string) || '';

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-6">
      <ProjectIntelligence projectId={projectId} />
    </div>
  );
}
