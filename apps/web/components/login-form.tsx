"use client"

import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Suspense, useEffect, useId, useRef, useState, type RefObject } from "react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

type AuthMethod = "magic_link" | "google"

const SHELL =
  "mx-auto flex min-h-svh w-full max-w-md flex-col px-6 pt-[max(4rem,env(safe-area-inset-top))] pb-16 sm:pt-24 md:pt-28"

const ACTION = "h-auto min-h-11 w-full whitespace-normal px-3 py-2.5"
const PENDING_EMAIL_KEY = "drop_login_pending_email"

const FIELD =
  "w-full min-h-11 border bg-background px-3 text-base outline-none focus-visible:border-foreground focus-visible:ring-3 focus-visible:ring-ring/50"

function rememberNext(next: string) {
  if (typeof window === "undefined") return
  sessionStorage.setItem("drop_auth_next", next.startsWith("/") ? next : "/")
}

function readableMessage(message: unknown, fallback: string) {
  if (typeof message !== "string") return fallback
  const text = message.trim()
  if (!text || text === "Falha ao enviar link." || text === "Google OAuth não configurado.") {
    return fallback
  }
  return text
}

function LoginBrand() {
  return (
    <header className="animate-fade-up">
      <h1>
        <Link
          href="/"
          className="font-bebas inline-block text-6xl leading-none tracking-[0.04em] outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          DRO/P
        </Link>
      </h1>
      <p className="mt-3 text-sm text-muted-foreground">Revele o que importa.</p>
      <p className="mt-3 font-mono text-[10px] uppercase leading-relaxed tracking-widest text-muted-foreground">
        Sem senha. O link abre o chat e os insights.
      </p>
    </header>
  )
}

function FieldError({ id, children }: Readonly<{ id: string; children: string }>) {
  return (
    <p id={id} role="alert" className="text-sm text-destructive">
      {children}
    </p>
  )
}

type LoginSuccessProps = Readonly<{
  email: string
  error: string
  devVerifyUrl: string
  busy: boolean
  loading: boolean
  statusRef: RefObject<HTMLOutputElement | null>
  onResend: () => void
  onEdit: () => void
}>

function LoginSuccess({
  email,
  error,
  devVerifyUrl,
  busy,
  loading,
  statusRef,
  onResend,
  onEdit,
}: LoginSuccessProps) {
  return (
    <output ref={statusRef} tabIndex={-1} className="mt-8 flex flex-col gap-4 outline-none">
      <p className="text-sm">
        Enviamos um link de acesso para <span className="break-all">{email}</span>.
      </p>
      <p className="text-sm text-muted-foreground">
        Abra esse e-mail para entrar. Se não aparecer, olhe o spam.
      </p>
      {error ? <FieldError id="login-resend-error">{error}</FieldError> : null}
      {devVerifyUrl ? (
        <p className="text-sm text-muted-foreground">
          Ambiente local —{" "}
          <Link href={devVerifyUrl} className="underline underline-offset-4">
            abrir o link de acesso
          </Link>
        </p>
      ) : null}
      <Button type="button" className={ACTION} disabled={busy} onClick={onResend}>
        {loading ? "Enviando…" : "Reenviar link"}
      </Button>
      <Button type="button" variant="ghost" className={ACTION} disabled={busy} onClick={onEdit}>
        Corrigir e-mail
      </Button>
    </output>
  )
}

type LoginMethodsProps = Readonly<{
  email: string
  emailId: string
  emailRef: RefObject<HTMLInputElement | null>
  magicError: string
  magicErrorId: string
  googleError: string
  googleErrorId: string
  showMagic: boolean
  showGoogle: boolean
  noMethods: boolean
  busy: boolean
  loading: boolean
  googleLoading: boolean
  onEmail: (value: string) => void
  onMagic: () => void
  onGoogle: () => void
}>

function LoginMethods({
  email,
  emailId,
  emailRef,
  magicError,
  magicErrorId,
  googleError,
  googleErrorId,
  showMagic,
  showGoogle,
  noMethods,
  busy,
  loading,
  googleLoading,
  onEmail,
  onMagic,
  onGoogle,
}: LoginMethodsProps) {
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        onMagic()
      }}
      className="mt-8 flex flex-col gap-4"
    >
      {showMagic ? (
        <MagicFields
          email={email}
          emailId={emailId}
          emailRef={emailRef}
          magicError={magicError}
          magicErrorId={magicErrorId}
          busy={busy}
          loading={loading}
          onEmail={onEmail}
        />
      ) : null}
      {showMagic && showGoogle ? (
        <p className="text-center font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          ou
        </p>
      ) : null}
      {showGoogle ? (
        <GoogleFields
          googleError={googleError}
          googleErrorId={googleErrorId}
          busy={busy}
          googleLoading={googleLoading}
          onGoogle={onGoogle}
        />
      ) : null}
      {noMethods ? (
        <output className="text-sm text-muted-foreground">Nenhum meio de login configurado.</output>
      ) : null}
    </form>
  )
}

type MagicFieldsProps = Readonly<{
  email: string
  emailId: string
  emailRef: RefObject<HTMLInputElement | null>
  magicError: string
  magicErrorId: string
  busy: boolean
  loading: boolean
  onEmail: (value: string) => void
}>

function MagicFields({
  email,
  emailId,
  emailRef,
  magicError,
  magicErrorId,
  busy,
  loading,
  onEmail,
}: MagicFieldsProps) {
  return (
    <>
      <label htmlFor={emailId} className="flex flex-col gap-2 text-sm">
        <span>E-mail</span>
        <input
          ref={emailRef}
          id={emailId}
          name="email"
          type="email"
          inputMode="email"
          autoComplete="email"
          autoCapitalize="none"
          autoCorrect="off"
          spellCheck={false}
          required
          value={email}
          aria-invalid={magicError ? true : undefined}
          aria-describedby={magicError ? magicErrorId : undefined}
          onChange={(e) => onEmail(e.target.value)}
          className={cn(FIELD, magicError ? "border-destructive" : "border-border")}
        />
      </label>
      {magicError ? <FieldError id={magicErrorId}>{magicError}</FieldError> : null}
      <Button type="submit" className={ACTION} disabled={busy}>
        {loading ? "Enviando…" : "Enviar link de acesso"}
      </Button>
    </>
  )
}

type GoogleFieldsProps = Readonly<{
  googleError: string
  googleErrorId: string
  busy: boolean
  googleLoading: boolean
  onGoogle: () => void
}>

function GoogleFields({
  googleError,
  googleErrorId,
  busy,
  googleLoading,
  onGoogle,
}: GoogleFieldsProps) {
  return (
    <>
      <Button
        type="button"
        variant="outline"
        className={ACTION}
        disabled={busy}
        aria-describedby={googleError ? googleErrorId : undefined}
        onClick={onGoogle}
      >
        {googleLoading ? "Abrindo o Google…" : "Continuar com Google"}
      </Button>
      {googleError ? <FieldError id={googleErrorId}>{googleError}</FieldError> : null}
    </>
  )
}

function LoginFormInner() {
  const search = useSearchParams()
  const next = search.get("next") || "/dashboard"
  const emailId = useId()
  const magicErrorId = useId()
  const googleErrorId = useId()
  const emailRef = useRef<HTMLInputElement>(null)
  const statusRef = useRef<HTMLOutputElement>(null)
  const [email, setEmail] = useState("")
  const [sent, setSent] = useState(false)
  const [devVerifyUrl, setDevVerifyUrl] = useState("")
  const [magicError, setMagicError] = useState("")
  const [googleError, setGoogleError] = useState("")
  const [loading, setLoading] = useState(false)
  const [googleLoading, setGoogleLoading] = useState(false)
  const [methods, setMethods] = useState<AuthMethod[] | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch("/api/auth/methods")
      .then((res) => res.json())
      .then((data) => {
        if (cancelled) return
        const list = Array.isArray(data.methods) ? data.methods : ["magic_link"]
        setMethods(list.filter((item: string) => item === "magic_link" || item === "google"))
      })
      .catch(() => {
        if (!cancelled) setMethods(["magic_link"])
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const saved = sessionStorage.getItem(PENDING_EMAIL_KEY)
    if (!saved) return
    setEmail(saved)
    setSent(true)
  }, [])

  useEffect(() => {
    if (sent) statusRef.current?.focus()
  }, [sent])

  const methodsReady = methods !== null
  const showMagic = !methodsReady || methods.includes("magic_link")
  const showGoogle = methodsReady && methods.includes("google")
  const busy = loading || googleLoading

  async function sendLink() {
    setLoading(true)
    setMagicError("")
    rememberNext(next)
    try {
      const res = await fetch("/api/auth/magic-link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      })
      const data = res.status === 204 ? {} : await res.json().catch(() => ({}))
      if (!res.ok && res.status !== 204) {
        setMagicError(
          readableMessage(data.message, "Não foi possível enviar o link. Confira o e-mail e tente de novo."),
        )
        return
      }
      if (typeof data.dev_verify_url === "string") setDevVerifyUrl(data.dev_verify_url)
      sessionStorage.setItem(PENDING_EMAIL_KEY, email)
      setSent(true)
    } catch {
      setMagicError("Sem conexão. Verifique a rede e tente de novo.")
    } finally {
      setLoading(false)
    }
  }

  async function startGoogle() {
    setGoogleLoading(true)
    setGoogleError("")
    rememberNext(next)
    try {
      const res = await fetch("/api/auth/google/start")
      const data = await res.json().catch(() => ({}))
      if (data.state) sessionStorage.setItem("google_oauth_state", data.state)
      if (data.authorization_url) {
        window.location.href = data.authorization_url
        return
      }
      setGoogleError(
        readableMessage(
          data.message,
          "Não foi possível abrir o Google. Tente de novo ou envie um link de acesso.",
        ),
      )
      setGoogleLoading(false)
    } catch {
      setGoogleError("Sem conexão. Verifique a rede e tente de novo.")
      setGoogleLoading(false)
    }
  }

  function editEmail() {
    sessionStorage.removeItem(PENDING_EMAIL_KEY)
    setSent(false)
    setMagicError("")
    requestAnimationFrame(() => emailRef.current?.focus())
  }

  return (
    <div className={SHELL}>
      <LoginBrand />
      {sent ? (
        <LoginSuccess
          email={email}
          error={magicError}
          devVerifyUrl={devVerifyUrl}
          busy={busy}
          loading={loading}
          statusRef={statusRef}
          onResend={() => void sendLink()}
          onEdit={editEmail}
        />
      ) : (
        <LoginMethods
          email={email}
          emailId={emailId}
          emailRef={emailRef}
          magicError={magicError}
          magicErrorId={magicErrorId}
          googleError={googleError}
          googleErrorId={googleErrorId}
          showMagic={showMagic}
          showGoogle={showGoogle}
          noMethods={methodsReady && !showMagic && !showGoogle}
          busy={busy}
          loading={loading}
          googleLoading={googleLoading}
          onEmail={setEmail}
          onMagic={() => void sendLink()}
          onGoogle={() => void startGoogle()}
        />
      )}
    </div>
  )
}

function LoginFallback() {
  return (
    <div className={SHELL}>
      <LoginBrand />
    </div>
  )
}

export function LoginForm() {
  return (
    <Suspense fallback={<LoginFallback />}>
      <LoginFormInner />
    </Suspense>
  )
}
