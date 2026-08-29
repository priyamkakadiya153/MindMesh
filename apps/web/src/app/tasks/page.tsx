'use client';

import React from 'react';
import { TaskDashboard } from '@/features/tasks/components/TaskDashboard';

export default function TasksPage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-6">
      <TaskDashboard />
    </div>
  );
}
