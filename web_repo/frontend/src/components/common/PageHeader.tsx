import React from 'react';
import { Link } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface Crumb {
  label: string;
  to?: string;
}

interface PageHeaderProps {
  title: React.ReactNode;
  /** Small uppercase eyebrow above the title. */
  eyebrow?: string;
  /** Supporting line under the title. */
  description?: React.ReactNode;
  /** Leading icon next to the title. */
  icon?: React.ReactNode;
  /** Right-aligned actions (buttons, etc). */
  actions?: React.ReactNode;
  /** Breadcrumb trail for deep pages. */
  breadcrumbs?: Crumb[];
  className?: string;
}

/** Consistent page title bar with optional breadcrumbs, eyebrow and actions. */
export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  eyebrow,
  description,
  icon,
  actions,
  breadcrumbs,
  className,
}) => (
  <div className={cn('mb-6', className)}>
    {breadcrumbs && breadcrumbs.length > 0 && (
      <nav aria-label="Breadcrumb" className="mb-2">
        <ol className="flex items-center gap-1 text-xs text-muted-foreground">
          {breadcrumbs.map((c, i) => (
            <li key={i} className="flex items-center gap-1">
              {c.to ? (
                <Link to={c.to} className="hover:text-foreground transition-colors">{c.label}</Link>
              ) : (
                <span className="text-foreground">{c.label}</span>
              )}
              {i < breadcrumbs.length - 1 && <ChevronRight className="h-3 w-3" aria-hidden="true" />}
            </li>
          ))}
        </ol>
      </nav>
    )}
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div className="min-w-0">
        {eyebrow && <p className="label-eyebrow mb-1">{eyebrow}</p>}
        <h1 className="flex items-center gap-2 text-2xl sm:text-3xl font-extrabold tracking-tight text-foreground">
          {icon && <span className="text-primary shrink-0">{icon}</span>}
          {title}
        </h1>
        {description && (
          <p className="mt-1.5 text-sm text-muted-foreground max-w-2xl">{description}</p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </div>
  </div>
);

export default PageHeader;
