import { Check, Loader2, Radio, Send } from 'lucide-react';

export const Brand = () => <div className="brand"><span className="brand-symbol"><Send size={23} strokeWidth={2.4} /></span><span>relay<span className="brand-period">.</span></span></div>;
export const Spinner = () => <Loader2 size={16} className="spin" aria-hidden="true" />;
export const BotAvatar = ({ bot, className = '' }) => <div className={`bot-avatar ${className}`}>
  {bot?.avatar_url ? <img src={bot.avatar_url} alt={bot.username} /> : <Radio size={23} />}
</div>;
export const SectionTitle = ({ number, title, right }) => <div className="section-heading"><h2><span className="step-number">{number}</span>{title}</h2>{right}</div>;
export const StatusBadge = ({ bot, testId = 'connection-status' }) => <span data-testid={testId} className={`status-badge ${bot ? 'connected' : ''}`}><i />{bot ? 'Połączono' : 'Niepołączony'}</span>;
export const CheckLine = ({ done, children, testId }) => <div data-testid={testId} className={`check-line ${done ? 'done' : ''}`}><span>{done ? <Check size={12} /> : <i />}</span>{children}</div>;