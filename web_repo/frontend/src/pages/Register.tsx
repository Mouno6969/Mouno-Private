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
        <div className="w-full max-w-md rounded-xl border border-success/30 bg-card/90 shadow-lg text-center p-10">
          <div className="w-14 h-14 bg-success/15 text-success rounded-full flex items-center justify-center mx-auto mb-5">
            <CheckCircle size={28} />
          </div>
          <h2 className="text-2xl font-bold mb-2">Registration Successful!</h2>
          <p className="text-muted-foreground text-sm">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-center items-center py-12 px-4">
      <div className="w-full max-w-md rounded-xl border border-border/70 bg-card/90 shadow-lg overflow-hidden">
        <div className="pt-8 pb-4 px-6 text-center space-y-3">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <UserPlus className="h-6 w-6" />
          </div>
          <div className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Get started</p>
            <h1 className="text-2xl font-bold tracking-tight">{t('register')}</h1>
            <p className="text-sm text-muted-foreground">Create a new account to start trading</p>
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

            <Button type="submit" className="w-full h-11 font-semibold" disabled={loading}>
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
        <CardFooter className="flex flex-col pb-6">
          <p className="text-center text-sm text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="text-primary font-medium hover:underline underline-offset-4">
              Login here
            </Link>
          </p>
        </CardFooter>
      </div>
    </div>
  );
};

export default Register;
