"use client";

import { useEffect } from "react";
import { useChatStore } from "@/store/useChatStore";

const LOCALE_TO_LANG: Record<string, string> = {
  en: "en",
  lg: "lg",
  sw: "sw",
  nyn: "nyn",
};

/**
 * Client component that syncs the <html lang> attribute
 * with the active locale from the chat store.
 */
export function LocaleHtmlLang() {
  const locale = useChatStore((s) => s.locale);

  useEffect(() => {
    const lang = LOCALE_TO_LANG[locale] || "en";
    document.documentElement.lang = lang;
  }, [locale]);

  return null;
}
