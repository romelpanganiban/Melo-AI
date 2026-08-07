const API_URL = "http://127.0.0.1:8000";

export async function getSessions() {
  const response = await fetch(
    `${API_URL}/sessions`
  );

  return response.json();
}

export async function createSession() {
  const response = await fetch(
    `${API_URL}/sessions`,
    {
      method: "POST",
    }
  );

  return response.json();
}

export async function getHistory(
  sessionId: string
) {
  const response = await fetch(
    `${API_URL}/history/${sessionId}`
  );

  return response.json();
}

export async function sendMessage(
  sessionId: string,
  message: string
) {
  const response = await fetch(
    `${API_URL}/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        message,
      }),
    }
  );

  return response.json();
}