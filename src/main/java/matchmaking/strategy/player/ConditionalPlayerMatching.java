package matchmaking.strategy.player;

import java.util.Comparator;
import java.util.Objects;
import java.util.Optional;

/**
 * Assignment 5 BEFORE version: every algorithm lives in this switch.
 * Adding an algorithm requires editing this class.
 */
public class ConditionalPlayerMatching implements PlayerMatchingStrategy {
    private final PlayerStrategySelector.Mode mode;

    public ConditionalPlayerMatching(PlayerStrategySelector.Mode mode) {
        this.mode = Objects.requireNonNull(mode);
    }

    @Override
    public Optional<Player> select(PlayerPool pool) {
        return switch (mode) {
            case SKILL -> pool.eligible().min(Comparator.comparingInt(
                    player -> Math.abs(player.rating() - pool.seeker().rating())));
            case WAITING -> pool.eligible().max(Comparator.comparingInt(Player::waitingSeconds));
            case ROLE -> pool.eligible().min(
                    Comparator.comparing((Player player) -> player.role().equals(pool.seeker().role()))
                            .thenComparingInt(player -> Math.abs(player.rating() - pool.seeker().rating())));
        };
    }
}
