import { createContext, useContext, useRef, useState } from 'react';
import { api } from '../lib/relay-api';

const RelayContext = createContext(null);
export const useRelay = () => useContext(RelayContext);

export const RelayProvider = ({ children }) => {
  const [token, setToken] = useState('');
  const [bot, setBot] = useState(null);
  const [channels, setChannels] = useState([]);
  const [message, setMessage] = useState('');
  const [history, setHistory] = useState([]);
  const [sending, setSending] = useState(false);
  const [results, setResults] = useState(null);
  const [helpOpen, setHelpOpen] = useState(false);
  const dispatchLock = useRef(false);
  const selected = channels.filter(c => c.selected);

  function disconnect() {
    if (dispatchLock.current) return;
    setToken(''); setBot(null); setChannels([]); setResults(null);
  }

  async function dispatch() {
    if (dispatchLock.current || !bot || !selected.length || !message.trim()) return;
    dispatchLock.current = true; setSending(true); setResults(null);
    const snapshot = { content: message, channels: selected.map(c => ({ ...c })), bot: bot.username };
    const requestId = crypto.randomUUID();
    try {
      const result = await api('/messages/send', {
        token, channel_ids: selected.map(c => c.id), content: message, request_id: requestId,
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
    setHelpOpen, disconnect, dispatch }}>{children}</RelayContext.Provider>;
};