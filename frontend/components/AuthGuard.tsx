"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { hasAccessToken } from "@/lib/api";

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

    function handleAuthChange() {
      setIsAuthenticated(hasAccessToken());
    }

    window.addEventListener("melo-auth-change", handleAuthChange);
    window.addEventListener("storage", handleAuthChange);

    return () => {
      window.clearTimeout(timeoutId);
      window.removeEventListener("melo-auth-change", handleAuthChange);
      window.removeEventListener("storage", handleAuthChange);
    };
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

  return children;
}