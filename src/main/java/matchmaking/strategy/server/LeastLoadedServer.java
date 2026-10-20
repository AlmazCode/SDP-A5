package matchmaking.strategy.server;

import java.util.Objects;
import java.util.Optional;

public class LeastLoadedServer implements ServerSelectionStrategy {
    private final ServerLoadSource loads;

    public LeastLoadedServer(ServerLoadSource loads) {
        this.loads = Objects.requireNonNull(loads);
    }

    @Override
    public Optional<ServerCandidate> select(ServerPool pool) {
        ServerCandidate selected = null;
        int lowestLoad = 100;
        for (ServerCandidate server : pool.eligible().toList()) {
            // One reading per candidate; repeated comparisons must not re-read a sensor.
            int load = loads.utilizationPercent(server.id());
            if (load < 0 || load > 100) {
                throw new IllegalArgumentException("Server utilization must be between 0 and 100");
            }
            if (load < lowestLoad) {
                lowestLoad = load;
                selected = server;
            }
        }
        return Optional.ofNullable(selected);
    }
}
