"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) {
        router.replace("/dashboard");
      }
    });
  }, [router]);

  async function handleGoogleLogin() {
    setLoading(true);
    setError("");

    const { error: authError } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="brand-mark">TF</div>
        <p className="eyebrow">HAIRDRAMA TECH ASSIGNMENT</p>
        <h1>TaskFlow</h1>
        <p className="auth-copy">
          A simple workspace to assign tasks, track progress, and keep everyone updated.
        </p>

        <button className="google-button" onClick={handleGoogleLogin} disabled={loading}>
          <span className="google-icon">G</span>
          {loading ? "Connecting..." : "Continue with Google"}
        </button>

        {error && <p className="error-text">{error}</p>}
        <p className="auth-footnote">Your Google account is used only for secure sign-in.</p>
      </section>
    </main>
  );
}
