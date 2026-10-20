package matchmaking.strategy.server;

import java.util.Objects;
import java.util.Optional;

public class ServerSelectionContext {
    private ServerSelectionStrategy strategy;

    public ServerSelectionContext(ServerSelectionStrategy strategy) {
        setStrategy(strategy);
    }

    public void setStrategy(ServerSelectionStrategy strategy) {
        this.strategy = Objects.requireNonNull(strategy);
    }

    public Optional<ServerCandidate> select(ServerPool pool) {
        return strategy.select(pool);
    }
}
