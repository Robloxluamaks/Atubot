import { useState } from 'react';
import { Check, CircleHelp, Hash, Plus, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { api } from '../../lib/relay-api';
import { useRelay } from '../../context/RelayContext';
import { SectionTitle, Spinner } from './Primitives';

export const ChannelPanel = () => {
  const { channels, setChannels, selected, token, bot, sending, setHelpOpen } = useRelay();
  const [id, setId] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  async function add(e) {
    e.preventDefault(); setError('');
    const value = id.trim();
    if (!/^[0-9]{17,20}$/.test(value)) return setError('ID kanału musi składać się z 17–20 cyfr.');
    if (channels.some(c => c.id === value)) return setError('Ten kanał jest już na liście.');
    if (channels.length >= 10) return setError('Możesz dodać maksymalnie 10 kanałów.');
    setLoading(true);
    try {
      const channel = bot ? await api('/channels/resolve', { token, channel_id: value }) : { id: value, name: `kanał-${value.slice(-4)}` };
      setChannels(prev => prev.some(c => c.id === value) ? prev : [...prev, { ...channel, verified: !!bot, selected: true }]);
      setId('');
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }
  return <section className="channel-panel tool-section">
    <SectionTitle number="02" title="Kanały odbiorców" right={<span data-testid="channel-count" className="small-counter">{channels.length} / 10</span>} />
    <form onSubmit={add}><div className="label-row"><label className="field-label" htmlFor="channel-id">ID kanału <span className="required-dot">*</span></label><button type="button" title="Gdzie znaleźć ID kanału?" aria-label="Gdzie znaleźć ID kanału?" data-testid="channel-help-button" onClick={() => setHelpOpen(true)}><CircleHelp size={14} /></button></div>
      <div className="channel-input-row"><div className="id-field"><Hash size={17} /><Input id="channel-id" data-testid="channel-id-input" inputMode="numeric" maxLength={20} placeholder="np. 123456789012345678" value={id} disabled={sending || loading || channels.length >= 10} onChange={e => { setId(e.target.value); setError(''); }} /></div><Button type="submit" variant="outline" className="add-channel-button" disabled={!id.trim() || sending || loading || channels.length >= 10} data-testid="channel-add-button">{loading ? <Spinner /> : <Plus size={16} />}Dodaj kanał</Button></div>
    </form>
    {error && <p role="alert" data-testid="channel-error" className="inline-error">{error}</p>}
    <div className="channel-list" data-testid="channel-list">
      {channels.length ? channels.map(c => <div key={c.id} className={`channel-item ${c.selected ? 'selected' : ''}`} data-testid={`channel-item-${c.id}`}>
        <button type="button" role="checkbox" aria-checked={c.selected} aria-label={`Wybierz kanał ${c.id}`} className="channel-select" disabled={sending} data-testid={`channel-toggle-${c.id}`} onClick={() => setChannels(prev => prev.map(x => x.id === c.id ? { ...x, selected: !x.selected } : x))}><span className="channel-checkbox">{c.selected && <Check size={12} />}</span><Hash size={17} /><span className="channel-info"><strong>{c.name}</strong><small>{c.id}</small></span></button>
        <button type="button" className="remove-channel" aria-label={`Usuń kanał ${c.id}`} title="Usuń kanał" disabled={sending} data-testid={`channel-delete-${c.id}`} onClick={() => setChannels(prev => prev.filter(x => x.id !== c.id))}><X size={14} /></button>
      </div>) : <div className="empty-channels" data-testid="channels-empty-state"><span className="empty-hash"><Hash size={20} /></span><div>Jeszcze żadnych kanałów<span>Twoi odbiorcy pojawią się tutaj.</span></div><span className="channel-empty-lines"><i /><i /><i /></span></div>}
    </div>
    <div className="channels-footnote"><span data-testid="selected-channel-count">{selected.length} wybranych kanałów</span><span>Maksymalnie 10 kanałów</span></div>
  </section>;
};