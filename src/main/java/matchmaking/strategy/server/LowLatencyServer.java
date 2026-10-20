package matchmaking.strategy.server;

import java.util.Comparator;
import java.util.Optional;

public class LowLatencyServer implements ServerSelectionStrategy {
    @Override
    public Optional<ServerCandidate> select(ServerPool pool) {
        return pool.eligible().min(Comparator.comparingInt(ServerCandidate::latencyMs));
    }
}
