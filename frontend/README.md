# Melo-AI Frontend

Next.js App Router frontend for Melo-AI.

## Features

- Session-based chat UI
- Real-time streaming responses from backend/Ollama
- Live assistant typing effect during generation
- Settings page for model/provider/temperature
- Models page with local model guidance

## Getting Started

Run the frontend development server:

```bash
npm run dev
```

Open http://localhost:3000.

## Required Backend

The frontend expects the backend API at:

- Default: http://127.0.0.1:8000
- Override with environment variable: `NEXT_PUBLIC_API_URL`

Streaming chat uses:

- `POST /chat/stream` (NDJSON events)

## Main Routes

- `/` Home
- `/chat` Chat UI
- `/models` Model recommendations and setup tips
- `/settings` Runtime model settings

## Build and Lint

```bash
npm run lint
npm run build
```

## Notes

- If offline or behind a restricted network, local system font fallbacks are used.
- If tests are needed, ensure Jest is installed in this environment.

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
