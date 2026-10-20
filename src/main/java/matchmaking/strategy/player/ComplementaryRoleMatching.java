package matchmaking.strategy.player;

import java.util.Comparator;
import java.util.Optional;

public class ComplementaryRoleMatching implements PlayerMatchingStrategy {
    @Override
    public Optional<Player> select(PlayerPool pool) {
        return pool.eligible().min(
                Comparator.comparing((Player player) -> player.role().equals(pool.seeker().role()))
                        .thenComparingInt(player -> Math.abs(player.rating() - pool.seeker().rating())));
    }
}
