import { NextRequest, NextResponse } from 'next/server';

// Replaces the old standalone Node/Express proxy (FrontEnd/node-server). The
// browser POSTs here (same-origin), and we forward to the Flask compute server.
// FLASK_URL is set as a Vercel env var, e.g. https://pandera-flask.onrender.com
export const dynamic = 'force-dynamic';
// Render's free tier sleeps after 15 min idle and takes ~30-50s to wake. Allow
// up to 60s so the first cold request isn't killed by the default 10s limit.
export const maxDuration = 60;

const FLASK_URL = process.env.FLASK_URL;

export async function POST(req: NextRequest) {
  if (!FLASK_URL) {
    return NextResponse.json(
      { error: 'FLASK_URL is not configured on the server' },
      { status: 500 }
    );
  }

  try {
    const body = await req.json();
    const upstream = await fetch(`${FLASK_URL}/compute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    // Flask returns JSON for both success ({plotly_json}) and its structured
    // error contract ({error,type,field} with 404/500). Forward the status so
    // the client sees the real outcome.
    const data = await upstream.json().catch(() => null);
    if (data === null) {
      return NextResponse.json(
        { error: 'Compute server returned a non-JSON response' },
        { status: 502 }
      );
    }
    return NextResponse.json(data, { status: upstream.status });
  } catch (err) {
    console.error('Error proxying to Flask compute server:', err);
    return NextResponse.json(
      { error: 'Could not reach the compute server' },
      { status: 502 }
    );
  }
}
