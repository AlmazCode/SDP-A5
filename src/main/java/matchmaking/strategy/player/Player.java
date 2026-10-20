package matchmaking.strategy.player;

public record Player(String id, int rating, String role, int waitingSeconds) {
    public Player {
        if (id == null || id.isBlank() || role == null || role.isBlank()) {
            throw new IllegalArgumentException("Player ID and role must not be blank");
        }
        if (rating < 0 || rating > 5000 || waitingSeconds < 0) {
            throw new IllegalArgumentException("Rating must be 0-5000; waiting time must be nonnegative");
        }
    }
}
