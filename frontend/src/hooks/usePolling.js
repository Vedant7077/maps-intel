import { useState, useEffect, useRef } from 'react';
import { fetchJob } from '../lib/api';

export function usePolling(jobId) {
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!jobId) return;

    const poll = async () => {
      try {
        const data = await fetchJob(jobId);
        setJob(data);
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(intervalRef.current);
        }
      } catch (err) {
        setError(err);
        clearInterval(intervalRef.current);
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 2000);

    return () => clearInterval(intervalRef.current);
  }, [jobId]);

  return { job, error };
}
