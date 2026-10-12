import { useState } from 'react';
import { Check, Eye, EyeOff, KeyRound, Link2, LockKeyhole, LogOut, ShieldCheck } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { api } from '../../lib/relay-api';
import { useRelay } from '../../context/RelayContext';
import { BotAvatar, SectionTitle, Spinner, StatusBadge } from './Primitives';

export const ConnectionPanel = () => {
  const { token, setToken, bot, setBot, disconnect, sending, setHelpOpen } = useRelay();
  const [visible, setVisible] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  async function connect(e) {
    e.preventDefault();
    if (!token.trim() || loading) return;
    setLoading(true); setError('');
    try { setBot(await api('/bot/connect', { token })); setVisible(false); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }
  return <section className="connection-panel tool-section">
    <SectionTitle number="01" title="Połączenie z botem" right={<StatusBadge bot={bot} />} />
    {bot ? <div className="connected-profile" data-testid="connected-bot-profile"><BotAvatar bot={bot} /><div><strong data-testid="connected-bot-name">{bot.username}<Check size={14} /></strong><span>Bot gotowy do wysyłki</span></div><Button variant="outline" disabled={sending} data-testid="bot-disconnect-button" onClick={() => { disconnect(); setVisible(false); setError(''); }}><LogOut size={15} />Rozłącz</Button></div> : <form onSubmit={connect}>
      <label className="field-label" htmlFor="bot-token">Token bota <span className="required-dot">*</span></label>
      <div className="connection-input-row"><div className="token-field ph-no-capture ph-sensitive" data-private="true"><KeyRound size={16} /><Input id="bot-token" data-testid="bot-token-input" type={visible ? 'text' : 'password'} autoComplete="off" spellCheck={false} maxLength={204} placeholder="Wklej token swojego bota" value={token} disabled={loading} onChange={e => { setToken(e.target.value); setError(''); }} /><Button type="button" variant="ghost" size="icon" aria-label={visible ? 'Ukryj token' : 'Pokaż token'} title={visible ? 'Ukryj token' : 'Pokaż token'} data-testid="bot-token-toggle-visibility-button" onClick={() => setVisible(!visible)}>{visible ? <EyeOff size={16} /> : <Eye size={16} />}</Button></div><Button className="connect-button" type="submit" disabled={!token.trim() || loading} data-testid="bot-token-connect-button">{loading ? <Spinner /> : <Link2 size={16} />}{loading ? 'Łączenie…' : 'Połącz bota'}</Button></div>
      {error && <p role="alert" data-testid="bot-connection-error" className="inline-error">{error}</p>}
    </form>}
    <div className="connection-footnote"><span><LockKeyhole size={12} />To połączenie nie zapisuje tokenu.</span><button type="button" data-testid="token-help-button" onClick={() => setHelpOpen(true)}>Skąd wziąć token? <span>↗</span></button></div>
    <span className="sr-only"><ShieldCheck />Oficjalne konto bota</span>
  </section>;
};