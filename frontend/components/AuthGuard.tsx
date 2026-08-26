"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { hasAccessToken, logout } from "@/lib/api";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = pathname === "/" || pathname === "/login";
  const [isHydrated, setIsHydrated] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setIsAuthenticated(hasAccessToken());
      setIsHydrated(true);
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, []);

  useEffect(() => {
    if (!isHydrated) {
      return;
    }
    if (!isPublic && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, isHydrated, isPublic, router]);

  if (isPublic) {
    return children;
  }

  if (!isHydrated || !isAuthenticated) {
    return null;
  }

  async function handleLogout() {
    await logout().catch(() => undefined);
    router.replace("/login");
  }

  return (
    <>
      <button
        type="button"
        onClick={() => void handleLogout()}
        className="fixed right-4 top-4 z-50 rounded-lg border border-white/20 bg-black/30 px-3 py-2 text-xs font-semibold text-white backdrop-blur transition hover:bg-black/50"
      >
        Sign out
      </button>
      {children}
    </>
  );
}