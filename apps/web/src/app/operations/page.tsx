"use client";

import React from 'react';
import { KnowledgeOperationsDashboard } from '@/features/operations/components/KnowledgeOperationsDashboard';

export default function OperationsPage() {
  return (
    <main className="min-h-screen bg-slate-950 py-8 px-4 font-sans">
      <KnowledgeOperationsDashboard />
    </main>
  );
}
