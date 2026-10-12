import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from 'sonner';
import { RelayProvider } from './context/RelayContext';
import { Layout } from './components/relay/Layout';
import ComposePage from './pages/ComposePage';
import HistoryPage from './pages/HistoryPage';
import LibraryPage from './pages/LibraryPage';
import SchedulesPage from './pages/SchedulesPage';
import PrivacyPage from './pages/PrivacyPage';
import './App.css';
import './features.css';

export default function App() {
  return <BrowserRouter><RelayProvider><Layout><Routes>
    <Route path="/" element={<ComposePage />} />
    <Route path="/historia" element={<HistoryPage />} />
    <Route path="/szablony" element={<LibraryPage kind="templates" />} />
    <Route path="/grupy" element={<LibraryPage kind="groups" />} />
    <Route path="/harmonogram" element={<SchedulesPage />} />
    <Route path="/prywatnosc" element={<PrivacyPage />} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></Layout><Toaster theme="dark" position="bottom-right" richColors closeButton />
  </RelayProvider></BrowserRouter>;
}