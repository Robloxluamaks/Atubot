import { useCallback, useEffect, useState } from 'react';
import { Files, FolderOpen, Plus, RefreshCw } from 'lucide-react';
import { useLocation, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Button } from '../components/ui/button';
import { useRelay } from '../context/RelayContext';
import { api } from '../lib/relay-api';
import { LibraryEditor } from '../components/relay/LibraryEditor';
import { LibraryItem } from '../components/relay/LibraryItem';
import { ConfirmDelete } from '../components/relay/ConfirmDelete';

export default function LibraryPage({ kind }) {
  const { workspace, workspaceError, loadDraft, setChannels, sending } = useRelay();
  const [items, setItems] = useState([]), [loading, setLoading] = useState(true), [error, setError] = useState('');
  const [form, setForm] = useState(null), [busy, setBusy] = useState(false), [saveError, setSaveError] = useState(''), [deleting, setDeleting] = useState(null);
  const template = kind === 'templates';
  const navigate = useNavigate(), location = useLocation();
  const blank = template ? { name: '', content: '', embed: null, overrides: {} } : { name: '', channels: [] };
  const load = useCallback(async () => {
    if (!workspace) return; setLoading(true); setError('');
    try { setItems(await api(`/library/${kind}`, undefined, 'GET')); }
    catch (e) { setError(e.message); } finally { setLoading(false); }
  }, [workspace, kind]);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (location.state?.capture) { setForm({ name: '', ...location.state.capture }); navigate(location.pathname, { replace: true, state: null }); }
  }, [location, navigate]);
  async function save() {
    setBusy(true); setSaveError('');
    try { await api(`/library/${kind}${form.id ? `/${form.id}` : ''}`, form, form.id ? 'PUT' : 'POST'); setForm(null); await load(); toast.success('Zapisano.'); }
    catch (e) { setSaveError(e.message); } finally { setBusy(false); }
  }
  async function remove() {
    setBusy(true);
    try { await api(`/library/${kind}/${deleting.id}`, undefined, 'DELETE'); setDeleting(null); await load(); }
    catch (e) { setError(e.message); setDeleting(null); } finally { setBusy(false); }
  }
  function applyItem(item) {
    if (template) loadDraft(item); else setChannels(item.channels.map(c => ({ ...c, selected: true, verified: false })));
    navigate('/'); toast.success(template ? 'Wczytano szablon.' : 'Wczytano grupę kanałów.');
  }
  const Icon = template ? Files : FolderOpen;
  return <div className="library-page page-enter">
    <div className="page-heading"><div><div className="eyebrow"><span />PRYWATNA BIBLIOTEKA</div><h1>{template ? 'Szablony' : 'Grupy kanałów'}<span>.</span></h1><p>{template ? 'Twój przekaz, gotowy na kolejny raz.' : 'Społeczności uporządkowane po Twojemu.'}</p></div><div className="page-actions"><Button variant="ghost" size="icon" aria-label="Odśwież" title="Odśwież" data-testid={`${kind}-refresh`} disabled={!workspace || loading} onClick={load}><RefreshCw size={16} /></Button><Button data-testid={`${kind}-create`} disabled={!workspace || sending} onClick={() => { setSaveError(''); setForm(blank); }}><Plus size={15} />{template ? 'Nowy szablon' : 'Nowa grupa'}</Button></div></div>
    {(error || workspaceError) && <p role="alert" className="inline-error" data-testid={`${kind}-load-error`}>{error || workspaceError}</p>}
    {loading && !workspaceError ? <p data-testid={`${kind}-loading`} className="muted">Wczytywanie biblioteki…</p> : !items.length ? <div className="empty-history" data-testid={`${kind}-empty`}><div className="empty-history-icon"><Icon size={33} /></div><h2>{template ? 'Dobry przekaz warto zachować.' : 'Każda społeczność ma swoje miejsce.'}</h2><p>{template ? 'Brak zapisanych szablonów.' : 'Brak zapisanych grup kanałów.'}</p></div> : <div className="library-grid">{items.map(item => <LibraryItem key={item.id} item={item} kind={kind} disabled={sending} onApply={() => applyItem(item)} onEdit={() => { setSaveError(''); setForm(structuredClone(item)); }} onDelete={() => setDeleting(item)} />)}</div>}
    <LibraryEditor key={`${kind}-${form?.id || 'new'}`} form={form} setForm={setForm} kind={kind} onSave={save} busy={busy} error={saveError} />
    <ConfirmDelete open={!!deleting} onOpenChange={open => !open && setDeleting(null)} onConfirm={remove} busy={busy} title="Usunąć zapisany wpis?" description={deleting?.name || ''} prefix={`${kind}-delete`} />
  </div>;
}