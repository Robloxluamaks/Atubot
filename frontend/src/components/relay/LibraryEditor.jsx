import { useState } from 'react';
import { Plus, Save, X } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog';
import { EmbedEditor } from './EmbedEditor';
import { validEmbed } from '../../lib/drafts';

export const LibraryEditor = ({ form, setForm, kind, onSave, busy, error }) => {
  const [channelId, setChannelId] = useState('');
  const [channelError, setChannelError] = useState('');
  const isTemplate = kind === 'templates';
  const update = (key, value) => setForm(prev => ({ ...prev, [key]: value }));
  function addChannel() {
    if (!/^[0-9]{17,20}$/.test(channelId) || form.channels.some(c => c.id === channelId)) return setChannelError('Podaj unikalne ID: 17–20 cyfr.');
    update('channels', [...form.channels, { id: channelId, name: `kanał-${channelId.slice(-4)}` }]); setChannelId(''); setChannelError('');
  }
  const valid = form && form.name.trim() && (isTemplate ? validEmbed(form.embed) && (form.content.trim() || form.embed || Object.values(form.overrides || {}).some(v => v.trim())) : form.channels.length > 0);
  return <Dialog open={!!form} onOpenChange={open => { if (!open && !busy) setForm(null); }}><DialogContent className="relay-dialog library-editor" data-testid={`${kind}-editor-dialog`}><DialogHeader><DialogTitle>{form?.id ? 'Edytuj' : 'Nowy'} {isTemplate ? 'szablon' : 'zestaw kanałów'}</DialogTitle><DialogDescription>{isTemplate ? 'Treść i embed w jednym miejscu.' : 'Do 10 kanałów w jednej grupie.'}</DialogDescription></DialogHeader>
    {form && <form onSubmit={e => { e.preventDefault(); if (valid) onSave(); }}><label className="form-field">Nazwa<Input maxLength={80} required value={form.name} data-testid={`${kind}-name-input`} onChange={e => update('name', e.target.value)} /></label>
      {isTemplate ? <><label className="form-field">Treść<Textarea value={form.content} maxLength={2000} data-testid="template-content-input" onChange={e => update('content', e.target.value)} /></label><EmbedEditor value={form.embed} onChange={value => update('embed', value)} prefix="template-embed" />{Object.keys(form.overrides || {}).length > 0 && <div className="saved-variants"><p>Osobne treści kanałów</p>{Object.entries(form.overrides).map(([id, text]) => <label key={id}>{id}<Textarea maxLength={2000} value={text} data-testid={`template-variant-${id}`} onChange={e => update('overrides', { ...form.overrides, [id]: e.target.value })} /><Button type="button" variant="ghost" size="sm" data-testid={`template-variant-remove-${id}`} onClick={() => { const next = { ...form.overrides }; delete next[id]; update('overrides', next); }}>Usuń wariant</Button></label>)}</div>}</> : <><div className="form-field"><label htmlFor="group-channel-input">ID kanału</label><div className="channel-input-row"><Input id="group-channel-input" inputMode="numeric" value={channelId} maxLength={20} disabled={form.channels.length >= 10} data-testid="group-channel-input" onChange={e => { setChannelId(e.target.value); setChannelError(''); }} /><Button type="button" variant="outline" disabled={!channelId || form.channels.length >= 10} data-testid="group-channel-add" onClick={addChannel}><Plus size={15} />Dodaj</Button></div>{channelError && <p role="alert" className="inline-error" data-testid="group-channel-error">{channelError}</p>}</div><div className="group-editor-list">{form.channels.map(c => <div key={c.id}><span>#{c.id}</span><button type="button" aria-label={`Usuń ${c.id}`} data-testid={`group-remove-${c.id}`} onClick={() => update('channels', form.channels.filter(x => x.id !== c.id))}><X size={14} /></button></div>)}</div></>}
      {error && <p role="alert" className="inline-error" data-testid={`${kind}-save-error`}>{error}</p>}<div className="dialog-actions"><Button type="button" variant="outline" disabled={busy} data-testid={`${kind}-editor-cancel`} onClick={() => setForm(null)}>Anuluj</Button><Button type="submit" disabled={!valid || busy} data-testid={`${kind}-save-button`}><Save size={15} />{busy ? 'Zapisywanie…' : 'Zapisz'}</Button></div>
    </form>}
  </DialogContent></Dialog>;
};