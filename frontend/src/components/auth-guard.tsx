"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";

const PUBLIC_PATHS = ["/", "/login", "/register"];

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { token, isAuthenticated, loadUser } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const verify = async () => {
      const isPublic = PUBLIC_PATHS.includes(pathname);

      if (!token) {
        if (!isPublic) {
          router.replace("/login");
        } else {
          setIsChecking(false);
        }
      } else {
        if (!isAuthenticated) {
          await loadUser();
        }
        
        // After loading check again
        const freshAuth = useAuth.getState().isAuthenticated;
        if (freshAuth && (pathname === "/login" || pathname === "/register")) {
          router.replace("/dashboard");
        } else if (!freshAuth && !isPublic) {
          router.replace("/login");
        } else {
          setIsChecking(false);
        }
      }
    };

    verify();
  }, [token, isAuthenticated, pathname, router, loadUser]);

  if (isChecking) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-950 text-slate-100">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
          <p className="text-sm font-medium text-slate-400">Verifying session...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
