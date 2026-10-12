import { useState } from 'react';
import { ArrowUpRight, CalendarClock, CheckCheck, Hash, Send, ShieldCheck } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '../ui/button';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog';
import { useRelay } from '../../context/RelayContext';
import { CheckLine, Spinner } from './Primitives';
import { SaveScheduleDialog } from './SaveScheduleDialog';
import { EmbedPreview } from './EmbedPreview';

export const SendControls = () => {
  const { bot, selected, message, sending, dispatch, embed, overrides, draftReady, workspace } = useRelay();
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [confirm, setConfirm] = useState(false);
  const [error, setError] = useState('');
  const ready = !!bot && selected.length > 0 && draftReady;
  async function send() {
    setConfirm(false); setError('');
    try {
      const result = await dispatch();
      if (!result) return;
      const sent = result.results.filter(r => r.status === 'sent').length;
      if (sent === result.results.length) toast.success(`Wiadomość wysłana! Kanały: ${sent}.`);
      else toast.warning(`Wysłano: ${sent} z ${result.results.length}. Sprawdź raport.`);
    } catch (e) { setError(e.status ? e.message : 'Połączenie zostało przerwane. Sprawdź kanały Discord przed ponowną wysyłką.'); }
  }
  return <section className="send-section">
    <div className="send-section-heading"><CheckCheck size={19} /><h2>Gotowość do wysyłki</h2></div>
    <div className="readiness-list"><CheckLine done={!!bot} testId="readiness-bot">Bot połączony</CheckLine><CheckLine done={selected.length > 0} testId="readiness-channels">{selected.length ? `${selected.length} wybranych kanałów` : 'Wybrane kanały'}</CheckLine><CheckLine done={draftReady} testId="readiness-message">Wiadomość gotowa</CheckLine></div>
    <div className="send-summary"><span>Tryb wysyłki</span><strong>Jednorazowa<ArrowUpRight size={13} /></strong></div>
    <Button className="send-button" disabled={!ready || sending} data-testid="send-messages-submit-button" onClick={() => setConfirm(true)}>{sending ? <Spinner /> : <Send size={17} />}{sending ? 'Wysyłanie wiadomości…' : 'Wyślij wiadomość'}<span>{selected.length}</span></Button>
    <p className="send-note"><ShieldCheck size={13} />Bez pingowania @everyone i ról</p>
    <Button variant="outline" className="schedule-trigger-button" disabled={!ready || sending || !workspace} data-testid="schedule-create-button" onClick={() => setScheduleOpen(true)}><CalendarClock size={16} />Zaplanuj na później</Button>
    {error && <p role="alert" className="inline-error" data-testid="send-error">{error}</p>}
    <Dialog open={confirm} onOpenChange={setConfirm}><DialogContent className="relay-dialog" data-testid="send-confirmation-dialog"><DialogHeader><DialogTitle>Wszystko gotowe?</DialogTitle><DialogDescription>Wiadomość zostanie wysłana jako {bot?.username} na wybrane kanały. Tej operacji nie można cofnąć w panelu.</DialogDescription></DialogHeader><div className="confirmation-channels" data-testid="confirmation-channels">{selected.map(c => <span key={c.id}><Hash size={13} />{c.name}</span>)}</div><pre className="confirmation-message" data-testid="confirmation-message">{message}</pre>{selected.filter(c => overrides[c.id] !== undefined).map(c => <div className="confirmation-variant" key={c.id} data-testid={`confirmation-variant-${c.id}`}><strong>#{c.name}</strong><pre>{overrides[c.id]}</pre></div>)}<EmbedPreview embed={embed} prefix="confirmation" /><div className="dialog-actions"><Button variant="outline" data-testid="send-cancel-button" onClick={() => setConfirm(false)}>Jeszcze nie</Button><Button className="primary-button" disabled={sending} data-testid="send-confirm-button" onClick={send}><Send size={16} />Potwierdź wysyłkę</Button></div></DialogContent></Dialog>
    {scheduleOpen && <SaveScheduleDialog open={scheduleOpen} onOpenChange={setScheduleOpen} />}
  </section>;
};