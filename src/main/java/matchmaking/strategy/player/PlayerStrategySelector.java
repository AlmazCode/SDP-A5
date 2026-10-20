package matchmaking.strategy.player;

public class PlayerStrategySelector {
    public enum Mode { SKILL, WAITING, ROLE }

    public PlayerMatchingStrategy manual(Mode mode) {
        return switch (mode) {
            case SKILL -> new SkillBasedMatching();
            case WAITING -> new LongestWaitingMatching();
            case ROLE -> new ComplementaryRoleMatching();
        };
    }

    public PlayerMatchingStrategy automatic(boolean ranked, int waitingSeconds, boolean teamMode) {
        if (waitingSeconds < 0) throw new IllegalArgumentException("Waiting time must be nonnegative");
        if (ranked) return manual(Mode.SKILL);
        if (waitingSeconds >= 120) return manual(Mode.WAITING);
        if (teamMode) return manual(Mode.ROLE);
        return manual(Mode.SKILL);
    }
}
