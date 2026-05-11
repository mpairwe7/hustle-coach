"use client";

import { useEffect, useState } from "react";

export function OfflineIndicator() {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    setIsOnline(navigator.onLine);

    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  if (isOnline) return null;

  return (
    <div
      className="flex items-center justify-center gap-2 px-4 py-2 text-center text-sm font-medium"
      style={{
        background: "var(--color-gold)",
        color: "white",
      }}
      role="alert"
    >
      <span className="inline-block h-2 w-2 rounded-full bg-white opacity-70" />
      You are offline — cached responses may be available
    </div>
  );
}
