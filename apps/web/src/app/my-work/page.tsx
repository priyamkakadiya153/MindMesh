'use client';

import React from 'react';
import { MyWorkDashboard } from '@/features/me/components/MyWorkDashboard';

export default function MyWorkPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-6">
      <MyWorkDashboard />
    </div>
  );
}
