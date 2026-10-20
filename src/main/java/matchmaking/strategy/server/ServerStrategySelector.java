package matchmaking.strategy.server;

import java.util.Objects;

public class ServerStrategySelector {
    public enum Mode { LATENCY, LOAD, REGION }
    private final ServerLoadSource loads;

    public ServerStrategySelector(ServerLoadSource loads) {
        this.loads = Objects.requireNonNull(loads);
    }

    public ServerSelectionStrategy manual(Mode mode) {
        return switch (mode) {
            case LATENCY -> new LowLatencyServer();
            case LOAD -> new LeastLoadedServer(loads);
            case REGION -> new RegionalServer();
        };
    }

    public ServerSelectionStrategy automatic(boolean competitive, int demandPercent) {
        if (demandPercent < 0 || demandPercent > 100) {
            throw new IllegalArgumentException("Demand must be between 0 and 100");
        }
        if (competitive) return manual(Mode.LATENCY);
        if (demandPercent >= 80) return manual(Mode.LOAD);
        return manual(Mode.REGION);
    }
}
