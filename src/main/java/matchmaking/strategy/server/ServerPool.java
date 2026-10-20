package matchmaking.strategy.server;

import java.util.List;
import java.util.stream.Stream;

public record ServerPool(String preferredRegion, List<ServerCandidate> candidates) {
    public ServerPool {
        if (preferredRegion == null || preferredRegion.isBlank()) {
            throw new IllegalArgumentException("Preferred region must not be blank");
        }
        candidates = List.copyOf(candidates);
    }

    // Matches the latency limit enforced by the existing ServerAllocator.
    public Stream<ServerCandidate> eligible() {
        return candidates.stream().filter(server -> server.latencyMs() <= 100);
    }
}
