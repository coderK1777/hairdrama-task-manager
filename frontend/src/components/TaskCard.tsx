"use client";

import type { Task } from "@/lib/api";

type Props = {
  task: Task;
  currentUserId: string;
  completing: boolean;
  onComplete: (taskId: string) => Promise<void>;
};

function displayName(name: string | null | undefined, email: string | undefined) {
  return name || email || "Unknown user";
}

export default function TaskCard({ task, currentUserId, completing, onComplete }: Props) {
  const isCompleted = task.status === "completed";
  const isAssignedToMe = task.assignee_id === currentUserId;
  const date = new Intl.DateTimeFormat("en", { day: "2-digit", month: "short", year: "numeric" })
    .format(new Date(task.created_at));

  return (
    <article className={`task-card ${isCompleted ? "task-card-complete" : ""}`}>
      <div className="task-card-topline">
        <span className={`status-pill ${isCompleted ? "status-complete" : "status-pending"}`}>
          {isCompleted ? "Completed" : "Pending"}
        </span>
        <span className="task-date">{date}</span>
      </div>

      <h3>{task.title}</h3>
      {task.description && <p className="task-description">{task.description}</p>}

      <div className="task-meta">
        <span>
          <strong>Assigned to:</strong> {displayName(task.assignee?.full_name, task.assignee?.email)}
        </span>
        <span>
          <strong>Created by:</strong> {displayName(task.creator?.full_name, task.creator?.email)}
        </span>
      </div>

      {!isCompleted && isAssignedToMe && (
        <button className="complete-button" onClick={() => onComplete(task.id)} disabled={completing}>
          {completing ? "Updating..." : "Mark complete"}
        </button>
      )}
    </article>
  );
}
