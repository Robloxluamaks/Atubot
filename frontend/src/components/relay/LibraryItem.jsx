import { ArrowUpRight, Files, FolderOpen, Pencil, Trash2 } from 'lucide-react';
import { Button } from '../ui/button';
import { EmbedPreview } from './EmbedPreview';

export const LibraryItem = ({ item, kind, disabled, onApply, onEdit, onDelete }) => {
  const template = kind === 'templates', Icon = template ? Files : FolderOpen;
  return <article className="library-item" data-testid={`${kind}-item-${item.id}`}>
    <div className="library-item-heading"><Icon size={19} /><h2>{item.name}</h2><Button variant="ghost" size="icon" aria-label="Edytuj" title="Edytuj" data-testid={`${kind}-edit-${item.id}`} disabled={disabled} onClick={onEdit}><Pencil size={15} /></Button><Button variant="ghost" size="icon" aria-label="Usuń" title="Usuń" data-testid={`${kind}-delete-${item.id}`} onClick={onDelete}><Trash2 size={15} /></Button></div>
    {template ? <><p className="library-excerpt">{item.content || 'Wiadomość embed'}</p><EmbedPreview embed={item.embed} prefix={`library-${item.id}`} />{Object.keys(item.overrides || {}).length > 0 && <small>{Object.keys(item.overrides).length} osobnych wariantów</small>}</> : <div className="group-chips">{item.channels.map(c => <span key={c.id} title={c.id}># {c.name}</span>)}</div>}
    <div className="library-item-footer"><small>{template ? 'Szablon wiadomości' : `${item.channels.length} kanałów`}</small><Button size="sm" variant="outline" disabled={disabled} data-testid={`${kind}-use-${item.id}`} onClick={onApply}>Użyj<ArrowUpRight size={14} /></Button></div>
  </article>;
};