import { createContext, useContext, useEffect, useState } from "react";

const Theme = {
  DARK: "dark",
  LIGHT: "light",
  SYSTEM: "system",
}

const initialState = {
  theme: Theme.SYSTEM,
  setTheme: () => null,
}

const ThemeProviderContext = createContext(initialState);


export function ThemeProvider({
  children,
  defaultTheme = Theme.SYSTEM,
  storageKey = "vite-ui-theme",
  ...props
}) {
  const [theme, setThemeState] = useState(() => {
    return localStorage.getItem(storageKey) || defaultTheme;
  });

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove("light", "dark");

    if (theme === Theme.SYSTEM) {
      const systemPreferDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      root.classList.add(systemPreferDark ? Theme.DARK : Theme.LIGHT);
    } else {
      root.classList.add(theme);
    }
  }, [theme])

  const setTheme = (newTheme) => {
    localStorage.setItem(storageKey, newTheme);
    setThemeState(newTheme);
  };

  const value = {
    theme,
    setTheme,
  };

  return (
    <ThemeProviderContext.Provider value={value} {...props}>
      {children}
    </ThemeProviderContext.Provider>
  )
}

export const useTheme = () => {
  const context = useContext(ThemeProviderContext);

  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }

  return context;
}