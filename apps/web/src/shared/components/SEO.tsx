import React, { useEffect } from 'react';

interface SEOProps {
  title?: string;
  description?: string;
}

const DEFAULT_TITLE = 'MindMesh — Transform Conversations into Knowledge';
const DEFAULT_DESCRIPTION = 'AI-Powered Knowledge Intelligence System transforming conversations, files, and project information into structured, searchable organizational memory.';

export const SEO: React.FC<SEOProps> = ({ title, description }) => {
  useEffect(() => {
    // Dynamic document title
    document.title = title ? `${title} | MindMesh` : DEFAULT_TITLE;

    // Dynamic meta description
    let metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
      metaDesc.setAttribute('content', description || DEFAULT_DESCRIPTION);
    }
  }, [title, description]);

  return null;
};

export default SEO;
