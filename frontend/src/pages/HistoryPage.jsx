import { ArrowLeft, Clock3, RotateCcw, Send, Trash2 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { DispatchResults } from '../components/relay/DispatchResults';
import { useRelay } from '../context/RelayContext';

export default function HistoryPage() {
  const { history, setHistory, setMessage, sending } = useRelay();
  const navigate = useNavigate();
  return <div className="history-page page-enter"><div className="page-heading"><div><div className="eyebrow"><span />BIEŻĄCA SESJA</div><h1>Historia wysyłek<span>.</span></h1><p>Twoje wiadomości i ich droga do społeczności.</p></div>{history.length > 0 && <Button variant="outline" disabled={sending} data-testid="history-clear-button" onClick={() => setHistory([])}><Trash2 size={15} />Wyczyść historię</Button>}</div>
    <div className="history-session-note" data-testid="history-session-notice"><Clock3 size={16} />Historia tej karty · ostatnie 50 wysyłek · znika po odświeżeniu</div>
    {!history.length ? <div className="empty-history" data-testid="history-empty-state"><div className="empty-history-icon"><Send size={35} /></div><h2>Jeszcze cisza na łączach.</h2><p>Twoja pierwsza wysyłka pojawi się właśnie tutaj.</p><Button asChild className="primary-button"><Link to="/" data-testid="history-compose-link"><ArrowLeft size={16} />Utwórz wiadomość</Link></Button></div> : <div className="history-list">{history.map(item => <article key={item.request_id} className="history-item" data-testid={`history-item-${item.request_id}`}><div className="history-item-header"><div><span className="history-sender">{item.bot}</span><time>{new Date(item.sent_at).toLocaleString('pl-PL')}</time></div><Button variant="ghost" size="sm" disabled={sending} data-testid={`history-reuse-${item.request_id}`} onClick={() => { setMessage(item.content); navigate('/'); }}><RotateCcw size={14} />Użyj ponownie</Button></div><p className="history-content" data-testid={`history-content-${item.request_id}`}>{item.content}</p><DispatchResults result={item} prefix={`history-${item.request_id}`} /></article>)}</div>}
  </div>;
}