import { LayoutTemplate } from 'lucide-react';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import { Switch } from '../ui/switch';
import { EMPTY_EMBED, hexColor, validEmbed } from '../../lib/drafts';

export const EmbedEditor = ({ value, onChange, disabled = false, prefix = 'embed' }) => {
  const update = (key, next) => onChange({ ...value, [key]: next });
  return <div className="embed-editor"><div className="feature-heading"><span><LayoutTemplate size={16} />Wiadomość embed</span><Switch checked={!!value} disabled={disabled} data-testid={`${prefix}-toggle`} aria-label="Włącz embed" onCheckedChange={checked => onChange(checked ? { ...EMPTY_EMBED } : null)} /></div>
    {value && <div className="embed-fields"><div className="form-grid"><label>Tytuł<Input value={value.title} maxLength={256} disabled={disabled} data-testid={`${prefix}-title`} onChange={e => update('title', e.target.value)} placeholder="Co nowego na serwerze?" /></label><label className="color-field">Kolor<input type="color" value={hexColor(value.color)} disabled={disabled} data-testid={`${prefix}-color`} onChange={e => update('color', parseInt(e.target.value.slice(1), 16))} /></label></div><label>Opis<Textarea value={value.description} maxLength={4096} disabled={disabled} data-testid={`${prefix}-description`} onChange={e => update('description', e.target.value)} placeholder="Szczegóły ogłoszenia…" /></label><label>Link do tytułu<Input type="url" value={value.url} maxLength={1000} disabled={disabled} data-testid={`${prefix}-url`} onChange={e => update('url', e.target.value)} placeholder="https://…" /></label><label>Stopka<Input value={value.footer} maxLength={2048} disabled={disabled} data-testid={`${prefix}-footer`} onChange={e => update('footer', e.target.value)} placeholder="Opcjonalna stopka" /></label>{!validEmbed(value) && <p className="inline-error" data-testid={`${prefix}-error`}>Podaj tytuł lub opis i poprawny link HTTP(S). Łączny limit: 6000 znaków.</p>}</div>}
  </div>;
};