const base = process.env.REACT_APP_BACKEND_URL;
if (!base) throw new Error('Brak konfiguracji adresu API.');

export async function api(path, body) {
  const response = await fetch(`${base}/api${path}`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body), cache: 'no-store',
  });
  let data;
  try { data = await response.json(); }
  catch { throw new Error('Brak odpowiedzi serwera. Spróbuj ponownie później.'); }
  if (!response.ok) {
    const error = new Error(typeof data.detail === 'string' ? data.detail : 'Nie udało się wykonać operacji.');
    error.status = response.status;
    throw error;
  }
  return data;
}