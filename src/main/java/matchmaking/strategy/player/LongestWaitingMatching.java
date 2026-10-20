package matchmaking.strategy.player;

import java.util.Comparator;
import java.util.Optional;

public class LongestWaitingMatching implements PlayerMatchingStrategy {
    @Override
    public Optional<Player> select(PlayerPool pool) {
        return pool.eligible().max(Comparator.comparingInt(Player::waitingSeconds));
    }
}
