import { useState } from 'react';
import { Cookie, KeyRound, LockKeyhole, ShieldCheck, Trash2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { ConfirmDelete } from '../components/relay/ConfirmDelete';
import { useRelay } from '../context/RelayContext';
import { api } from '../lib/relay-api';

export default function PrivacyPage() {
  const { workspace, workspaceError, sending } = useRelay();
  const [confirm, setConfirm] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState('');
  async function erase() { setBusy(true); try { await api('/workspace', undefined, 'DELETE'); window.location.assign('/'); } catch (e) { setError(e.message); setBusy(false); setConfirm(false); } }
  return <div className="privacy-page page-enter"><div className="page-heading"><div><div className="eyebrow"><span />PRYWATNOŚĆ BEZ UKRYWANIA AUTOMATYZACJI</div><h1>Twoje dane<span>.</span></h1><p>Kontrola nad tym, co zostaje w Relay.</p></div><ShieldCheck size={32} className="mint-text" /></div>
    <div className="privacy-settings"><section><KeyRound size={22} /><div><h2>Token tylko tam, gdzie potrzebny</h2><p>Token bieżącego połączenia pozostaje w pamięci karty. Harmonogram zapisuje oddzielną, szyfrowaną kopię wyłącznie za Twoją zgodą. Kopia znika po zakończeniu lub usunięciu zadania.</p></div></section><section><Cookie size={22} /><div><h2>Prywatna przestrzeń przeglądarki</h2><p>Dostęp chroni cookie HttpOnly i Secure. Szablony, grupy i harmonogramy są przypisane do tej przeglądarki. Usunięcie cookie oznacza utratę dostępu — najpierw usuń aktywne zadania.</p><span data-testid="workspace-expiry">Ważność: {workspace ? new Date(workspace.expires_at).toLocaleString('pl-PL') : '—'}</span></div></section><section><LockKeyhole size={22} /><div><h2>Bez analityki i tokenów w historii</h2><p>Nie zapisujemy tokenów w localStorage, historii wysyłek ani logach aplikacji. Dane przestrzeni i harmonogramy wygasają najpóźniej po 30 dniach. Oficjalne API pozostaje widoczne dla Discorda.</p></div></section></div>
    <div className="danger-zone"><div><h2>Usuń prywatną przestrzeń</h2><p>Usunięcie wszystkich szablonów, grup, harmonogramów i zapisanych tokenów. Operacja nieodwracalna.</p></div><Button variant="destructive" disabled={!workspace || sending || busy} data-testid="workspace-delete-button" onClick={() => setConfirm(true)}><Trash2 size={15} />Usuń wszystkie dane</Button></div>{(error || workspaceError) && <p className="inline-error" role="alert" data-testid="workspace-delete-error">{error || workspaceError}</p>}
    <ConfirmDelete open={confirm} onOpenChange={setConfirm} onConfirm={erase} busy={busy} title="Usunąć całą przestrzeń?" description="Aktywne harmonogramy zostaną zatrzymane. Wszystkie zapisane tokeny, szablony i grupy zostaną usunięte. Trwającej już wysyłki nie można cofnąć." prefix="workspace-delete" />
  </div>;
}