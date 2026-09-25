"use client";

import { FormEvent, useState } from "react";
import type { Profile } from "@/lib/api";

export type NewTaskValues = {
  title: string;
  description: string;
  assignee_id: string;
};

type Props = {
  users: Profile[];
  currentUserId: string;
  busy: boolean;
  onSubmit: (values: NewTaskValues) => Promise<void>;
  onCancel: () => void;
};

export default function CreateTaskForm({ users, currentUserId, busy, onSubmit, onCancel }: Props) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [assigneeId, setAssigneeId] = useState(currentUserId);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim() || !assigneeId) return;

    await onSubmit({
      title: title.trim(),
      description: description.trim(),
      assignee_id: assigneeId,
    });
  }

  return (
    <form className="task-form" onSubmit={handleSubmit}>
      <div>
        <label htmlFor="title">Task title</label>
        <input
          id="title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="Example: Review landing page copy"
          maxLength={120}
          required
        />
      </div>

      <div>
        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Add a short note or expected outcome"
          rows={4}
          maxLength={1000}
        />
      </div>

      <div>
        <label htmlFor="assignee">Assign to</label>
        <select id="assignee" value={assigneeId} onChange={(event) => setAssigneeId(event.target.value)}>
          {users.map((user) => (
            <option value={user.id} key={user.id}>
              {user.full_name || user.email}{user.id === currentUserId ? " (You)" : ""}
            </option>
          ))}
        </select>
      </div>

      <div className="form-actions">
        <button type="button" className="secondary-button" onClick={onCancel} disabled={busy}>
          Cancel
        </button>
        <button type="submit" className="primary-button" disabled={busy || !title.trim()}>
          {busy ? "Creating..." : "Create task"}
        </button>
      </div>
    </form>
  );
}
