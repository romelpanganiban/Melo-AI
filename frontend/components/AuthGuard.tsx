"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

import { hasAccessToken } from "@/lib/api";

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = pathname === "/" || pathname === "/login";
  const isAuthenticated = hasAccessToken();

  useEffect(() => {
    if (!isPublic && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, isPublic, router]);

  return isPublic || isAuthenticated ? children : null;
}