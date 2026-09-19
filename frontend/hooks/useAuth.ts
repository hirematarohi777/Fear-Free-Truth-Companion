"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { UserProfile } from "@/types";

export function useAuth(options: { redirectToLogin?: boolean } = { redirectToLogin: true }) {
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .getMe()
      .then((u) => {
        if (!cancelled) setUser(u);
      })
      .catch(() => {
        if (!cancelled && options.redirectToLogin) router.push("/login");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [router, options.redirectToLogin]);

  const logout = useCallback(async () => {
    await api.logout();
    router.push("/login");
  }, [router]);

  return { user, loading, logout };
}
