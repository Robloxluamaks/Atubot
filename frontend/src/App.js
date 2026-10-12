import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'sonner';
import { RelayProvider } from './context/RelayContext';
import { Layout } from './components/relay/Layout';
import ComposePage from './pages/ComposePage';
import HistoryPage from './pages/HistoryPage';
import './App.css';

export default function App() {
  return <BrowserRouter><RelayProvider><Layout><Routes>
    <Route path="/" element={<ComposePage />} />
    <Route path="/historia" element={<HistoryPage />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></Layout><Toaster theme="dark" position="bottom-right" richColors closeButton />
  </RelayProvider></BrowserRouter>;
}