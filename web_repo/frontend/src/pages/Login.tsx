import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient, getErrorMessage } from '../lib/apiClient';
import type { LoginResponse } from '../types';
import { useAuth } from '../context/AuthContext';
import { User, Lock, AlertCircle, Loader2, ShieldCheck } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { CardContent, CardFooter } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { TexturePanel } from '../components/common';

const Login: React.FC = () => {
  const { t } = useTranslation();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await apiClient.post<LoginResponse>(
        '/api/login',
        { username, password },
        { silent: true }
      );
      login(res.data.username, res.data.token, res.data.telegram_id);
      navigate('/');
    } catch (err) {
      setError(getErrorMessage(err, 'Login failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex justify-center items-center py-12 px-4 overflow-hidden">
      <div className="absolute inset-0 dot-matrix dot-matrix-fade pointer-events-none" aria-hidden="true" />
      <TexturePanel variant="primary" glow aurora accentTop strong className="relative w-full max-w-md">
        <div className="pt-8 pb-2 px-6 text-center space-y-3">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 ring-1 ring-primary/30 text-primary ring-glow-primary">
            <ShieldCheck className="h-7 w-7 drop-shadow-[0_0_10px_hsl(var(--primary)/0.6)]" />
          </div>
          <div className="space-y-1">
            <p className="label-eyebrow">Welcome back</p>
            <h1 className="text-3xl font-bold tracking-tight">{t('login')}</h1>
            <p className="text-sm text-muted-foreground">Enter your credentials to access your account</p>
          </div>
        </div>
        <CardContent className="pt-4">
          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">{t('username')}</Label>
              <div className="relative">
                <User className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="username"
                  placeholder="Enter username"
                  className="pl-10"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">{t('password')}</Label>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="Enter password"
                  className="pl-10"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <Button type="submit" className="w-full h-11" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Logging in...
                </>
              ) : (
                t('login')
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col">
          <p className="text-center text-sm text-muted-foreground">
            Don't have an account?{" "}
            <Link to="/register" className="text-primary font-medium hover:underline underline-offset-4">
              Register here
            </Link>
          </p>
        </CardFooter>
      </TexturePanel>
    </div>
  );
};

export default Login;
