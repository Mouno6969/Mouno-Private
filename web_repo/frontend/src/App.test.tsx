import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { AuthProvider } from './context/AuthContext';
import App from './App';

// App reads the auth token via useAuth, so it must be rendered inside the
// AuthProvider. With no token in storage, the guest "/" route renders Landing.
describe('App', () => {
  it('renders the guest landing route without crashing', async () => {
    render(
      <AuthProvider>
        <App />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(
        screen.getByText(/I ALREADY HAVE AN ACCOUNT/i)
      ).toBeInTheDocument();
    });
  });
});
