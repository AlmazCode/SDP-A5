package matchmaking.strategy.player;

import java.util.List;
import java.util.Objects;
import java.util.stream.Stream;

public record PlayerPool(Player seeker, List<Player> candidates) {
    public PlayerPool {
        Objects.requireNonNull(seeker);
        candidates = List.copyOf(candidates);
    }

    // Shared domain constraints also satisfy Assignment 4's SkillRatingService.
    public Stream<Player> eligible() {
        return candidates.stream()
                .filter(player -> !player.id().equals(seeker.id()))
                .filter(player -> Math.abs(player.rating() - seeker.rating()) <= 300);
    }
}
