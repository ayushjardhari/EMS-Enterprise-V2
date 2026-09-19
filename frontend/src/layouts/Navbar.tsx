import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const titles: Record<string,string> = {
  '/dashboard':'Overview','/employees':'People','/projects':'Projects','/attendance':'Attendance','/leave':'Leave','/payroll':'Payroll','/my-payroll':'My payslips','/reports':'Reports','/audit':'Audit logs','/settings':'Settings','/departments':'Departments','/roles':'Job roles','/skills':'Skills'
};

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const name = user?.email?.split('@')[0] ?? 'User';
  const displayName = name.split(/[._-]/).map(s => s.charAt(0).toUpperCase()+s.slice(1)).join(' ');
  return <header className="topbar">
    <div className="mobile-brand"><div className="brand-mark small">E</div><strong>EMS</strong></div>
    <div className="crumb"><span>Workspace</span><b>/</b><strong>{titles[location.pathname] ?? 'Workspace'}</strong></div>
    <div className="topbar-actions">
      <label className="global-search"><span>⌕</span><input placeholder="Search people, projects..."/><kbd>⌘ K</kbd></label>
      <button className="icon-button" aria-label="Help">?</button>
      <button className="icon-button notification-button" aria-label="Notifications"><span>♢</span><i/></button>
      <div className="top-divider"/>
      <button className="profile-button" onClick={() => navigate('/settings')}>
        <span className="avatar">{displayName.charAt(0)}</span><span className="profile-meta"><b>{displayName}</b><small>{user?.user_role ?? 'USER'}</small></span><span className="chevron">⌄</span>
      </button>
      <button className="signout-button" onClick={logout}>Sign out</button>
    </div>
  </header>;
}
