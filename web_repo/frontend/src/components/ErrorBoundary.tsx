import React from 'react';

interface ErrorBoundaryProps {
  children: React.ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Catches runtime errors anywhere in the React tree so that a single
 * failing component never unmounts the whole app and leaves a blank page.
 * Instead of a "white screen of death", the user sees a readable error
 * and a way to recover.
 */
class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Surface the real error in the console for debugging on deployed sites.
    console.error('[v0] Uncaught render error:', error, info);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          role="alert"
          style={{
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '16px',
            padding: '24px',
            textAlign: 'center',
            background: '#0a0a0a',
            color: '#fafafa',
            fontFamily: 'system-ui, -apple-system, sans-serif',
          }}
        >
          <h1 style={{ fontSize: '20px', fontWeight: 700, margin: 0 }}>
            কিছু একটা সমস্যা হয়েছে
          </h1>
          <p style={{ fontSize: '14px', opacity: 0.7, maxWidth: '420px', margin: 0 }}>
            পেজটি লোড করতে গিয়ে একটি ত্রুটি হয়েছে। নিচের বাটনে ক্লিক করে আবার চেষ্টা করুন।
          </p>
          {this.state.error?.message && (
            <pre
              style={{
                fontSize: '12px',
                opacity: 0.6,
                maxWidth: '90vw',
                overflowX: 'auto',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                margin: 0,
              }}
            >
              {this.state.error.message}
            </pre>
          )}
          <button
            onClick={this.handleReload}
            style={{
              marginTop: '8px',
              padding: '10px 20px',
              borderRadius: '8px',
              border: '1px solid #fafafa',
              background: '#fafafa',
              color: '#0a0a0a',
              fontWeight: 600,
              fontSize: '14px',
              cursor: 'pointer',
            }}
          >
            আবার লোড করুন
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
