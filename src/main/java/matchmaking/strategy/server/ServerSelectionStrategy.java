package matchmaking.strategy.server;

import java.util.Optional;

@FunctionalInterface
public interface ServerSelectionStrategy {
    Optional<ServerCandidate> select(ServerPool pool);
}
