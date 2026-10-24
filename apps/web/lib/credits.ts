/** Below this, insights (the costliest live action) may fail. */
export const LOW_CREDITS_THRESHOLD = 10

export const LOW_CREDITS_DISMISS_KEY = "drop.lowCreditsDismissedBalance"

export function formatCredits(balance: number) {
  return `${balance} ${balance === 1 ? "crédito" : "créditos"}`
}

export function isLowBalance(balance: number) {
  return balance < LOW_CREDITS_THRESHOLD
}

export function isCreditsNotice(message: string) {
  return /cr[eé]ditos?/i.test(message)
}

export function lowCreditsMessage(balance: number) {
  if (balance <= 0) {
    return "Seu saldo acabou. Ações que usam créditos não vão funcionar até a renovação."
  }
  return `Seu saldo está baixo (${formatCredits(balance)}). Algumas ações podem não funcionar.`
}
