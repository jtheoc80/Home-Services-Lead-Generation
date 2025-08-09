/**
 * Staging environment banner component.
 * Displays a prominent banner when running in staging mode.
 */
import React from 'react';
import { config } from '../lib/config';

interface StagingBannerProps {
  className?: string;
  showEnvironmentInfo?: boolean;
}

export const StagingBanner: React.FC<StagingBannerProps> = ({
  className = '',
  showEnvironmentInfo = false,
}) => {
  // Only render in staging environment
  if (!config.features.showStagingBanner) {
    return null;
  }

  return (
    <div
      className={`w-full py-2 px-4 text-center text-sm font-medium text-white ${className}`}
      style={{ backgroundColor: config.ui.stagingBannerColor }}
      role="banner"
      aria-label="Staging environment notice"
    >
      <div className="flex items-center justify-center gap-2">
        <span className="inline-block w-2 h-2 bg-white rounded-full animate-pulse" />
        <span>{config.ui.stagingBannerText}</span>
        <span className="inline-block w-2 h-2 bg-white rounded-full animate-pulse" />
      </div>
      {showEnvironmentInfo && (
        <div className="mt-1 text-xs opacity-90">
          Environment: {config.environment} | API: {config.apiBaseUrl}
        </div>
      )}
    </div>
  );
};

export default StagingBanner;