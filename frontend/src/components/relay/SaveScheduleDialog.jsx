import { useState } from 'react';
import { CalendarClock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Checkbox } from '../ui/checkbox';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog';
import { useRelay } from '../../context/RelayContext';
import { api } from '../../lib/relay-api';

function initialTime() { const date = new Date(Math.ceil((Date.now() + 60000) / 900000) * 900000); const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000); return local.toISOString().slice(0, 16); }

export const SaveScheduleDialog = ({ open, onOpenChange }) => {
  const { token, bot, selected, draft, workspace, draftReady } = useRelay();
  const [name, setName] = useState(''), [time, setTime] = useState(initialTime), [interval, setInterval] = useState('0'), [count, setCount] = useState(24), [consent, setConsent] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('');
  const navigate = useNavigate();
  async function save(e) {
    e.preventDefault(); setBusy(true); setError('');
    try { await api('/schedules', { token, ...draft, channel_ids: selected.map(c => c.id), name, next_run: new Date(time).toISOString(), interval_minutes: Number(interval), max_runs: interval === '0' ? 1 : Number(count), consent }); onOpenChange(false); navigate('/harmonogram'); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  return <Dialog open={open} onOpenChange={value => !busy && onOpenChange(value)}><DialogContent className="relay-dialog" data-testid="schedule-create-dialog"><DialogHeader><DialogTitle>Wiadomość na właściwy moment.</DialogTitle><DialogDescription>{bot?.username} · {selected.length} kanałów · {Intl.DateTimeFormat().resolvedOptions().timeZone}</DialogDescription></DialogHeader><form onSubmit={save}>
    <label className="form-field">Nazwa harmonogramu<Input required maxLength={80} value={name} data-testid="schedule-name-input" placeholder="np. Ogłoszenie wieczorne" onChange={e => setName(e.target.value)} /></label><label className="form-field">Pierwsza wysyłka — czas lokalny<Input type="datetime-local" required value={time} data-testid="schedule-time-input" onChange={e => setTime(e.target.value)} /></label>
    <div className="form-grid equal"><label className="form-field">Powtarzanie<select value={interval} data-testid="schedule-interval-select" onChange={e => setInterval(e.target.value)}>{[['0','Tylko raz'],['15','Co 15 minut'],['30','Co 30 minut'],['60','Co godzinę'],['180','Co 3 godziny'],['360','Co 6 godzin'],['720','Co 12 godzin'],['1440','Co 24 godziny'],['10080','Co 7 dni']].map(([v, text]) => <option key={v} value={v}>{text}</option>)}</select></label><label className="form-field">Liczba wysyłek<Input type="number" min={1} max={1000} required disabled={interval === '0'} value={interval === '0' ? 1 : count} data-testid="schedule-count-input" onChange={e => setCount(e.target.value)} /></label></div>
    <p className="schedule-timing-note" data-testid="schedule-timing-note">Realizacja w pierwszym cyklu po wskazanej godzinie. Cykl: co 15 minut. Ważność do {workspace ? new Date(workspace.expires_at).toLocaleDateString('pl-PL') : '—'}.</p>
    <label className="schedule-consent"><Checkbox checked={consent} onCheckedChange={setConsent} data-testid="schedule-token-consent" /><span>Zgadzam się na zaszyfrowany zapis tokenu bota dla tego harmonogramu. Token zostanie usunięty po zakończeniu, usunięciu lub wygaśnięciu zadania.</span></label>
    {error && <p role="alert" className="inline-error" data-testid="schedule-create-error">{error}</p>}<div className="dialog-actions"><Button type="button" variant="outline" disabled={busy} data-testid="schedule-cancel-button" onClick={() => onOpenChange(false)}>Anuluj</Button><Button type="submit" disabled={busy || !consent || !name.trim() || !workspace || !draftReady || !token || !selected.length} data-testid="schedule-save-button"><CalendarClock size={16} />{busy ? 'Zapisywanie…' : 'Zaplanuj wysyłkę'}</Button></div>
  </form></DialogContent></Dialog>;
};