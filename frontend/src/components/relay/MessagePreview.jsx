import { Check, Hash, Radio } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useRelay } from '../../context/RelayContext';
import { BotAvatar } from './Primitives';

export const MessagePreview = () => {
  const { message, bot, selected } = useRelay();
  return <section className="preview-section">
    <div className="preview-section-heading"><h2>Podgląd wiadomości</h2><span className="live-label"><i />NA ŻYWO</span></div>
    <div className="discord-preview" data-testid="discord-live-preview-card">
      <div className="discord-channel"><Hash size={19} /><span data-testid="preview-channel-name">{selected[0]?.name || 'twój-kanał'}</span><span className="discord-channel-label">Discord</span></div>
      <div className="preview-date"><span /><span>DZISIAJ</span><span /></div>
      <div className="discord-message"><BotAvatar bot={bot} /><div className="discord-message-main"><div className="discord-author"><strong data-testid="preview-bot-name">{bot?.username || 'Twój bot'}</strong><span className="bot-badge"><Check size={9} />BOT</span><time>{new Date().toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}</time></div>
        <div className={`markdown-content ${!message ? 'preview-placeholder' : ''}`} data-testid="preview-message-content">{message ? <ReactMarkdown remarkPlugins={[remarkGfm]} allowedElements={['p', 'strong', 'em', 'code', 'pre', 'blockquote', 'ul', 'ol', 'li', 'br', 'a', 'del', 'h1', 'h2', 'h3', 'hr']} unwrapDisallowed components={{ a: ({ node, ...props }) => <a {...props} data-testid={`preview-link-${node.position?.start.offset}`} target="_blank" rel="noreferrer" /> }}>{message}</ReactMarkdown> : <><p>Twoja następna wielka wiadomość<br />zaczyna się tutaj<span> ✨</span></p><div className="preview-skeleton"><i /><i /></div></>}</div>
      </div></div>
      <div className="preview-watermark"><Radio size={13} /><span>Podgląd · jeszcze nie wysłano</span></div>
    </div>
    <p className="preview-caption">Ten sam przekaz. Na każdym wybranym kanale.</p>
  </section>;
};