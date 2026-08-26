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

  return isPublic || (isHydrated && isAuthenticated) ? children : null;
}