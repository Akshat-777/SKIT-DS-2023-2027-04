import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, User, Mail, Lock, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useToast } from '../components/ui/Toast';
import Card, { CardHeader, CardContent, CardFooter } from '../components/ui/Card';
import Button from '../components/ui/Button';
import Input from '../components/ui/Input';
import Badge from '../components/ui/Badge';

export default function RegisterPage() {
  const { register } = useAuth();
  const toast = useToast();
  const navigate = useNavigate();

  const [name, setName] = useState('Aarav Sharma');
  const [email, setEmail] = useState('aarav.sharma@skit.ac.in');
  const [password, setPassword] = useState('CareerLens@2026');
  const [role, setRole] = useState('candidate');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setLoading(true);

    try {
      await register({ name, email, password, role });
      toast.success('Registration Complete', 'Your account has been created successfully!');
      navigate('/upload');
    } catch (err) {
      setErrorMsg(err.message || 'Registration failed.');
      toast.error('Registration Error', err.message || 'Unable to register user.');
    } finally {
      setLoading(false);
    }
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
          Create Your Career Profile
        </h2>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
          Unlock live market benchmarking, ATS scoring, and recruiter critiques
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <Card variant="default" className="shadow-card">
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="primary" size="sm">
                Node.js JWT Auth
              </Badge>
              <span className="text-2xs text-slate-400 font-mono">POST /api/auth/register</span>
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
                label="Full Name"
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Aarav Sharma"
                icon={<User className="w-4 h-4 text-slate-400" />}
              />

              <Input
                label="Academic / Work Email"
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

              <div className="space-y-1.5">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  Account Type
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setRole('candidate')}
                    className={`py-2 px-3 text-xs font-semibold rounded-xl border text-center transition-colors ${
                      role === 'candidate'
                        ? 'border-brand-500 bg-brand-50 dark:bg-brand-950/40 text-brand-600 dark:text-brand-400'
                        : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    Student / Candidate
                  </button>
                  <button
                    type="button"
                    onClick={() => setRole('recruiter')}
                    className={`py-2 px-3 text-xs font-semibold rounded-xl border text-center transition-colors ${
                      role === 'recruiter'
                        ? 'border-brand-500 bg-brand-50 dark:bg-brand-950/40 text-brand-600 dark:text-brand-400'
                        : 'border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    Tech Recruiter / Evaluator
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                variant="primary"
                size="md"
                className="w-full justify-center"
                isLoading={loading}
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
              >
                Create Account & Continue
              </Button>
            </form>
          </CardContent>

          <CardFooter className="flex justify-between items-center text-xs text-slate-500">
            <span>Already registered?</span>
            <Link to="/login" className="font-semibold text-brand-600 hover:underline">
              Sign In
            </Link>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}
