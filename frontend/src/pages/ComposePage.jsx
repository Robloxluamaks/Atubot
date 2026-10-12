import { ArrowUpRight, Radio, Sparkles } from 'lucide-react';
import { Button } from '../components/ui/button';
import { ConnectionPanel } from '../components/relay/ConnectionPanel';
import { ChannelPanel } from '../components/relay/ChannelPanel';
import { Composer } from '../components/relay/Composer';
import { MessagePreview } from '../components/relay/MessagePreview';
import { SendControls } from '../components/relay/SendControls';
import { DispatchResults } from '../components/relay/DispatchResults';
import { QuickLibrary } from '../components/relay/QuickLibrary';
import { useRelay } from '../context/RelayContext';

export default function ComposePage() {
  const { results, setHelpOpen } = useRelay();
  return <div className="compose-page page-enter"><div className="page-heading"><div><div className="eyebrow"><span />TWOJA SPOŁECZNOŚĆ, TWÓJ GŁOS</div><h1>Nowa wiadomość<span>.</span></h1><p>Dobre rzeczy zasługują na to, by o nich usłyszeć.</p></div><Button variant="outline" className="guide-button" data-testid="setup-guide-button" onClick={() => setHelpOpen(true)}><Radio size={16} />Konfiguracja Discord<ArrowUpRight size={15} /></Button></div>
    <QuickLibrary /><div className="compose-grid"><div className="compose-main"><ConnectionPanel /><ChannelPanel /><Composer /></div><aside className="compose-aside"><MessagePreview /><SendControls /><DispatchResults result={results} /><div className="aside-signoff"><Sparkles size={18} /><span>Mniej klikania.<br /><strong>Więcej społeczności.</strong></span></div></aside></div>
  </div>;
}