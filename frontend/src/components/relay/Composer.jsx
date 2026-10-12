import { useRef } from 'react';
import { Bold, Code2, Italic, MessageSquareText, Trash2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Textarea } from '../ui/textarea';
import { useRelay } from '../../context/RelayContext';
import { SectionTitle } from './Primitives';
import { EmojiPicker } from './EmojiPicker';

export const Composer = () => {
  const { message, setMessage, sending } = useRelay();
  const inputRef = useRef(null);
  const selection = useRef({ start: 0, end: 0 });
  function replaceSelection(prefix, suffix = '') {
    const { start, end } = selection.current;
    const next = message.slice(0, start) + prefix + message.slice(start, end) + suffix + message.slice(end);
    if (next.length > 2000) return;
    setMessage(next);
    const position = end + prefix.length;
    selection.current = { start: position, end: position };
    requestAnimationFrame(() => { inputRef.current?.focus(); inputRef.current?.setSelectionRange(position, position); });
  }
  return <section className="composer-panel tool-section">
    <SectionTitle number="03" title="Twoja wiadomość" right={<MessageSquareText size={17} className="muted" />} />
    <label className="sr-only" htmlFor="message-composer">Treść wiadomości</label>
    <div className="editor-shell"><Textarea ref={inputRef} id="message-composer" data-testid="message-composer-textarea" placeholder={'Hej, społeczności! 👋\nCo dzisiaj ogłaszamy?'} value={message} maxLength={2000} disabled={sending} onChange={e => setMessage(e.target.value)} onSelect={e => { selection.current = { start: e.target.selectionStart, end: e.target.selectionEnd }; }} />
      <div className="editor-toolbar"><div className="format-actions"><Button type="button" variant="ghost" size="icon" data-testid="format-bold-button" title="Pogrubienie" aria-label="Pogrubienie" disabled={sending || message.length > 1996} onClick={() => replaceSelection('**', '**')}><Bold size={17} /></Button><Button type="button" variant="ghost" size="icon" data-testid="format-italic-button" title="Kursywa" aria-label="Kursywa" disabled={sending || message.length > 1998} onClick={() => replaceSelection('*', '*')}><Italic size={17} /></Button><Button type="button" variant="ghost" size="icon" data-testid="format-code-button" title="Kod" aria-label="Kod" disabled={sending || message.length > 1998} onClick={() => replaceSelection('`', '`')}><Code2 size={18} /></Button><span className="toolbar-separator" /><EmojiPicker disabled={sending} onSelect={emoji => replaceSelection(emoji)} /></div><span data-testid="message-char-counter" className={`char-counter ${message.length >= 1900 ? 'near-limit' : ''}`}>{message.length}<span> / 2 000</span></span></div>
    </div><div className="editor-footnote"><span>Tekst, emoji i odrobina Twojego stylu.</span><Button variant="ghost" size="sm" disabled={!message || sending} data-testid="message-clear-button" onClick={() => { setMessage(''); selection.current = { start: 0, end: 0 }; }}><Trash2 size={13} />Wyczyść</Button></div>
  </section>;
};