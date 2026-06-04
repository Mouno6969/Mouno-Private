import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import './i18n/config';

import Layout from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Register from './pages/Register';
import Buy from './pages/Buy';
import Swap from './pages/Swap';
import MyWallet from './pages/Wallet';
import Orders from './pages/Orders';
import { useAuth } from './context/AuthContext';

const App: React.FC = () => {
  const { token } = useAuth();

  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/buy" element={token ? <Buy /> : <Navigate to="/login" />} />
          <Route path="/swap" element={<Swap />} />
          <Route path="/wallet" element={<MyWallet />} />
          <Route path="/orders" element={token ? <Orders /> : <Navigate to="/login" />} />
        </Routes>
      </Layout>
    </Router>
  );
};

export default App;
