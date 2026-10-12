import { Hash, Split, X } from 'lucide-react';
import { Textarea } from '../ui/textarea';
import { Button } from '../ui/button';
import { useRelay } from '../../context/RelayContext';

export const ChannelVariants = () => {
  const { selected, overrides, setOverrides, message, sending } = useRelay();
  if (!selected.length) return null;
  function clear(id) { setOverrides(prev => { const next = { ...prev }; delete next[id]; return next; }); }
  return <div className="channel-variants"><div className="feature-heading"><span><Split size={16} />Treść dla poszczególnych kanałów</span></div>{selected.map(c => <div key={c.id} className="variant-row"><div><span><Hash size={13} />{c.name}</span>{overrides[c.id] === undefined ? <Button variant="ghost" size="sm" data-testid={`variant-add-${c.id}`} disabled={sending} onClick={() => setOverrides(prev => ({ ...prev, [c.id]: message }))}>Osobna treść</Button> : <Button variant="ghost" size="sm" data-testid={`variant-clear-${c.id}`} disabled={sending} onClick={() => clear(c.id)}><X size={12} />Wspólna treść</Button>}</div>{overrides[c.id] !== undefined && <><Textarea aria-label={`Wiadomość dla ${c.name}`} maxLength={2000} data-testid={`variant-text-${c.id}`} value={overrides[c.id]} disabled={sending} onChange={e => setOverrides(prev => ({ ...prev, [c.id]: e.target.value }))} /><small data-testid={`variant-counter-${c.id}`}>{overrides[c.id].length} / 2000</small></>}</div>)}</div>;
};