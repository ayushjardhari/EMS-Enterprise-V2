import { NavLink } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import type { UserRole } from '../types';

type Item = { to: string; label: string; icon: string; roles: UserRole[] };
type Group = { label: string; items: Item[] };

const groups: Group[] = [
  { label: 'WORKSPACE', items: [
    { to: '/dashboard', label: 'Overview', icon: '⌂', roles: ['ADMIN','HR','MANAGER','EMPLOYEE'] },
    { to: '/employees', label: 'People', icon: '○', roles: ['ADMIN','HR','MANAGER','EMPLOYEE'] },
    { to: '/projects', label: 'Projects', icon: '▦', roles: ['ADMIN','HR','MANAGER','EMPLOYEE'] },
  ]},
  { label: 'PEOPLE OPERATIONS', items: [
    { to: '/attendance', label: 'Attendance', icon: '◷', roles: ['ADMIN','HR','MANAGER','EMPLOYEE'] },
    { to: '/leave', label: 'Leave', icon: '□', roles: ['ADMIN','HR','MANAGER','EMPLOYEE'] },
    { to: '/payroll', label: 'Payroll', icon: '₹', roles: ['ADMIN','HR'] },
    { to: '/my-payroll', label: 'My payslips', icon: '▤', roles: ['EMPLOYEE'] },
    { to: '/reports', label: 'Reports', icon: '◒', roles: ['ADMIN','HR','MANAGER'] },
  ]},
  { label: 'ADMINISTRATION', items: [
    { to: '/departments', label: 'Departments', icon: '▥', roles: ['ADMIN','HR'] },
    { to: '/roles', label: 'Job roles', icon: '◆', roles: ['ADMIN','HR'] },
    { to: '/skills', label: 'Skills', icon: '✦', roles: ['ADMIN','HR'] },
    { to: '/audit', label: 'Audit logs', icon: '◇', roles: ['ADMIN','HR'] },
    { to: '/settings', label: 'Settings', icon: '⚙', roles: ['ADMIN'] },
  ]},
];

export default function Sidebar() {
  const { user } = useAuth();
  const role = user?.user_role;
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">E</div>
        <div className="brand-copy"><strong>EMS Enterprise</strong><span>People Operations</span></div>
      </div>
      <div className="workspace-switcher">
        <div className="workspace-logo">A</div>
        <div><b>Acme Corporation</b><span>Head office</span></div>
        <span className="chevron">⌄</span>
      </div>
      <nav className="nav-scroll">
        {groups.map(group => {
          const items = group.items.filter(item => role && item.roles.includes(role));
          if (!items.length) return null;
          return <div className="nav-group" key={group.label}>
            <p>{group.label}</p>
            {items.map(item => <NavLink key={item.to} to={item.to} className={({isActive}) => `nav-item${isActive ? ' active' : ''}`}>
              <span className="nav-icon">{item.icon}</span><span>{item.label}</span>
            </NavLink>)}
          </div>;
        })}
      </nav>
      <div className="sidebar-bottom">
        <div className="help-card"><span className="help-icon">?</span><div><b>Need help?</b><small>Open support center</small></div></div>
        <div className="system-status"><span className="online-dot"/><span>All systems operational</span><span className="status-arrow">↗</span></div>
      </div>
    </aside>
  );
}
