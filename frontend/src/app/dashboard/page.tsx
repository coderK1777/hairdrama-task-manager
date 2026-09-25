"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import {
  completeTask,
  createTask,
  getProfiles,
  getTasks,
  syncProfile,
  type Profile,
  type Task,
} from "@/lib/api";
import CreateTaskForm, { type NewTaskValues } from "@/components/CreateTaskForm";
import TaskCard from "@/components/TaskCard";

export default function DashboardPage() {
  const router = useRouter();
  const [accessToken, setAccessToken] = useState("");
  const [currentUser, setCurrentUser] = useState<Profile | null>(null);
  const [users, setUsers] = useState<Profile[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [creating, setCreating] = useState(false);
  const [completingId, setCompletingId] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const loadData = useCallback(async (token: string) => {
    const { profile } = await syncProfile(token);
    const [profileResult, taskResult] = await Promise.all([
      getProfiles(token),
      getTasks(token),
    ]);

    setCurrentUser(profile);
    setUsers(profileResult.profiles);
    setTasks(taskResult.tasks);
  }, []);

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setAccessToken(session?.access_token || "");
      if (!session) router.replace("/login");
    });
    async function initialize() {
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        router.replace("/login");
        return;
      }

      const token = data.session.access_token;
      setAccessToken(token);

      try {
        await loadData(token);
      } catch (error) {
        setError(error instanceof Error ? error.message : "Could not load dashboard");
      } finally {
        setLoading(false);
      }
    }

    initialize();
    return () => subscription.unsubscribe();
  }, [loadData, router]);

  const pendingCount = useMemo(
    () => tasks.filter((task) => task.status === "pending").length,
    [tasks],
  );
  const completedCount = tasks.length - pendingCount;

  async function handleCreate(values: NewTaskValues) {
    if (!accessToken) return;
    setCreating(true);
    setError("");
    setNotice("");

    try {
      const result = await createTask(accessToken, values);
      setTasks((current) => [result.task, ...current]);
      setShowCreate(false);
      setNotice(result.email_sent ? "Task created and email notification sent." : "Task created. Email notification could not be sent.");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not create task");
    } finally {
      setCreating(false);
    }
  }

  async function handleComplete(taskId: string) {
    if (!accessToken) return;
    setCompletingId(taskId);
    setError("");
    setNotice("");

    try {
      const result = await completeTask(accessToken, taskId);
      setTasks((current) => current.map((task) => (task.id === taskId ? result.task : task)));
      setNotice(result.already_completed ? "This task was already completed." : result.email_sent ? "Task completed and email notification sent." : "Task completed. Email notification could not be sent.");
    } catch (error) {
      setError(error instanceof Error ? error.message : "Could not complete task");
    } finally {
      setCompletingId("");
    }
  }

  async function handleLogout() {
    const { error: logoutError } = await supabase.auth.signOut();
    if (logoutError) {
      setError("Could not sign out. Please try again.");
      return;
    }
    router.replace("/login");
  }

  if (loading) {
    return <main className="loading-page"><div className="loader" /></main>;
  }

  return (
    <main className="dashboard-shell">
      <aside className="sidebar">
        <div>
          <div className="sidebar-brand">
            <div className="brand-mark small">TF</div>
            <span>TaskFlow</span>
          </div>
          <nav className="sidebar-nav">
            <button className="nav-item active">Dashboard</button>
          </nav>
        </div>
        <button className="logout-button" onClick={handleLogout}>Sign out</button>
      </aside>

      <section className="dashboard-content">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">TEAM TASKS</p>
            <h1>Good to see you, {currentUser?.full_name?.split(" ")[0] || "there"}.</h1>
            <p>Keep track of what is assigned and what is already done.</p>
          </div>
          <button className="primary-button" onClick={() => setShowCreate(true)}>+ New task</button>
        </header>

        {(notice || error) && (
          <div className={error ? "message error-message" : "message success-message"}>
            {error || notice}
          </div>
        )}

        <div className="stats-grid">
          <div className="stat-card">
            <span>Total tasks</span>
            <strong>{tasks.length}</strong>
          </div>
          <div className="stat-card">
            <span>Pending</span>
            <strong>{pendingCount}</strong>
          </div>
          <div className="stat-card">
            <span>Completed</span>
            <strong>{completedCount}</strong>
          </div>
        </div>

        {showCreate && currentUser && (
          <section className="panel create-panel">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">NEW TASK</p>
                <h2>Create and assign</h2>
              </div>
            </div>
            <CreateTaskForm
              users={users}
              currentUserId={currentUser.id}
              busy={creating}
              onSubmit={handleCreate}
              onCancel={() => setShowCreate(false)}
            />
          </section>
        )}

        <section className="tasks-section">
          <div className="section-heading">
            <div>
              <p className="eyebrow">WORKSPACE</p>
              <h2>Your tasks</h2>
            </div>
            <span>{tasks.length} items</span>
          </div>

          {tasks.length === 0 ? (
            <div className="empty-state">
              <h3>No tasks yet</h3>
              <p>Create your first task and assign it to yourself or another user.</p>
              <button className="secondary-button" onClick={() => setShowCreate(true)}>Create a task</button>
            </div>
          ) : (
            <div className="task-grid">
              {tasks.map((task) => (
                <TaskCard
                  task={task}
                  currentUserId={currentUser?.id || ""}
                  completing={completingId === task.id}
                  onComplete={handleComplete}
                  key={task.id}
                />
              ))}
            </div>
          )}
        </section>
      </section>
    </main>
  );
}
