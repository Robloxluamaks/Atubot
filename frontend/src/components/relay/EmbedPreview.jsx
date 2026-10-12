import { hexColor } from '../../lib/drafts';
export const EmbedPreview = ({ embed, prefix = 'preview' }) => !embed ? null : <div data-testid={`${prefix}-embed`} className="embed-preview" style={{ borderLeftColor: hexColor(embed.color) }}>
  {embed.title && (embed.url && /^https?:\/\//.test(embed.url) ? <a data-testid={`${prefix}-embed-link`} target="_blank" rel="noreferrer" href={embed.url}>{embed.title}</a> : <strong>{embed.title}</strong>)}
  {embed.description && <p>{embed.description}</p>}{embed.footer && <small>{embed.footer}</small>}
</div>;