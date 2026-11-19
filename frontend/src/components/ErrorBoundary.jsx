import { Component } from "react";

// Catches rendering crashes so the user sees a friendly message instead of a blank page.
export default class ErrorBoundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(error, info) { console.error("UI crashed:", error, info); }
  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="mx-auto max-w-md py-24 text-center">
        <h1 className="text-2xl font-bold">Something went wrong</h1>
        <p className="mt-2 text-slate-500 dark:text-slate-400">An unexpected error occurred. Reloading the page usually fixes it.</p>
        <button onClick={() => window.location.assign("/")} className="mt-5 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">Back to home</button>
      </div>
    );
  }
}
