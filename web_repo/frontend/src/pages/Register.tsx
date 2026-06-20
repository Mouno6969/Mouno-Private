import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { apiClient, getErrorMessage } from '../lib/apiClient';
import { User, Lock, AlertCircle, CheckCircle, Loader2, UserPlus } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { CardContent, CardFooter } from '../components/ui/card';
import { Alert, AlertDescription } from '../components/ui/alert';
import { TexturePanel } from '../components/common';

const Register: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await apiClient.post('/api/register', { username, password }, { silent: true });
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      setError(getErrorMessage(err, 'Registration failed'));
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="flex justify-center items-center py-20 px-4">
        <TexturePanel variant="success" glow scanline accentTop className="w-full max-w-md text-center border-success/40">
          <CardContent className="pt-10 pb-10">
            <div className="w-16 h-16 bg-success/20 text-success rounded-full flex items-center justify-center mx-auto mb-6 animate-bounce ring-glow-success">
              <CheckCircle size={32} />
            </div>
            <h2 className="text-2xl font-bold mb-2 drop-shadow-[0_0_14px_hsl(var(--success)/0.4)]">Registration Successful!</h2>
            <p className="text-muted-foreground">Redirecting to login…</p>
          </CardContent>
        </TexturePanel>
      </div>
    );
  }

  return (
    <div className="relative flex justify-center items-center py-12 px-4 overflow-hidden">
      <div className="absolute inset-0 dot-matrix dot-matrix-fade pointer-events-none" aria-hidden="true" />
      <TexturePanel variant="primary" glow aurora accentTop strong className="relative w-full max-w-md">
        <div className="pt-8 pb-2 px-6 text-center space-y-3">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 ring-1 ring-primary/30 text-primary ring-glow-primary">
            <UserPlus className="h-7 w-7 drop-shadow-[0_0_10px_hsl(var(--primary)/0.6)]" />
          </div>
          <div className="space-y-1">
            <p className="label-eyebrow">Get started</p>
            <h1 className="text-3xl font-bold tracking-tight">{t('register')}</h1>
            <p className="text-sm text-muted-foreground">Create a new account to start trading</p>
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
                  placeholder="Choose a username"
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
                  placeholder="Create a password"
                  className="pl-10"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Confirm your password"
                  className="pl-10"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <Button type="submit" className="w-full h-11" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                t('register')
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col">
          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="text-primary font-medium hover:underline underline-offset-4">
              Login here
            </Link>
          </p>
        </CardFooter>
      </TexturePanel>
    </div>
  );
};

export default Register;
