import { useLang } from '../context/LangContext'

export default function LangToggle() {
  const { lang, toggle } = useLang()

  return (
    <button
      onClick={toggle}
      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded border border-slate-border
                 bg-white text-ink-400 text-xs font-medium hover:bg-slate transition-colors"
      title="Toggle language"
    >
      <span>{lang === 'en' ? '🇮🇳' : '🇬🇧'}</span>
      <span className="font-mono">{lang === 'en' ? 'हि' : 'EN'}</span>
    </button>
  )
}
