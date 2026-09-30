import React, { useEffect, useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Menu, Activity, Sparkles, ChevronRight, Layers } from 'lucide-react';
import { healthApi } from '../../api';

interface TopbarProps {
  onOpenMobile: () => void;
}

export const Topbar: React.FC<TopbarProps> = ({ onOpenMobile }) => {
  const location = useLocation();
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    let isMounted = true;
    healthApi
      .getHealth()
      .then(() => {
        if (isMounted) setIsBackendHealthy(true);
      })
      .catch(() => {
        if (isMounted) setIsBackendHealthy(false);
      });
    return () => {
      isMounted = false;
    };
  }, [location.pathname]);

  // Generate breadcrumbs from route path
  const pathParts = location.pathname.split('/').filter(Boolean);
  const breadcrumbItems = pathParts.map((part, index) => {
    const url = `/${pathParts.slice(0, index + 1).join('/')}`;
    return { name: part.charAt(0).toUpperCase() + part.slice(1).replace('-', ' '), url };
  });

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between sticky top-0 z-20">
      {/* Left: Mobile hamburger & Breadcrumbs */}
      <div className="flex items-center space-x-4">
        <button
          onClick={onOpenMobile}
          className="lg:hidden p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg"
          aria-label="Open sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <nav aria-label="Breadcrumb" className="flex items-center space-x-2 text-xs text-slate-500">
          <Link to="/dashboard" className="hover:text-brand-900 font-medium">
            Platform
          </Link>
          {breadcrumbItems.map((item, index) => (
            <React.Fragment key={item.url}>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
              {index === breadcrumbItems.length - 1 ? (
                <span className="font-semibold text-slate-900">{item.name}</span>
              ) : (
                <Link to={item.url} className="hover:text-brand-900">
                  {item.name}
                </Link>
              )}
            </React.Fragment>
          ))}
        </nav>
      </div>

      {/* Right: Quick actions & Backend Health */}
      <div className="flex items-center space-x-4">
        {/* Backend Connectivity Status */}
        <div className="flex items-center space-x-2 px-3 py-1 bg-slate-50 border border-slate-200 rounded-full text-xs">
          <span
            className={`w-2 h-2 rounded-full ${
              isBackendHealthy === true
                ? 'bg-emerald-500 animate-pulse'
                : isBackendHealthy === false
                ? 'bg-red-500'
                : 'bg-amber-400'
            }`}
          />
          <span className="text-[11px] font-medium text-slate-600">
            {isBackendHealthy === true
              ? 'Backend Online'
              : isBackendHealthy === false
              ? 'Backend Reconnecting'
              : 'Verifying Gateway'}
          </span>
        </div>
      </div>
    </header>
  );
};
