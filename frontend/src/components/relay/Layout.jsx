import { ArrowUpRight, CalendarClock, ChevronRight, CircleHelp, Clock3, Files, FolderOpen, Hash, LockKeyhole, MessageSquareText, Radio, ShieldCheck } from 'lucide-react';
import { NavLink, useLocation } from 'react-router-dom';
import { Button } from '../ui/button';
import { useRelay } from '../../context/RelayContext';
import { Brand, StatusBadge } from './Primitives';
import { HelpDialog } from './HelpDialog';

export const Layout = ({ children }) => {
  const { bot, setHelpOpen, history, workspaceError } = useRelay();
  const path = useLocation().pathname;
  const titles = { '/': 'Wiadomości', '/historia': 'Historia wysyłek', '/szablony': 'Szablony', '/grupy': 'Grupy kanałów', '/harmonogram': 'Harmonogram', '/prywatnosc': 'Twoje dane' };
  return <div className="app-shell">
    <aside className="sidebar">
      <NavLink to="/" className="brand-link" data-testid="brand-home-link"><Brand /></NavLink>
      <div className="sidebar-caption">DISCORD AUTOSENDER</div>
      <div className="nav-label">TWOJA PRZESTRZEŃ</div>
      <nav aria-label="Nawigacja główna">
        <NavLink to="/" end data-testid="nav-messages" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><MessageSquareText size={19} />Wiadomości<ChevronRight className="nav-arrow" size={14} /></NavLink>
        <NavLink to="/historia" data-testid="nav-history" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><Clock3 size={19} />Historia wysyłek{history.length > 0 && <span className="nav-count" data-testid="history-count">{history.length}</span>}</NavLink>
        <NavLink to="/szablony" data-testid="nav-templates" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><Files size={19} />Szablony</NavLink>
        <NavLink to="/grupy" data-testid="nav-groups" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><FolderOpen size={19} />Grupy kanałów</NavLink>
        <NavLink to="/harmonogram" data-testid="nav-schedules" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><CalendarClock size={19} />Harmonogram</NavLink>
        <NavLink to="/prywatnosc" data-testid="nav-privacy" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}><ShieldCheck size={19} />Twoje dane</NavLink>
      </nav>
      <div className="sidebar-bottom">
        <div className="setup-teaser"><div className="setup-art"><img src="/discord.jpg" alt="Logo Discord" /><span>Dobry początek<br />dla Twojego bota.</span></div><Button variant="ghost" data-testid="sidebar-help-button" onClick={() => setHelpOpen(true)}>Konfiguracja bota<ArrowUpRight size={15} /></Button></div>
        <div className="sidebar-security"><ShieldCheck size={17} /><span>Twoje dane pod ochroną.</span></div>
        <div className="sidebar-version"><span>RELAY / v1.1</span><span className="tiny-dot" />Zbudowane dla społeczności</div>
      </div>
    </aside>
    <div className="workspace">
      <header className="topbar"><div className="breadcrumbs"><Hash size={16} /><span>Twoja przestrzeń</span><ChevronRight size={13} /><strong>{titles[path]}</strong></div><div className="header-actions"><span className="secure-session"><LockKeyhole size={13} />Prywatna przestrzeń</span><Button variant="ghost" size="icon" data-testid="header-help-button" title="Pomoc i konfiguracja" aria-label="Pomoc i konfiguracja" onClick={() => setHelpOpen(true)}><CircleHelp size={18} /></Button></div></header>
      {workspaceError && <div role="alert" className="workspace-alert" data-testid="workspace-session-error">Nie można otworzyć prywatnej przestrzeni: {workspaceError}</div>}
      <main className="main-content">{children}</main>
      <footer className="workspace-footer"><span><Radio size={14} /> Oficjalne API Discord</span><StatusBadge bot={bot} testId="footer-connection-status" /><span>Mała wiadomość. Duży zasięg.</span></footer>
    </div>
    <HelpDialog />
  </div>;
};