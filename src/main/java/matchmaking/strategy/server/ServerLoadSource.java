package matchmaking.strategy.server;

@FunctionalInterface
public interface ServerLoadSource {
    /** Returns current utilization from 0 (idle) to 100 (full). */
    int utilizationPercent(String serverId);
}
