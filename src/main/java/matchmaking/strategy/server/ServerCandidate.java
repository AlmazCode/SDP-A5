package matchmaking.strategy.server;

public record ServerCandidate(String id, String region, int latencyMs) {
    public ServerCandidate {
        if (id == null || id.isBlank() || region == null || region.isBlank() || latencyMs < 0) {
            throw new IllegalArgumentException("Server ID/region must not be blank; latency must be nonnegative");
        }
    }
}
