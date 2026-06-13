import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';
import { AuthProvider } from './context/AuthContext';
import ErrorBoundary from './components/ErrorBoundary';
import { AppSWRConfig } from './lib/swrConfig';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      <AuthProvider>
        <AppSWRConfig>
          <App />
        </AppSWRConfig>
      </AuthProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
