"use client";

import React from 'react';
import { KnowledgeGovernanceCenter } from '@/features/governance/components/KnowledgeGovernanceCenter';

export default function GovernancePage() {
  return (
    <main className="min-h-screen bg-slate-950 py-8 px-4 font-sans">
      <KnowledgeGovernanceCenter />
    </main>
  );
}
