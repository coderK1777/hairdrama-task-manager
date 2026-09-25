const API_URL = process.env.NEXT_PUBLIC_API_URL;

if (!API_URL) {
  throw new Error("Missing NEXT_PUBLIC_API_URL");
}

export type Profile = {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
};

export type Task = {
  id: string;
  title: string;
  description: string | null;
  status: "pending" | "completed";
  creator_id: string;
  assignee_id: string;
  created_at: string;
  completed_at: string | null;
  creator?: Profile | null;
  assignee?: Profile | null;
};

async function apiRequest<T>(
  path: string,
  accessToken: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...options.headers,
    },
  });

  const body = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(body.error || "Something went wrong");
  }

  return body as T;
}

export function syncProfile(accessToken: string) {
  return apiRequest<{ profile: Profile }>("/api/profile/sync", accessToken, {
    method: "POST",
  });
}

export function getProfiles(accessToken: string) {
  return apiRequest<{ profiles: Profile[] }>("/api/profiles", accessToken);
}

export function getTasks(accessToken: string) {
  return apiRequest<{ tasks: Task[] }>("/api/tasks", accessToken);
}

export function createTask(
  accessToken: string,
  payload: { title: string; description: string; assignee_id: string },
) {
  return apiRequest<{ task: Task; email_sent: boolean }>(
    "/api/tasks",
    accessToken,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
  );
}

export function completeTask(accessToken: string, taskId: string) {
  return apiRequest<{ task: Task; email_sent: boolean; already_completed?: boolean }>(
    `/api/tasks/${taskId}/complete`,
    accessToken,
    { method: "PATCH" },
  );
}
