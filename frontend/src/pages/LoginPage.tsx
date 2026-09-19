import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ApiError } from '../services/api';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email,setEmail] = useState(''); const [password,setPassword] = useState(''); const [error,setError] = useState<string|null>(null); const [submitting,setSubmitting] = useState(false);
  const submit = async (e:React.FormEvent) => { e.preventDefault(); setError(null); setSubmitting(true); try { await login(email,password); navigate('/dashboard'); } catch(err) { setError(err instanceof ApiError ? err.message : 'Unable to sign in. Please try again.'); } finally { setSubmitting(false); } };
  return <div className="login-shell">
    <div className="login-art"><div className="art-grid"/><div className="art-content"><div className="login-brand"><span className="brand-mark">E</span><span><b>EMS Enterprise</b><small>People Operations Platform</small></span></div><div className="art-copy"><span className="pill">WORKFORCE OPERATIONS</span><h1>One workspace for your entire people operation.</h1><p>Connect employees, attendance, leave, payroll and projects in one secure enterprise platform.</p></div><div className="art-stat"><div><b>100+</b><span>employees managed</span></div><div><b>24/7</b><span>operational visibility</span></div><div><b>1</b><span>connected workspace</span></div></div></div></div>
    <div className="login-panel"><div className="login-form-wrap"><div className="mobile-login-brand"><span className="brand-mark">E</span><div><b>EMS Enterprise</b><small>People Operations</small></div></div><div className="login-heading"><span>WELCOME BACK</span><h2>Sign in to your workspace</h2><p>Use your company credentials to continue.</p></div>
      <form onSubmit={submit} className="login-form"><label>Email address<input type="email" required value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@company.com" autoComplete="email"/></label><label>Password<div className="password-field"><input type="password" required value={password} onChange={e=>setPassword(e.target.value)} placeholder="Enter your password" autoComplete="current-password"/></div></label>{error&&<div className="login-error">{error}</div>}<button className="login-submit" disabled={submitting}>{submitting?'Signing you in…':'Sign in'}<span>→</span></button></form>
      <div className="login-demo"><span>Demo access</span><p>admin@acmecorp.example <b>·</b> Admin@123</p></div><p className="login-footer">Protected workforce data · Secure session · EMS Enterprise</p>
    </div></div>
  </div>;
}
