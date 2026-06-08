import { createContext, useContext, useState } from 'react'
import en from '../i18n/en'
import hi from '../i18n/hi'

const LangContext = createContext(null)

const strings = { en, hi }

export function LangProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('fleet_lang') || 'en')

  function toggle() {
    const next = lang === 'en' ? 'hi' : 'en'
    localStorage.setItem('fleet_lang', next)
    setLang(next)
  }

  const t = strings[lang]

  return (
    <LangContext.Provider value={{ lang, toggle, t }}>
      {children}
    </LangContext.Provider>
  )
}

export function useLang() {
  return useContext(LangContext)
}
