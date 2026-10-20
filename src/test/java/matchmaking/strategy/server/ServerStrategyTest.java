package matchmaking.strategy.server;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.CsvSource;
import java.util.List;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

class ServerStrategyTest {
    private final ServerCandidate fast = new ServerCandidate("fast", "EU", 20);
    private final ServerCandidate free = new ServerCandidate("free", "US", 70);
    private final ServerCandidate local = new ServerCandidate("local", "KZ", 40);
    private final ServerPool pool = new ServerPool("KZ", List.of(fast, free, local));
    // Fixed fake data: no API, clock, random values or shared state.
    private final ServerLoadSource loads = id -> Map.of("fast", 90, "free", 10, "local", 50).get(id);
    private final ServerStrategySelector selector = new ServerStrategySelector(loads);

    private ServerSelectionContext context(ServerStrategySelector.Mode mode) {
        return new ServerSelectionContext(selector.manual(mode));
    }

    @Test void lowLatencyChoosesTheFastestServer() {
        assertEquals(fast, context(ServerStrategySelector.Mode.LATENCY).select(pool).orElseThrow());
    }

    @Test void leastLoadedUsesTheInjectedSourceInsteadOfLatency() {
        assertEquals(free, context(ServerStrategySelector.Mode.LOAD).select(pool).orElseThrow());
        var swappedSource = new ServerStrategySelector(id -> id.equals("local") ? 0 : 90);
        assertEquals(local, new ServerSelectionContext(swappedSource.manual(ServerStrategySelector.Mode.LOAD))
                .select(pool).orElseThrow());
    }

    @Test void regionalPrefersLocalThenFallsBackToLowestLatency() {
        assertEquals(local, context(ServerStrategySelector.Mode.REGION).select(pool).orElseThrow());
        assertEquals(fast, context(ServerStrategySelector.Mode.REGION)
                .select(new ServerPool("AU", pool.candidates())).orElseThrow());
        var slowerLocal = new ServerCandidate("local-2", "KZ", 60);
        assertEquals(local, context(ServerStrategySelector.Mode.REGION)
                .select(new ServerPool("KZ", List.of(slowerLocal, local, fast))).orElseThrow());
    }

    @ParameterizedTest
    @EnumSource(ServerStrategySelector.Mode.class)
    void everyStrategyReturnsAnEligibleServerWithoutChangingTheInput(ServerStrategySelector.Mode mode) {
        var slow = new ServerCandidate("slow", "KZ", 101);
        var candidates = List.of(slow, fast, free, local);
        var input = new ServerPool("KZ", candidates);
        var result = context(mode).select(input).orElseThrow();
        assertTrue(candidates.contains(result));
        assertTrue(result.latencyMs() >= 0 && result.latencyMs() <= 100);
        assertEquals(candidates, input.candidates());
        assertTrue(context(mode).select(new ServerPool("KZ", List.of())).isEmpty());
        assertTrue(context(mode).select(new ServerPool("KZ", List.of(slow))).isEmpty());
        var boundary = new ServerCandidate("free", "US", 100);
        assertEquals(boundary, context(mode).select(new ServerPool("KZ", List.of(boundary))).orElseThrow());
    }

    @ParameterizedTest
    @CsvSource({
            "true, 100, fast",
            "true, 0, fast",
            "false, 80, free",
            "false, 100, free",
            "false, 79, local",
            "false, 0, local"
    })
    void automaticSelectionFollowsRulesInPriorityOrder(boolean competitive, int demand, String expected) {
        var context = new ServerSelectionContext(selector.automatic(competitive, demand));
        assertEquals(expected, context.select(pool).orElseThrow().id());
    }

    @Test void contextCanSwitchAtRuntimeIncludingAnUnknownImplementation() {
        var context = context(ServerStrategySelector.Mode.LATENCY);
        assertEquals(fast, context.select(pool).orElseThrow());
        context.setStrategy(selector.manual(ServerStrategySelector.Mode.LOAD));
        assertEquals(free, context.select(pool).orElseThrow());
        context.setStrategy(input -> java.util.Optional.of(local));
        assertEquals(local, context.select(pool).orElseThrow());
        assertThrows(NullPointerException.class, () -> context.setStrategy(null));
        assertThrows(NullPointerException.class, () -> new ServerSelectionContext(null));
        assertThrows(NullPointerException.class, () -> new ServerStrategySelector(null));
    }

    @Test void leastLoadedReadsEachEligibleServerOncePerCallAndRefreshesOnNextCall() {
        var readings = new java.util.HashMap<String, Integer>();
        var current = new java.util.HashMap<>(Map.of("fast", 90, "free", 10, "local", 50));
        ServerLoadSource changing = id -> {
            readings.merge(id, 1, Integer::sum);
            return current.get(id);
        };
        var strategy = new LeastLoadedServer(changing);
        assertEquals(free, strategy.select(pool).orElseThrow());
        assertEquals(Map.of("fast", 1, "free", 1, "local", 1), readings);
        current.put("fast", 0);
        assertEquals(fast, strategy.select(pool).orElseThrow());
        assertEquals(Map.of("fast", 2, "free", 2, "local", 2), readings);
    }

    @Test void fullServersAreExcludedAndInvalidLoadIsRejected() {
        assertTrue(new LeastLoadedServer(id -> 100).select(pool).isEmpty());
        assertThrows(IllegalArgumentException.class, () -> new LeastLoadedServer(id -> -1).select(pool));
        assertThrows(IllegalArgumentException.class, () -> new LeastLoadedServer(id -> 101).select(pool));
    }

    @Test void simulatedSourceCopiesItsSnapshotAndTreatsUnknownServersAsFull() {
        var values = new java.util.HashMap<>(Map.of("fast", 40));
        var source = new SimulatedServerLoadSource(values);
        values.put("fast", 80);
        assertEquals(40, source.utilizationPercent("fast"));
        assertEquals(100, source.utilizationPercent("unknown"));
    }

    @Test void equalScoresKeepTheFirstCandidate() {
        var tie = new ServerCandidate("tie", fast.region(), fast.latencyMs());
        var input = new ServerPool("EU", List.of(fast, tie));
        var equalLoads = new ServerStrategySelector(id -> 25);
        for (var mode : ServerStrategySelector.Mode.values()) {
            assertEquals(fast, new ServerSelectionContext(equalLoads.manual(mode)).select(input).orElseThrow());
        }
    }

    @Test void dataRejectsInvalidValuesAndCopiesTheCandidateList() {
        assertThrows(IllegalArgumentException.class, () -> new ServerCandidate("", "EU", 0));
        assertThrows(IllegalArgumentException.class, () -> new ServerCandidate("x", "", 0));
        assertThrows(IllegalArgumentException.class, () -> new ServerCandidate("x", "EU", -1));
        assertThrows(IllegalArgumentException.class, () -> new ServerPool("", List.of()));
        assertThrows(IllegalArgumentException.class, () -> selector.automatic(false, -1));
        assertThrows(IllegalArgumentException.class, () -> selector.automatic(false, 101));
        var mutable = new java.util.ArrayList<>(List.of(fast));
        var input = new ServerPool("KZ", mutable);
        mutable.clear();
        assertEquals(List.of(fast), input.candidates());
    }
}
