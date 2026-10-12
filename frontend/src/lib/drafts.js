export const EMPTY_EMBED = { title: '', description: '', color: 7636982, url: '', footer: '' };
export function validEmbed(embed) {
  if (!embed) return true;
  if (!embed.title.trim() && !embed.description.trim()) return false;
  if (embed.title.length > 256 || embed.description.length > 4096 || embed.footer.length > 2048) return false;
  if ((embed.title + embed.description + embed.footer).length > 6000) return false;
  if (embed.url) { try { const u = new URL(embed.url); if (!['http:', 'https:'].includes(u.protocol) || u.username) return false; } catch { return false; } }
  return true;
}
export const hexColor = color => `#${Number(color).toString(16).padStart(6, '0')}`;
export const scheduleState = { active: 'Aktywny', paused: 'Wstrzymany', running: 'Wysyłanie', completed: 'Zakończony', error: 'Wymaga uwagi' };