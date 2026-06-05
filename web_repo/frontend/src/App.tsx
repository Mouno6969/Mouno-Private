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
import Referral from './pages/Referral';
import GiftCode from './pages/GiftCode';
import Support from './pages/Support';
import Seller from './pages/Seller';
import LinkTelegram from './pages/LinkTelegram';
import { Toaster } from 'sonner';
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
          <Route path="/referral" element={token ? <Referral /> : <Navigate to="/login" />} />
          <Route path="/gift" element={token ? <GiftCode /> : <Navigate to="/login" />} />
          <Route path="/support" element={token ? <Support /> : <Navigate to="/login" />} />
          <Route path="/seller" element={token ? <Seller /> : <Navigate to="/login" />} />
          <Route path="/link-telegram" element={token ? <LinkTelegram /> : <Navigate to="/login" />} />
        </Routes>
      </Layout>
      <Toaster richColors position="top-center" />
    </Router>
  );
};

export default App;
