/**
 * Root component wrapper for entire Docusaurus site
 * This adds the ChatWidget globally across all pages
 */
import React from 'react';
import BrowserOnly from '@docusaurus/BrowserOnly';
import ChatWidget from '../components/ChatWidget';

export default function Root({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <>
      {children}
      <BrowserOnly fallback={<div />}>
        {() => <ChatWidget />}
      </BrowserOnly>
    </>
  );
}
