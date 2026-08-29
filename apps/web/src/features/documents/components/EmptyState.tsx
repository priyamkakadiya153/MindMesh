import React from 'react';
import { EmptyState as SharedEmptyState } from '../../../shared/components/EmptyState';

export interface EmptyStateProps {
  title: string;
  description: string;
  onAction?: () => void;
  actionLabel?: string;
  icon?: any;
  secondaryActionLabel?: string;
  onSecondaryAction?: () => void;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  onAction,
  actionLabel,
  icon,
  secondaryActionLabel,
  onSecondaryAction
}) => {
  return (
    <SharedEmptyState
      title={title}
      description={description}
      icon={icon}
      primaryAction={actionLabel ? { label: actionLabel, onClick: onAction } : undefined}
      secondaryAction={secondaryActionLabel ? { label: secondaryActionLabel, onClick: onSecondaryAction } : undefined}
      variant="card"
    />
  );
};

export default EmptyState;
