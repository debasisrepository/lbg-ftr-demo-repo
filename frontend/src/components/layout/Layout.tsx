import { ReactNode } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-paper">
      <Header />
      <div className="app-layout">
        <Sidebar />
        <main className="app-main p-s5">
          {children}
        </main>
      </div>
    </div>
  );
}
