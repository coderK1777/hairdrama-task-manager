"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { syncProfile } from "@/lib/api";

function CallbackContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [message, setMessage] = useState("Finishing sign in...");
  const started = useRef(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    async function finishLogin() {
      try {
        if (searchParams.get("error")) {
          throw new Error("Google sign-in was cancelled or could not be completed. Please try again.");
        }
        const code = searchParams.get("code");

        if (code) {
          const { error } = await supabase.auth.exchangeCodeForSession(code);
          if (error) throw error;
        }

        const { data, error } = await supabase.auth.getSession();
        if (error || !data.session) {
          throw new Error("Could not create a login session");
        }

        await syncProfile(data.session.access_token);
        router.replace("/dashboard");
      } catch (error) {
        setFailed(true);
        setMessage(error instanceof Error ? error.message : "Login failed");
      }
    }

    finishLogin();
  }, [router, searchParams]);

  return (
    <main className="auth-page">
      <section className="auth-card callback-card">
        {!failed && <div className="loader" />}
        <h2>{message}</h2>
        {failed && <a href="/login">Return to sign in</a>}
      </section>
    </main>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={<main className="auth-page"><div className="loader" /></main>}>
      <CallbackContent />
    </Suspense>
  );
}
