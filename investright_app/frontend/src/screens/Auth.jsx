import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";

export default function Auth({ onAuthenticated }) {
  const googleButtonRef = useRef(null);
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [age, setAge] = useState("");
  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!googleClientId || !googleButtonRef.current) return undefined;
    const renderGoogleButton = () => {
      if (!window.google?.accounts?.id || !googleButtonRef.current) return;
      window.google.accounts.id.initialize({
        client_id: googleClientId,
        callback: async ({ credential }) => {
          setError("");
          setLoading(true);
          try {
            const result = await api.loginWithGoogle(credential);
            api.setToken(result.access_token);
            await onAuthenticated();
          } catch (e) {
            setError(e.message || "Google login failed. Please try again.");
          } finally {
            setLoading(false);
          }
        },
      });
      googleButtonRef.current.replaceChildren();
      window.google.accounts.id.renderButton(googleButtonRef.current, {
        theme: "outline", size: "large", width: 348, text: "continue_with",
      });
    };
    if (window.google?.accounts?.id) { renderGoogleButton(); return undefined; }
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true; script.defer = true;
    script.onload = renderGoogleButton;
    document.head.appendChild(script);
    return () => script.remove();
  }, [googleClientId, onAuthenticated]);

  const submit = async () => {
    setError("");
    if (!email.trim() || !password) { setError("Please enter your email and password."); return; }
    if (mode === "signup" && !fullName.trim()) { setError("What's your name? We'd love to know 😊"); return; }
    setLoading(true);
    try {
      const result =
        mode === "login"
          ? await api.login(email.trim(), password)
          : await api.signup(fullName.trim(), email.trim(), password, age ? Number(age) : null);
      api.setToken(result.access_token);
      await onAuthenticated();
    } catch (e) {
      setError(e.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth">
      {/* Hero */}
      <div className="auth-hero">
        <div className="auth-hero-icon">F</div>
        <div className="auth-hero-title">
          {mode === "login" ? "Welcome back! 👋" : "Start your journey 🚀"}
        </div>
        <div className="auth-hero-sub">
          {mode === "login"
            ? "Log in to continue with your AI financial advisor"
            : "Create a free account to get your personalised investment plan"}
        </div>
      </div>

      {/* Mode switcher */}
      <div className="auth-tabs">
        <button className={`auth-tab${mode === "login" ? " active" : ""}`} onClick={() => { setMode("login"); setError(""); }}>
          Log in
        </button>
        <button className={`auth-tab${mode === "signup" ? " active" : ""}`} onClick={() => { setMode("signup"); setError(""); }}>
          Sign up
        </button>
      </div>

      {error && <div className="auth-error">⚠️ {error}</div>}

      {/* Google */}
      {googleClientId ? (
        <div className="google-button" ref={googleButtonRef} />
      ) : (
        <button className="google-fallback" onClick={() => setError("Google login is not configured. Add VITE_GOOGLE_CLIENT_ID to frontend/.env.")} disabled={loading}>
          <strong>G</strong> Continue with Google
        </button>
      )}

      <div className="auth-divider"><span>or continue with email</span></div>

      {/* Fields */}
      {mode === "signup" && (
        <div className="auth-field">
          <label>Your name</label>
          <input
            type="text"
            placeholder="Priya Sharma"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            autoComplete="name"
          />
        </div>
      )}

      <div className="auth-field">
        <label>{mode === "login" ? "Email or Username" : "Email"}</label>
        <input
          type={mode === "login" ? "text" : "email"}
          placeholder={mode === "login" ? "you@example.com or admin" : "you@example.com"}
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete={mode === "login" ? "username" : "email"}
        />
      </div>

      {mode === "signup" && (
        <div className="auth-field">
          <label>Age <span className="auth-optional">(optional — helps with personalisation)</span></label>
          <input
            type="number"
            inputMode="numeric"
            placeholder="e.g. 28"
            value={age}
            onChange={(e) => setAge(e.target.value)}
          />
        </div>
      )}

      <div className="auth-field">
        <label>Password</label>
        <div className="pass-wrap">
          <input
            type={showPass ? "text" : "password"}
            placeholder={mode === "signup" ? "At least 6 characters" : "••••••••"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && submit()}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
          />
          <button className="pass-toggle" type="button" onClick={() => setShowPass((s) => !s)}>
            {showPass ? "Hide" : "Show"}
          </button>
        </div>
      </div>

      <button className="btn btn-block auth-submit" onClick={submit} disabled={loading}>
        {loading ? "Please wait…" : mode === "login" ? "Log in →" : "Create my account →"}
      </button>

      <div className="auth-fine">
        By continuing you agree to our{" "}
        <span className="auth-link">Terms of Service</span> and{" "}
        <span className="auth-link">Privacy Policy</span>.
        <br />Your financial data is encrypted and never sold.
      </div>
    </div>
  );
}
