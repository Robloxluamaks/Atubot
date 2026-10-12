import { useState } from 'react';
import { Search, Smile } from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from '../ui/popover';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { EMOJIS } from '../../lib/emojis';

export const EmojiPicker = ({ onSelect, disabled }) => {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('Wszystkie');
  const matches = EMOJIS.filter(([emoji, name, group]) => (category === 'Wszystkie' || group === category) && (name.includes(search.toLowerCase()) || emoji.includes(search)));
  return <Popover><PopoverTrigger asChild><Button variant="ghost" size="icon" data-testid="emoji-picker-trigger-button" title="Dodaj emoji" aria-label="Dodaj emoji" disabled={disabled}><Smile size={18} /></Button></PopoverTrigger><PopoverContent align="start" side="top" className="emoji-popover" data-testid="emoji-picker-popover">
    <div className="emoji-picker-heading"><strong>Trochę więcej emocji.</strong><Smile size={17} /></div>
    <div className="emoji-search"><Search size={15} /><Input data-testid="emoji-search-input" aria-label="Szukaj emoji" placeholder="Szukaj emoji…" value={search} onChange={e => setSearch(e.target.value)} /></div>
    <div className="emoji-categories">{['Wszystkie', 'Twarze', 'Gesty', 'Symbole'].map(c => <button key={c} type="button" className={category === c ? 'active' : ''} data-testid={`emoji-category-${c}`} onClick={() => setCategory(c)}>{c}</button>)}</div>
    <div className="emoji-grid">{matches.map(([emoji, name]) => <button key={emoji} type="button" data-testid={`emoji-item-${EMOJIS.findIndex(e => e[0] === emoji)}`} title={name} aria-label={name} onClick={() => onSelect(emoji)}>{emoji}</button>)}</div>
    {!matches.length && <p data-testid="emoji-no-results" className="muted">Nie znaleziono emoji.</p>}
  </PopoverContent></Popover>;
};