package matchmaking.strategy;

import matchmaking.common.CsvStore;
import matchmaking.facade.MatchmakingFacade;
import matchmaking.strategy.player.*;
import matchmaking.strategy.server.*;
import java.io.PrintStream;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

public class StrategyDemo {
    public static void main(String[] args) {
        run(new CsvStore(Path.of(args.length == 0 ? "data-strategy" : args[0])), System.out);
    }

    public static void run(CsvStore store, PrintStream out) {
        var seeker = new Player("you", 1000, "tank", 30);
        var players = new PlayerPool(seeker, List.of(
                new Player("close", 1010, "tank", 10),
                new Player("waiting", 1200, "tank", 180),
                new Player("support", 1100, "healer", 50)));
        var servers = new ServerPool("KZ", List.of(
                new ServerCandidate("fast", "EU", 20),
                new ServerCandidate("free", "US", 70),
                new ServerCandidate("local", "KZ", 40)));
        var loadValues = Map.of("fast", 90, "free", 10, "local", 50);
        var playerSelector = new PlayerStrategySelector();
        var serverSelector = new ServerStrategySelector(new SimulatedServerLoadSource(loadValues));

        out.println("Assignment 5: Strategy Pattern");
        out.println("Player input: " + players);
        out.println("Same player input, every algorithm:");
        for (var mode : PlayerStrategySelector.Mode.values()) {
            var context = new PlayerMatchingContext(playerSelector.manual(mode));
            out.println(mode + " -> " + context.select(players).orElseThrow().id());
        }
        out.println("Server input: " + servers + "; utilization (%): " + loadValues);
        out.println("Same server input, every algorithm:");
        for (var mode : ServerStrategySelector.Mode.values()) {
            var context = new ServerSelectionContext(serverSelector.manual(mode));
            out.println(mode + " -> " + context.select(servers).orElseThrow().id());
        }

        var playerContext = new PlayerMatchingContext(playerSelector.manual(PlayerStrategySelector.Mode.SKILL));
        var serverContext = new ServerSelectionContext(serverSelector.manual(ServerStrategySelector.Mode.LATENCY));
        var manualPlayer = playerContext.select(players).orElseThrow();
        var manualServer = serverContext.select(servers).orElseThrow();
        out.println("Manual player: " + manualPlayer.id());
        out.println("Manual server: " + manualServer.id());
        playerContext.setStrategy(playerSelector.manual(PlayerStrategySelector.Mode.WAITING));
        serverContext.setStrategy(serverSelector.manual(ServerStrategySelector.Mode.LOAD));
        out.println("Runtime player switch: " + manualPlayer.id() + " -> " + playerContext.select(players).orElseThrow().id());
        out.println("Runtime server switch: " + manualServer.id() + " -> " + serverContext.select(servers).orElseThrow().id());

        out.println("Automatic situation: casual team match, waited 30 seconds, demand 90%");
        playerContext.setStrategy(playerSelector.automatic(false, seeker.waitingSeconds(), true));
        serverContext.setStrategy(serverSelector.automatic(false, 90));
        var selectedPlayer = playerContext.select(players).orElseThrow();
        var selectedServer = serverContext.select(servers).orElseThrow();
        out.println("Automatic player: " + selectedPlayer.id());
        out.println("Automatic server: " + selectedServer.id());
        var match = new MatchmakingFacade(store).startMatch(
                seeker.rating(), selectedPlayer.rating(), selectedServer.latencyMs(), false, 0);
        out.println("Existing Facade: " + match.stage() + " | ID: " + match.id());
    }
}
