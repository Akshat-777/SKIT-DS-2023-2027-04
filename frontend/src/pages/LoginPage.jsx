import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Sparkles, Mail, Lock, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/ui/Toast';
import Card, { CardHeader, CardContent, CardFooter } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Badge from '../components/ui/Badge';

export default function LoginPage() {
  const { login } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState('aarav.sharma@skit.ac.in');
  const [password, setPassword] = useState('CareerLens@2026');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Destination after login
  const from = location.state?.from?.pathname || '/upload';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setLoading(true);

    try {
      await login(email, password);
      toast.success('Authenticated Successfully', `Welcome back, ${email}!`);
      navigate(from, { replace: true });
    } catch (err) {
      setErrorMsg(err.message || 'Authentication failed. Please verify credentials.');
      toast.error('Authentication Error', err.message || 'Invalid email or password.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemo = (demoEmail) => {
    setEmail(demoEmail);
    setPassword('CareerLens@2026');
  };

  return (
    <div className="min-h-screen flex flex-col justify-center py-12 sm:px-6 lg:px-8 bg-slate-50 dark:bg-slate-925">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link to="/" className="inline-flex items-center gap-2.5 group mb-4">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-brand-600 via-indigo-600 to-violet-500 text-white flex items-center justify-center shadow-glow-brand group-hover:scale-105 transition-transform duration-200">
            <Sparkles className="w-6 h-6" />
          </div>
          <span className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">
            CareerLens
          </span>
        </Link>
        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
          Sign In to Your Workspace
        </h2>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Smart Resume & Market Analysis System • SKIT Final Year Project
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <Card variant="default" className="shadow-card">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="primary" size="sm">
                Node.js JWT Auth
              </Badge>
              <span className="text-2xs text-slate-400 font-mono">auth-service:5000</span>
            </div>
          </CardHeader>

          <CardContent>
            {errorMsg && (
              <div className="mb-4 p-3 rounded-xl bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-900 text-xs text-rose-700 dark:text-rose-300">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Email Address"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@skit.ac.in"
                icon={<Mail className="w-4 h-4 text-slate-400" />}
              />

              <Input
                label="Password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                icon={<Lock className="w-4 h-4 text-slate-400" />}
              />

              <Button
                type="submit"
                variant="primary"
                size="md"
                className="w-full justify-center"
                isLoading={loading}
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
              >
                Sign In
              </Button>
            </form>

            {/* Quick Demo Credentials Switcher */}
            <div className="mt-6 pt-4 border-t border-slate-100 dark:border-slate-800">
              <p className="text-2xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                1-Click Quick Demo Credentials:
              </p>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => handleQuickDemo('aarav.sharma@skit.ac.in')}
                  className="p-2 text-left rounded-lg bg-slate-50 dark:bg-slate-800 hover:bg-brand-50 dark:hover:bg-brand-950/40 border border-slate-200 dark:border-slate-700 transition-colors text-xs"
                >
                  <p className="font-semibold text-slate-900 dark:text-slate-100">Candidate</p>
                  <p className="text-2xs text-slate-500 truncate">Aarav Sharma</p>
                </button>
                <button
                  type="button"
                  onClick={() => handleQuickDemo('recruiter@techventures.ai')}
                  className="p-2 text-left rounded-lg bg-slate-50 dark:bg-slate-800 hover:bg-brand-50 dark:hover:bg-brand-950/40 border border-slate-200 dark:border-slate-700 transition-colors text-xs"
                >
                  <p className="font-semibold text-slate-900 dark:text-slate-100">Recruiter</p>
                  <p className="text-2xs text-slate-500 truncate">Senior Reviewer</p>
                </button>
              </div>
            </div>
          </CardContent>

          <CardFooter className="flex justify-between items-center text-xs text-slate-500">
            <span>Don&apos;t have an account?</span>
            <Link to="/register" className="font-semibold text-brand-600 hover:underline">
              Create account
            </Link>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
