import { AlertCircle, ArrowUpRight, CheckCircle2, CircleSlash, Hash } from 'lucide-react';

export const DispatchResults = ({ result, prefix = 'dispatch' }) => {
  if (!result) return null;
  const sent = result.results.filter(r => r.status === 'sent').length;
  return <section className="dispatch-results" data-testid={`${prefix}-results`} aria-live="polite"><div className="results-heading"><h2>Raport wysyłki</h2><span data-testid={`${prefix}-summary`}>{sent} / {result.results.length} wysłanych</span></div><div className="result-list">{result.results.map(r => <div className={`result-item ${r.status}`} key={r.channel_id} data-testid={`${prefix}-result-item-${r.channel_id}`}>
    {r.status === 'sent' ? <CheckCircle2 size={17} /> : r.status === 'skipped' ? <CircleSlash size={17} /> : <AlertCircle size={17} />}<div><strong><Hash size={12} />{r.channel_name || r.channel_id}</strong><p>{r.detail}</p></div>{r.message_url && <a href={r.message_url} target="_blank" rel="noreferrer" title="Otwórz w Discordzie" aria-label="Otwórz w Discordzie" data-testid={`${prefix}-message-link-${r.channel_id}`}><ArrowUpRight size={17} /></a>}
  </div>)}</div></section>;
};