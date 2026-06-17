import React from 'react';
import { useTranslation } from 'react-i18next';
import { Bell, Gift, TrendingUp, ArrowUpRight, CheckCheck, Info } from 'lucide-react';
import { Button } from '../ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from '../ui/dropdown-menu';
import { useNotifications } from '../../lib/hooks';
import { apiClient } from '../../lib/apiClient';
import type { AppNotification, NotificationType } from '../../types';

const ICONS: Record<NotificationType, React.ReactNode> = {
  price_alert: <TrendingUp className="h-4 w-4 text-info" />,
  bonus: <Gift className="h-4 w-4 text-success" />,
  large_tx: <ArrowUpRight className="h-4 w-4 text-warning" />,
  info: <Info className="h-4 w-4 text-muted-foreground" />,
};

const timeAgo = (iso: string, t: ReturnType<typeof useTranslation>['t']) => {
  if (!iso) return '';
  const d = new Date(iso.replace(' ', 'T') + (iso.includes('Z') ? '' : 'Z'));
  const secs = Math.floor((Date.now() - d.getTime()) / 1000);
  if (Number.isNaN(secs)) return '';
  if (secs < 60) return t('just_now', 'just now');
  const mins = Math.floor(secs / 60);
  if (mins < 60) return t('time_minutes', '{{count}}m', { count: mins });
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return t('time_hours', '{{count}}h', { count: hrs });
  return t('time_days', '{{count}}d', { count: Math.floor(hrs / 24) });
};

const NotificationBell: React.FC = () => {
  const { t } = useTranslation();
  const { data, mutate } = useNotifications(true);
  const notifications: AppNotification[] = data?.data?.notifications ?? [];
  const unread = data?.data?.unread ?? 0;

  const markRead = async (id?: number) => {
    try {
      await apiClient.post('/api/notifications/read', id ? { id } : {}, { silent: true });
      mutate();
    } catch {
      /* non-blocking */
    }
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="outline"
          size="icon"
          aria-label={t('aria_notifications', 'Notifications')}
          className="relative h-9 w-9 rounded-xl"
        >
          <Bell className="h-4 w-4" />
          {unread > 0 && (
            <span className="absolute -top-1 -right-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground">
              {unread > 9 ? '9+' : unread}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="w-80 p-0" align="end" forceMount>
        <div className="flex items-center justify-between border-b px-3 py-2">
          <span className="text-sm font-semibold">{t('notifications', 'Notifications')}</span>
          {unread > 0 && (
            <Button variant="ghost" size="sm" className="h-7 gap-1 px-2 text-xs" onClick={() => markRead()}>
              <CheckCheck className="h-3.5 w-3.5" />
              {t('mark_all_read', 'Mark all read')}
            </Button>
          )}
        </div>
        <div className="max-h-96 overflow-y-auto">
          {notifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 px-4 py-10 text-center">
              <Bell className="h-6 w-6 text-muted-foreground/50" />
              <p className="text-sm text-muted-foreground">{t('no_notifications', 'No notifications yet')}</p>
            </div>
          ) : (
            notifications.map((n) => (
              <button
                key={n.id}
                type="button"
                onClick={() => !n.read && markRead(n.id)}
                className={`flex w-full items-start gap-3 border-b border-border/50 px-3 py-3 text-left transition-colors hover:bg-muted/40 ${
                  n.read ? 'opacity-70' : 'bg-primary/5'
                }`}
              >
                <span className="mt-0.5 shrink-0">{ICONS[n.type] ?? ICONS.info}</span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-2">
                    <p className="truncate text-sm font-medium">{n.title}</p>
                    <span className="shrink-0 text-[10px] text-muted-foreground">{timeAgo(n.created_at, t)}</span>
                  </div>
                  {n.body && <p className="mt-0.5 text-xs text-muted-foreground">{n.body}</p>}
                </div>
                {!n.read && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary" />}
              </button>
            ))
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};

export default NotificationBell;
