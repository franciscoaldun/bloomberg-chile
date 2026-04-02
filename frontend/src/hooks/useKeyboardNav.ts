"use client";

import { useEffect } from "react";

type TabId = "main" | "analytics" | "cobre_fx" | "renta_fija" | "macro";

interface UseKeyboardNavProps {
  activeTab: TabId;
  setActiveTab: (tab: TabId) => void;
  commandLineOpen: boolean;
  setCommandLineOpen: (open: boolean) => void;
}

const TAB_KEYS: Record<string, TabId> = {
  "1": "main",
  "2": "analytics",
  "3": "cobre_fx",
  "4": "renta_fija",
  "5": "macro",
};

export function useKeyboardNav({
  activeTab,
  setActiveTab,
  commandLineOpen,
  setCommandLineOpen,
}: UseKeyboardNavProps) {
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Ignorar si estamos en un input/textarea
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "INPUT" || tag === "TEXTAREA") {
        // Solo Escape cierra el command line desde un input
        if (e.key === "Escape") {
          setCommandLineOpen(false);
        }
        return;
      }

      // "/" abre command line
      if (e.key === "/") {
        e.preventDefault();
        setCommandLineOpen(true);
        return;
      }

      // Escape cierra command line
      if (e.key === "Escape") {
        if (commandLineOpen) {
          setCommandLineOpen(false);
        }
        return;
      }

      // Tabs 1-4
      if (TAB_KEYS[e.key]) {
        e.preventDefault();
        setActiveTab(TAB_KEYS[e.key]);
        return;
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeTab, setActiveTab, commandLineOpen, setCommandLineOpen]);
}
