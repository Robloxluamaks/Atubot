import { createContext, useContext, useEffect, useRef, useState } from 'react';
import { api } from '../lib/relay-api';
import { validEmbed } from '../lib/drafts';

const RelayContext = createContext(null);
export const useRelay = () => useContext(RelayContext);

export const RelayProvider = ({ children }) => {
  const [token, setToken] = useState('');
  const [bot, setBot] = useState(null);
  const [channels, setChannels] = useState([]);
  const [message, setMessage] = useState('');
  const [embed, setEmbed] = useState(null);
  const [overrides, setOverrides] = useState({});
  const [workspace, setWorkspace] = useState(null);
  const [workspaceError, setWorkspaceError] = useState('');
  const sessionPromise = useRef(null);
  const [history, setHistory] = useState([]);
  const [sending, setSending] = useState(false);
  const [results, setResults] = useState(null);
  const [helpOpen, setHelpOpen] = useState(false);
  const dispatchLock = useRef(false);
  const selected = channels.filter(c => c.selected);
  const draftReady = validEmbed(embed) && selected.every(c => ((overrides[c.id] ?? message).trim() || embed) && (overrides[c.id] ?? message).length <= 2000) && (selected.length > 0 || !!message.trim() || !!embed);
  const draft = { content: message, embed, overrides: Object.fromEntries(selected.filter(c => overrides[c.id] !== undefined).map(c => [c.id, overrides[c.id]])) };

  useEffect(() => {
    if (!sessionPromise.current) sessionPromise.current = api('/workspace/session', {});
    sessionPromise.current.then(setWorkspace).catch(e => setWorkspaceError(e.message));
  }, []);

  function loadDraft(value) { setMessage(value.content || ''); setEmbed(value.embed || null); setOverrides(value.overrides || {}); }

  function disconnect() {
    if (dispatchLock.current) return;
    setToken(''); setBot(null); setChannels([]); setResults(null);
  }

  async function dispatch() {
    if (dispatchLock.current || !bot || !selected.length || !draftReady) return;
    dispatchLock.current = true; setSending(true); setResults(null);
    const snapshot = { ...draft, channels: selected.map(c => ({ ...c })), bot: bot.username };
    const requestId = crypto.randomUUID();
    try {
      const result = await api('/messages/send', {
        token, channel_ids: selected.map(c => c.id), ...draft, request_id: requestId,
      });
      setResults(result);
      setHistory(prev => [{ ...snapshot, ...result }, ...prev].slice(0, 50));
      return result;
    } catch (error) {
      if (error.status === 401) { setBot(null); setToken(''); setChannels([]); }
      throw error;
    } finally { dispatchLock.current = false; setSending(false); }
  }

  return <RelayContext.Provider value={{ token, setToken, bot, setBot, channels, setChannels,
    message, setMessage, history, setHistory, sending, selected, results, helpOpen,
    setHelpOpen, disconnect, dispatch, embed, setEmbed, overrides, setOverrides,
    workspace, workspaceError, loadDraft, draftReady, draft }}>{children}</RelayContext.Provider>;
};