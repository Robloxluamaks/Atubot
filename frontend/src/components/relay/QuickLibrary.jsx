import { useEffect, useState } from 'react';
import { Bookmark, FolderOpen } from 'lucide-react';
import { useRelay } from '../../context/RelayContext';
import { api } from '../../lib/relay-api';

export const QuickLibrary = () => {
  const { workspace, loadDraft, setChannels, sending } = useRelay();
  const [templates, setTemplates] = useState([]), [groups, setGroups] = useState([]);
  const [error, setError] = useState('');
  useEffect(() => { if (!workspace) return; let alive = true; Promise.all([api('/library/templates', undefined, 'GET'), api('/library/groups', undefined, 'GET')]).then(([t, g]) => { if (alive) { setTemplates(t); setGroups(g); } }).catch(e => { if (alive) setError(e.message); }); return () => { alive = false; }; }, [workspace]);
  return <div className="quick-library"><div><Bookmark size={15} /><select aria-label="Wczytaj szablon" data-testid="quick-template-select" value="" disabled={sending || !templates.length} onChange={e => { const t = templates.find(t => t.id === e.target.value); if (t) loadDraft(t); }}><option value="">{templates.length ? 'Wczytaj szablon' : 'Brak zapisanych szablonów'}</option>{templates.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}</select></div><div><FolderOpen size={15} /><select aria-label="Wczytaj grupę" data-testid="quick-group-select" value="" disabled={sending || !groups.length} onChange={e => { const g = groups.find(g => g.id === e.target.value); if (g) setChannels(g.channels.map(c => ({ ...c, selected: true, verified: false }))); }}><option value="">{groups.length ? 'Wczytaj grupę kanałów' : 'Brak zapisanych grup'}</option>{groups.map(g => <option key={g.id} value={g.id}>{g.name}</option>)}</select></div>{error && <p className="inline-error" data-testid="quick-library-error">{error}</p>}</div>;
};