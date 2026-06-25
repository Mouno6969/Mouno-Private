import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient, getErrorMessage } from '../lib/apiClient';
import type { LoginResponse } from '../types';
import { useAuth } from '../context/AuthContext';
import { User, Lock, AlertCircle, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { CardContent, CardFooter } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';

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
      setError(getErrorMessage(err, t('login_failed', 'Login failed')));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex justify-center items-center py-12 px-4">
      <div className="w-full max-w-md rounded-xl border border-border/70 bg-card/90 shadow-lg overflow-hidden">
        <div className="pt-8 pb-4 px-6 text-center space-y-3">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <Lock className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <p className="text-xs font-medium tracking-wider text-muted-foreground">{t('welcome_back', 'Welcome back')}</p>
            <h1 className="text-2xl font-bold tracking-tight">{t('login')}</h1>
            <p className="text-sm text-muted-foreground">{t('login_subtitle', 'Enter your credentials to access your account')}</p>
          </div>
        </div>
        <CardContent className="pt-2">
          {error && (
            <Alert variant="destructive" className="mb-5">
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
                  placeholder={t('enter_username', 'Enter username')}
                  className="pl-10"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">{t('password')}</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder={t('enter_password', 'Enter password')}
                  className="pl-10"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <Button type="submit" className="w-full h-11 font-semibold" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {t('logging_in', 'Logging in...')}
                </>
              ) : (
                t('login')
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col pb-6">
          <p className="text-center text-sm text-muted-foreground">
            {t('no_account', "Don't have an account?")}{" "}
            <Link to="/register" className="text-primary font-medium hover:underline underline-offset-4">
              {t('register_here', 'Register here')}
            </Link>
          </p>
        </CardFooter>
      </div>
    </div>
  );
};

export default Login;
