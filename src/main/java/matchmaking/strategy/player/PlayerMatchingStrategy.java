package matchmaking.strategy.player;

import java.util.Optional;

@FunctionalInterface
public interface PlayerMatchingStrategy {
    Optional<Player> select(PlayerPool pool);
}
