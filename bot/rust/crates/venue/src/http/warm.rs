//! Keep-warm: a GET /time on any order connection idle for >= warm_s (an idle connection costs
//! +20-40 ms on the next request, reports/infra-plan.md). Mirrors venue/worker.py `_idle`.

use std::sync::atomic::Ordering;
use std::time::Duration;

use futures_util::future::join_all;
use tokio::task::JoinHandle;

use super::conn::Req;
use super::pool::Clob;

impl Clob {
    /// Spawn the keep-warm loop; abort the handle to stop it. Round trips land in `ping_ns()`.
    pub fn spawn_keep_warm(&self, warm_s: f64) -> JoinHandle<()> {
        let clob = self.clone();
        let warm_ns = (warm_s.max(0.05) * 1e9) as u64;
        tokio::spawn(async move {
            loop {
                let idle = clob.idle_ns();
                let due: Vec<usize> = (0..idle.len()).filter(|&i| idle[i] >= warm_ns).collect();
                if !due.is_empty() {
                    let rs = join_all(due.iter().map(|&i| clob.on(i, Req::get("/time")))).await;
                    for r in rs {
                        if r.code != 0 {
                            clob.inner.ping_ns[r.conn].store(r.t_ack_mono_ns - r.t_send_mono_ns, Ordering::Relaxed);
                        }
                    }
                }
                // sleep until the next connection comes due (bounded 10 ms .. warm_s)
                let idle = clob.idle_ns();
                let next = idle.iter().map(|&x| warm_ns.saturating_sub(x.min(warm_ns))).min().unwrap_or(warm_ns);
                tokio::time::sleep(Duration::from_nanos(next.clamp(10_000_000, warm_ns))).await;
            }
        })
    }
}
