package matchmaking.strategy.server;

import java.util.Comparator;
import java.util.Optional;

public class RegionalServer implements ServerSelectionStrategy {
    @Override
    public Optional<ServerCandidate> select(ServerPool pool) {
        return pool.eligible().min(
                Comparator.comparing((ServerCandidate server) -> !server.region().equals(pool.preferredRegion()))
                        .thenComparingInt(ServerCandidate::latencyMs));
    }
}
