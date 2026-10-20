package matchmaking.strategy;

import matchmaking.common.CsvStore;
import matchmaking.facade.ChainRepository;
import matchmaking.facade.MatchChain;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.io.ByteArrayOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import static org.junit.jupiter.api.Assertions.*;

class StrategyDemoTest {
    @TempDir Path disk;

    @Test void demoShowsAllAlgorithmsThenStartsAMatchWithAutomaticSelections() {
        var output = new ByteArrayOutputStream();
        var store = new CsvStore(disk);
        StrategyDemo.run(store, new PrintStream(output, true, StandardCharsets.UTF_8));
        String text = output.toString(StandardCharsets.UTF_8);
        for (String result : new String[]{"SKILL -> close", "WAITING -> waiting", "ROLE -> support",
                "LATENCY -> fast", "LOAD -> free", "REGION -> local",
                "Manual player: close", "Automatic player: support",
                "Manual server: fast", "Automatic server: free",
                "Runtime player switch: close -> waiting", "Runtime server switch: fast -> free",
                "COMPLETED"}) {
            assertTrue(text.contains(result), result);
        }
        var matches = new ChainRepository(store).all();
        assertEquals(1, matches.size());
        assertEquals(1000, matches.get(0).rating1());
        assertEquals(1100, matches.get(0).rating2());
        assertEquals(70, matches.get(0).latency());
        assertEquals(MatchChain.Stage.COMPLETED, matches.get(0).stage());
    }

    @Test void mainUsesTheSuppliedStorageDirectory() {
        var original = System.out;
        try {
            System.setOut(new PrintStream(new ByteArrayOutputStream()));
            StrategyDemo.main(new String[]{disk.toString()});
        } finally {
            System.setOut(original);
        }
        assertEquals(1, new ChainRepository(new CsvStore(disk)).all().size());
    }
}
