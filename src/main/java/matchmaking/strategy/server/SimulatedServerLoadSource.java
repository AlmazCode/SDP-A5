package matchmaking.strategy.server;

import java.util.Map;

public class SimulatedServerLoadSource implements ServerLoadSource {
    private final Map<String, Integer> loads;

    public SimulatedServerLoadSource(Map<String, Integer> loads) {
        this.loads = Map.copyOf(loads);
    }

    @Override
    public int utilizationPercent(String serverId) {
        return loads.getOrDefault(serverId, 100);
    }
}
