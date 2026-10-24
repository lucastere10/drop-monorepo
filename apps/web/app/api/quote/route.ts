import { NextResponse } from "next/server"

export async function GET() {
  try {
    const res = await fetch("https://www.stoic-quotes.com/api/quote", {
      next: { revalidate: 300 },
    })
    if (!res.ok) {
      return NextResponse.json(
        { code: "upstream", message: "Quote unavailable." },
        { status: 502 }
      )
    }
    const data = (await res.json()) as { text?: string; author?: string }
    return NextResponse.json({
      text: data.text || "",
      author: data.author || "",
    })
  } catch {
    return NextResponse.json(
      { code: "upstream", message: "Quote unavailable." },
      { status: 502 }
    )
  }
}
