import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

const RunContext = createContext(null);

/**
 * Session-scoped record of the most recent verification run — feeds the
 * A2A protocol monitor page (parity with Streamlit's `st.session_state.agent_logs`).
 */
export function RunProvider({ children }) {
  const [agentLogs, setAgentLogs] = useState([]);
  const [lastRunAt, setLastRunAt] = useState(null);

  const recordRun = useCallback((logs) => {
    setAgentLogs(Array.isArray(logs) ? logs : []);
    setLastRunAt(Date.now());
  }, []);

  const clearRuns = useCallback(() => {
    setAgentLogs([]);
    setLastRunAt(null);
  }, []);

  const value = useMemo(
    () => ({ agentLogs, lastRunAt, recordRun, clearRuns }),
    [agentLogs, lastRunAt, recordRun, clearRuns]
  );

  return <RunContext.Provider value={value}>{children}</RunContext.Provider>;
}

export function useRuns() {
  const ctx = useContext(RunContext);
  if (!ctx) throw new Error('useRuns must be used within a RunProvider');
  return ctx;
}
