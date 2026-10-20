package matchmaking.strategy.player;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.CsvSource;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class PlayerStrategyTest {
    private final Player seeker = new Player("you", 1000, "tank", 30);
    private final Player closest = new Player("close", 1010, "tank", 10);
    private final Player waiting = new Player("waiting", 1200, "tank", 180);
    private final Player support = new Player("support", 1100, "healer", 50);
    private final PlayerPool pool = new PlayerPool(seeker, List.of(closest, waiting, support));
    private final PlayerStrategySelector selector = new PlayerStrategySelector();

    private PlayerMatchingContext context(PlayerStrategySelector.Mode mode) {
        return new PlayerMatchingContext(selector.manual(mode));
    }

    @Test void skillChoosesTheSmallestRatingGap() {
        assertEquals(closest, context(PlayerStrategySelector.Mode.SKILL).select(pool).orElseThrow());
    }

    @Test void waitingChoosesTheLongestWaitingEligiblePlayer() {
        assertEquals(waiting, context(PlayerStrategySelector.Mode.WAITING).select(pool).orElseThrow());
    }

    @Test void rolePrefersAComplementaryRoleThenTheClosestRating() {
        var otherHealer = new Player("other", 1250, "healer", 300);
        var candidates = new PlayerPool(seeker, List.of(closest, otherHealer, support));
        assertEquals(support, context(PlayerStrategySelector.Mode.ROLE).select(candidates).orElseThrow());
        assertEquals(closest, context(PlayerStrategySelector.Mode.ROLE)
                .select(new PlayerPool(seeker, List.of(waiting, closest))).orElseThrow());
    }

    @ParameterizedTest
    @EnumSource(PlayerStrategySelector.Mode.class)
    void everyStrategyReturnsAnEligibleCandidateWithoutChangingTheInput(PlayerStrategySelector.Mode mode) {
        Player invalid = new Player("too-far", 2000, "healer", 1000);
        var candidates = List.of(seeker, invalid, closest, waiting, support);
        var input = new PlayerPool(seeker, candidates);
        var result = context(mode).select(input).orElseThrow();
        assertTrue(candidates.contains(result));
        assertNotEquals(seeker.id(), result.id());
        assertTrue(Math.abs(seeker.rating() - result.rating()) <= 300);
        assertEquals(candidates, input.candidates());
        assertTrue(context(mode).select(new PlayerPool(seeker, List.of(seeker, invalid))).isEmpty());
        assertTrue(context(mode).select(new PlayerPool(seeker, List.of())).isEmpty());
        var boundary = new Player("boundary", 1300, "tank", 0);
        assertEquals(boundary, context(mode).select(new PlayerPool(seeker, List.of(boundary))).orElseThrow());
    }

    @ParameterizedTest
    @CsvSource({
            "true, 180, true, close",
            "true, 0, false, close",
            "false, 120, true, waiting",
            "false, 121, false, waiting",
            "false, 119, true, support",
            "false, 0, false, close"
    })
    void automaticSelectionFollowsRulesInPriorityOrder(boolean ranked, int waited, boolean team, String expected) {
        var context = new PlayerMatchingContext(selector.automatic(ranked, waited, team));
        assertEquals(expected, context.select(pool).orElseThrow().id());
    }

    @Test void contextCanSwitchAtRuntimeIncludingAnUnknownImplementation() {
        var context = context(PlayerStrategySelector.Mode.SKILL);
        assertEquals(closest, context.select(pool).orElseThrow());
        context.setStrategy(selector.manual(PlayerStrategySelector.Mode.WAITING));
        assertEquals(waiting, context.select(pool).orElseThrow());
        context.setStrategy(input -> java.util.Optional.of(support));
        assertEquals(support, context.select(pool).orElseThrow());
        assertThrows(NullPointerException.class, () -> context.setStrategy(null));
        assertThrows(NullPointerException.class, () -> new PlayerMatchingContext(null));
    }

    @Test void equalScoresKeepTheFirstCandidate() {
        var tied = new Player("tie", closest.rating(), closest.role(), closest.waitingSeconds());
        for (var mode : PlayerStrategySelector.Mode.values()) {
            assertEquals(closest, context(mode).select(new PlayerPool(seeker, List.of(closest, tied))).orElseThrow());
        }
    }

    @Test void dataRejectsInvalidValuesAndCopiesTheCandidateList() {
        assertThrows(IllegalArgumentException.class, () -> new Player("", 1000, "tank", 0));
        assertThrows(IllegalArgumentException.class, () -> new Player("x", -1, "tank", 0));
        assertThrows(IllegalArgumentException.class, () -> new Player("x", 5001, "tank", 0));
        assertThrows(IllegalArgumentException.class, () -> new Player("x", 1000, "", 0));
        assertThrows(IllegalArgumentException.class, () -> new Player("x", 1000, "tank", -1));
        assertThrows(IllegalArgumentException.class, () -> selector.automatic(false, -1, false));
        assertThrows(NullPointerException.class, () -> new PlayerPool(null, List.of()));
        var mutable = new java.util.ArrayList<>(List.of(closest));
        var input = new PlayerPool(seeker, mutable);
        mutable.clear();
        assertEquals(List.of(closest), input.candidates());
    }
}
