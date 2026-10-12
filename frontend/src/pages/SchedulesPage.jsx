import { useCallback, useEffect, useState } from 'react';
import { CalendarClock, FilePenLine, Pause, Play, Plus, RefreshCw, Trash2 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { ConfirmDelete } from '../components/relay/ConfirmDelete';
import { DispatchResults } from '../components/relay/DispatchResults';
import { EmbedPreview } from '../components/relay/EmbedPreview';
import { useRelay } from '../context/RelayContext';
import { api } from '../lib/relay-api';
import { scheduleState } from '../lib/drafts';

export default function SchedulesPage() {
  const { workspace, workspaceError, loadDraft, setChannels, sending } = useRelay();
  const [items, setItems] = useState([]), [error, setError] = useState(''), [loading, setLoading] = useState(true), [busy, setBusy] = useState(''), [deleting, setDeleting] = useState(null);
  const navigate = useNavigate();
  const load = useCallback(async () => { if (!workspace) return; setLoading(true); setError(''); try { setItems(await api('/schedules', undefined, 'GET')); } catch (e) { setError(e.message); } finally { setLoading(false); } }, [workspace]);
  useEffect(() => { load(); }, [load]);
  async function action(item, value) { setBusy(item.id); setError(''); try { await api(`/schedules/${item.id}`, { action: value }, 'PATCH'); await load(); } catch (e) { setError(e.message); } finally { setBusy(''); } }
  async function remove() { setBusy(deleting.id); try { await api(`/schedules/${deleting.id}`, undefined, 'DELETE'); setDeleting(null); await load(); } catch (e) { setError(e.message); setDeleting(null); } finally { setBusy(''); } }
  function reuse(item) { loadDraft(item); setChannels(item.channel_ids.map(id => ({ id, name: `kanał-${id.slice(-4)}`, selected: true, verified: false }))); navigate('/'); }
  return <div className="schedules-page page-enter"><div className="page-heading"><div><div className="eyebrow"><span />WIADOMOŚCI NA CZAS</div><h1>Harmonogram<span>.</span></h1><p>Każdy przekaz ma swój moment.</p></div><div className="page-actions"><Button variant="outline" data-testid="schedules-refresh" disabled={!workspace || loading} onClick={load}><RefreshCw size={15} />Odśwież</Button><Button asChild><Link to="/" data-testid="schedule-new-message-link"><Plus size={15} />Nowa wiadomość</Link></Button></div></div>
    <div className="schedule-banner" data-testid="schedules-cadence-notice"><CalendarClock size={19} /><div><strong>Cykl realizacji co 15 minut</strong><p>Wysyłki nie wcześniej niż o zadanej godzinie. Pauza zatrzymuje kolejne wiadomości; już wysłanych nie można cofnąć.</p></div></div>
    {(error || workspaceError) && <p role="alert" className="inline-error" data-testid="schedules-error">{error || workspaceError}</p>}
    {loading && !workspaceError ? <p className="muted loading-line" data-testid="schedules-loading">Wczytywanie harmonogramu…</p> : !items.length ? <div className="empty-history" data-testid="schedules-empty"><div className="empty-history-icon"><CalendarClock size={33} /></div><h2>Na razie bez planów.</h2><p>Brak zaplanowanych wiadomości.</p></div> : <div className="schedule-list">{items.map(item => <article className="schedule-item" key={item.id} data-testid={`schedule-item-${item.id}`}><div className="schedule-item-heading"><div><span className={`schedule-state ${item.state}`} data-testid={`schedule-state-${item.id}`}>{scheduleState[item.state]}</span><h2>{item.name}</h2><small>{item.bot_name} · {item.channel_ids.length} kanałów</small></div><div className="page-actions">{['active', 'running'].includes(item.state) && <Button variant="outline" size="sm" disabled={!!busy} data-testid={`schedule-pause-${item.id}`} onClick={() => action(item, 'pause')}><Pause size={14} />Pauza</Button>}{['paused', 'error'].includes(item.state) && <Button variant="outline" size="sm" disabled={!!busy} data-testid={`schedule-resume-${item.id}`} onClick={() => action(item, 'resume')}><Play size={14} />Wznów</Button>}<Button variant="ghost" size="icon" title="Użyj treści ponownie" aria-label="Użyj treści ponownie" disabled={sending} data-testid={`schedule-reuse-${item.id}`} onClick={() => reuse(item)}><FilePenLine size={15} /></Button><Button variant="ghost" size="icon" title="Usuń harmonogram" aria-label="Usuń harmonogram" disabled={!!busy} data-testid={`schedule-delete-${item.id}`} onClick={() => setDeleting(item)}><Trash2 size={15} /></Button></div></div>
      <div className="schedule-meta"><div><span>Następna wysyłka</span><strong data-testid={`schedule-next-${item.id}`}>{['active', 'running'].includes(item.state) && item.next_run ? new Date(item.next_run).toLocaleString('pl-PL') : '—'}</strong></div><div><span>Powtarzanie</span><strong>{item.interval_minutes === 0 ? 'Jednorazowo' : `Co ${item.interval_minutes} min`}</strong></div><div><span>Wykonane cykle</span><strong data-testid={`schedule-runs-${item.id}`}>{item.run_count} / {item.max_runs}</strong></div></div>
      <p className="schedule-content">{item.content}</p><EmbedPreview embed={item.embed} prefix={`schedule-${item.id}`} />{item.last_error && <p className="inline-error" role="alert" data-testid={`schedule-error-${item.id}`}>{item.last_error}</p>}{item.last_results?.length > 0 && <DispatchResults result={{ results: item.last_results }} prefix={`schedule-${item.id}`} />}
    </article>)}</div>}
    <ConfirmDelete open={!!deleting} onOpenChange={open => !open && setDeleting(null)} onConfirm={remove} busy={!!busy} title="Usunąć harmonogram?" description="Kolejne wysyłki zostaną zatrzymane, a zapisany token usunięty. Rozpoczęta już wiadomość może zostać dostarczona." prefix="schedule-delete" />
  </div>;
}