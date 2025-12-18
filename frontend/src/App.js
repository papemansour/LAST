import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import { CurrencyProvider } from './components/CurrencySelector';
import '@/App.css';

import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import StudentDashboard from './pages/StudentDashboard';
import KidDashboard from './pages/KidDashboard';
import TeacherDashboard from './pages/TeacherDashboard';
import AdminDashboard from './pages/AdminDashboard';
import SecretaryLogin from './pages/SecretaryLogin';
import SecretaryDashboard from './pages/SecretaryDashboard';
import TestPage from './pages/TestPage';
import LegalPage from './pages/LegalPage';
import CGUPage from './pages/CGUPage';
import PrivacyPage from './pages/PrivacyPage';
import Kalamatheque from './pages/Kalamatheque';
import KalamathequeAccess from './pages/KalamathequeAccess';
import BookReader from './pages/BookReader';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <CurrencyProvider>
      <div className="App">
        <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/test/:level" element={<TestPage />} />
          <Route path="/legal" element={<LegalPage />} />
          <Route path="/cgu" element={<CGUPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/library" element={<Kalamatheque />} />
          <Route path="/kalamatheque-access" element={<KalamathequeAccess />} />
          <Route path="/kalamatheque" element={<Kalamatheque />} />
          <Route path="/kalamatheque/reader/:id" element={<BookReader />} />
          
          <Route path="/student/*" element={
            <ProtectedRoute allowedRoles={['student']}>
              <StudentDashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/kid-dashboard/*" element={
            <ProtectedRoute allowedRoles={['student']}>
              <KidDashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/teacher/*" element={
            <ProtectedRoute allowedRoles={['teacher']}>
              <TeacherDashboard />
            </ProtectedRoute>
          } />
          
          <Route path="/admin/*" element={
            <ProtectedRoute allowedRoles={['admin']}>
              <AdminDashboard />
            </ProtectedRoute>
          } />
        </Routes>
        </BrowserRouter>
        <Toaster position="top-center" richColors />
      </div>
    </CurrencyProvider>
  );
}

export default App;
