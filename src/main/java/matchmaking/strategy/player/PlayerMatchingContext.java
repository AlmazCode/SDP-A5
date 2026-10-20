package matchmaking.strategy.player;

import java.util.Objects;
import java.util.Optional;

public class PlayerMatchingContext {
    private PlayerMatchingStrategy strategy;

    public PlayerMatchingContext(PlayerMatchingStrategy strategy) {
        setStrategy(strategy);
    }

    public void setStrategy(PlayerMatchingStrategy strategy) {
        this.strategy = Objects.requireNonNull(strategy);
    }

    public Optional<Player> select(PlayerPool pool) {
        return strategy.select(pool);
    }
}
