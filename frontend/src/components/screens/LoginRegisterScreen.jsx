import React, { useState } from 'react';
import { Mail, Lock, User, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';
import Button from '../ui/Button';
import Input from '../ui/Input';
import Card, { CardContent } from '../ui/Card';
import Badge from '../ui/Badge';
import ErrorState from '../ui/ErrorState';
import Spinner from '../ui/Spinner';

export default function LoginRegisterScreen({ state = 'success', onLoginSuccess = () => {} }) {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('aarav.sharma@skit.ac.in');
  const [password, setPassword] = useState('CareerLens@2026');
  const [name, setName] = useState('Aarav Sharma');
  const [submitting, setSubmitting] = useState(false);

  if (state === 'loading') {
    return (
      <div className="flex flex-col items-center justify-center p-12 space-y-4">
        <Spinner size="lg" color="brand" label="Authenticating JWT session..." />
        <p className="text-sm text-slate-500 font-medium">Validating JWT session with Node.js auth-service...</p>
      </div>
    );
  }

  if (state === 'error') {
    return (
      <ErrorState
        error={{
          code: 'AUTH_JWT_EXPIRED',
          message: 'Your authorization token has expired or is invalid. Please sign in again to obtain a fresh JWT token.'
        }}
        onRetry={() => window.location.reload()}
        actionLabel="Re-authenticate"
      />
    );
  }

  const handleSubmit = (e) => {
    e.preventDefault();
    setSubmitting(true);
    setTimeout(() => {
      setSubmitting(false);
      onLoginSuccess();
    }, 800);
  };

  return (
    <div className="max-w-md mx-auto my-6">
      <Card variant="elevated" className="overflow-hidden border-slate-200 dark:border-slate-800">
        {/* Header gradient banner */}
        <div className="p-6 bg-gradient-to-r from-brand-600 via-indigo-600 to-purple-700 text-white relative">
          <div className="flex items-center justify-between mb-3">
            <Badge variant="primary" size="sm" className="bg-white/20 text-white border-white/30 backdrop-blur-xs">
              <Sparkles className="w-3 h-3 mr-1" /> SDG 4: Quality Education
            </Badge>
            <span className="text-2xs font-mono opacity-80">v2.4 Live</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight">
            {isRegister ? 'Create Candidate Account' : 'Welcome to CareerLens'}
          </h2>
          <p className="text-xs text-indigo-100 mt-1 leading-relaxed">
            Smart Resume & Live Market Analysis Engine • SKIT Jaipur
          </p>
        </div>

        <CardContent className="p-6 space-y-5">
          <div className="flex rounded-lg bg-slate-100 dark:bg-slate-800/80 p-1">
            <button
              type="button"
              onClick={() => setIsRegister(false)}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
                !isRegister
                  ? 'bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => setIsRegister(true)}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
                isRegister
                  ? 'bg-white dark:bg-slate-900 text-brand-600 dark:text-brand-400 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400'
              }`}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <Input
                label="Full Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Aarav Sharma"
                leadingIcon={<User className="w-4 h-4" />}
                required
              />
            )}

            <Input
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="candidate@skit.ac.in"
              leadingIcon={<Mail className="w-4 h-4" />}
              helperText="University or personal email ID"
              required
            />

            <Input
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              leadingIcon={<Lock className="w-4 h-4" />}
              required
            />

            <div className="flex items-center justify-between text-xs">
              <label className="flex items-center gap-2 cursor-pointer text-slate-600 dark:text-slate-400">
                <input
                  type="checkbox"
                  defaultChecked
                  className="rounded border-slate-300 text-brand-600 focus:ring-brand-500"
                />
                <span>Remember me</span>
              </label>
              {!isRegister && (
                <a href="#forgot" className="text-brand-600 dark:text-brand-400 hover:underline font-medium">
                  Forgot password?
                </a>
              )}
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full"
              isLoading={submitting}
              icon={<ArrowRight className="w-4 h-4" />}
              iconPosition="right"
            >
              {isRegister ? 'Register Candidate Account' : 'Sign In to Dashboard'}
            </Button>
          </form>

          <div className="pt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-2xs text-slate-500 dark:text-slate-400">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
              Node.js JWT + FastAPI Auth
            </span>
            <span>Final Year Project</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
