import { ArrowUpRight, Bot, Hash, KeyRound, ShieldCheck } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../ui/dialog';
import { useRelay } from '../../context/RelayContext';

export const HelpDialog = () => {
  const { helpOpen, setHelpOpen } = useRelay();
  return <Dialog open={helpOpen} onOpenChange={setHelpOpen}><DialogContent className="relay-dialog" data-testid="help-dialog">
    <DialogHeader><DialogTitle>Twój bot, gotowy do działania.</DialogTitle><DialogDescription>Oficjalny bot Discord. Bez tokenu prywatnego konta.</DialogDescription></DialogHeader>
    <ol className="help-steps">
      <li><KeyRound /><div><h3>Utwórz bota i pobierz token</h3><p>Discord Developer Portal → New Application → Bot → Reset Token. Skopiuj token i wklej w pole „Token bota”. Nie udostępniaj go innym.</p><a href="https://discord.com/developers/applications" target="_blank" rel="noreferrer" data-testid="discord-portal-link">Otwórz Developer Portal <ArrowUpRight size={14} /></a></div></li>
      <li><Bot /><div><h3>Dodaj bota na swój serwer</h3><p>W OAuth2 → URL Generator zaznacz „bot”, następnie uprawnienia „View Channels” i „Send Messages”. Otwórz wygenerowany link. Dla wątków dodaj „Send Messages in Threads”.</p></div></li>
      <li><Hash /><div><h3>Skopiuj ID kanału</h3><p>Discord → Ustawienia użytkownika → Zaawansowane → Tryb deweloperski. Kliknij prawym przyciskiem wybrany kanał → Kopiuj ID kanału.</p></div></li>
    </ol><div className="privacy-note"><ShieldCheck size={18} /><p>Token jest wysyłany szyfrowanym połączeniem do serwera i dalej do Discorda. Nie zapisujemy tokenów. Odświeżenie karty kończy sesję.</p></div>
  </DialogContent></Dialog>;
};