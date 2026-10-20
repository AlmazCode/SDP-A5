# Video Game Matchmaking

Assignment 5: Strategy, built on Assignment 4: Facade. Java 17+, Maven, JUnit 5, CSV files.

## Assignment 5 report

[PDF diagrams](output/pdf/SDP_Assignment_5_Sabirzhanov_Emil.pdf):
assignment title, author, player matching UML, server selection UML, runtime selection
sequence and links to the repository and refactoring commits.

Vector diagrams: [player matching](docs/strategy/player-matching.svg),
[server selection](docs/strategy/server-selection.svg),
[runtime selection](docs/strategy/runtime-selection.svg).

To rebuild the PDF, run `python3 docs/report/build_report.py`
with Python packages `reportlab` and `pypdf` installed.
The generator uses bundled fonts with their licenses in `docs/report/`.

## Assignment 5: run

```sh
./run-strategy.sh
```

After building, the equivalent command is:

```sh
java -cp target/matchmaking-1.0.jar matchmaking.strategy.StrategyDemo
```

An optional first argument sets the storage directory. The default is `data-strategy/`.
The original Assignment 4 console menu remains available with `./run.sh`.

The demo prints the same candidate pools for all six algorithms, demonstrates manual selection,
changes strategies on existing contexts with `setStrategy()`, then selects automatically.
The selected player ratings plus server latency go into `MatchmakingFacade.startMatch()`.
The facade reserves the party, allocates the server, confirms the session, then saves its CSV records.
Its existing schema stores ratings plus latency; candidate IDs appear in the demo output.

## Assignment 5: two strategy families

**Player matching:** every algorithm excludes the seeker and candidates whose rating gap exceeds 300.

| Strategy | Algorithm | Demo result |
| --- | --- | --- |
| `SkillBasedMatching` | Minimize the absolute rating gap. | `close` |
| `LongestWaitingMatching` | Maximize the candidate's waiting time. | `waiting` |
| `ComplementaryRoleMatching` | Prefer a different role, then minimize the rating gap. | `support` |

**Server selection:** every algorithm excludes servers with latency above 100 ms.

| Strategy | Algorithm | Demo result |
| --- | --- | --- |
| `LowLatencyServer` | Minimize latency. | `fast` |
| `LeastLoadedServer` | Read utilization from an injected source; minimize load below 100%. | `free` |
| `RegionalServer` | Prefer the requested region, then minimize latency. | `local` |

These algorithms select a domain entity; they do not implement sorting algorithms.
The role strategy falls back to the closest rating when no complementary role exists.
The regional strategy falls back to the lowest latency when no local server exists.
Equal scores keep the first candidate in input order. No suitable candidate produces `Optional.empty()`.
Inputs are immutable snapshots. Invalid ratings, negative measurements, blank identifiers,
out-of-range percentages and null strategies are rejected.

### Selectors

Rules are evaluated from top to bottom:

| Selector | Situation | Strategy |
| --- | --- | --- |
| `PlayerStrategySelector` | Ranked match | Skill |
| `PlayerStrategySelector` | Casual match; seeker waited at least 120 seconds | Longest waiting |
| `PlayerStrategySelector` | Casual team match; shorter wait | Complementary role |
| `PlayerStrategySelector` | Remaining situations | Skill |
| `ServerStrategySelector` | Competitive match | Low latency |
| `ServerStrategySelector` | Noncompetitive match; demand at least 80% | Least loaded |
| `ServerStrategySelector` | Remaining situations | Regional |

`manual(Mode)` makes an explicit choice; `automatic(...)` chooses from the situation.
Only selectors branch on which algorithm to construct. Contexts hold an interface reference,
accept it in their constructor, replace it through `setStrategy()`, then delegate `select()`.
Domain validation and comparisons inside algorithms do not choose a strategy type.

### Isolation from external data

`LeastLoadedServer` depends on our `ServerLoadSource` interface.
`SimulatedServerLoadSource` supplies a fixed snapshot; an unknown server is treated as full.
Tests also inject fake lambdas with fixed values. A real monitoring adapter can implement the
same interface without changing the strategy or context.

Each selection reads every eligible server once, so a changing sensor cannot return
contradictory values during repeated comparisons. The next selection obtains fresh readings.
The load strategy excludes full servers and rejects measurements outside 0–100%.
Latency and regional policies do not consult utilization; their eligibility contract is latency only.

### Class responsibilities

Assignment 5 production types, including interfaces and records:

| Type | Responsibility |
| --- | --- |
| `Player` | Stores a validated queued player's attributes. |
| `PlayerPool` | Exposes eligible player candidates from an immutable snapshot. |
| `PlayerMatchingStrategy` | Defines the player selection contract. |
| `PlayerMatchingContext` | Delegates player selection to its replaceable strategy. |
| `SkillBasedMatching` | Selects the eligible player with the smallest rating gap. |
| `LongestWaitingMatching` | Selects the eligible player with the longest waiting time. |
| `ComplementaryRoleMatching` | Selects a complementary role with rating proximity as the secondary criterion. |
| `PlayerStrategySelector` | Chooses the player matching policy. |
| `PlayerStrategySelector.Mode` | Names the built-in manual player policies. |
| `ServerCandidate` | Stores a validated server candidate's attributes. |
| `ServerPool` | Exposes eligible server candidates from an immutable snapshot. |
| `ServerSelectionStrategy` | Defines the server selection contract. |
| `ServerSelectionContext` | Delegates server selection to its replaceable strategy. |
| `LowLatencyServer` | Selects the eligible server with the lowest latency. |
| `LeastLoadedServer` | Selects the least utilized eligible server using injected measurements. |
| `RegionalServer` | Selects a preferred region with latency as the secondary criterion. |
| `ServerStrategySelector` | Chooses the server selection policy. |
| `ServerStrategySelector.Mode` | Names the built-in manual server policies. |
| `ServerLoadSource` | Defines access to server utilization measurements. |
| `SimulatedServerLoadSource` | Supplies utilization measurements from a fixed snapshot. |
| `StrategyDemo` | Demonstrates interchangeable matchmaking policies through a complete match. |

### Why Strategy, not State or Template Method

This solution uses Strategy because each family represents interchangeable algorithms for
the same operation. Player policies receive a `PlayerPool` and return an optional player;
server policies receive a `ServerPool` and return an optional server. A caller can use any
implementation through the same interface. Different results on identical input are expected:
fairness by rating, queue waiting time and role compatibility are different matchmaking goals.
Server latency, external utilization and regional preference similarly express different goals.

Each context delegates work through composition. It neither knows concrete algorithm classes
nor examines their types. The client can inject a policy directly, ask a selector to choose one,
or replace the policy while retaining the same context and input. To add an algorithm,
implement the family interface and pass the new object to the context. Existing strategies
and contexts remain unchanged. Registering that algorithm as a new built-in manual choice,
or assigning it an automatic rule, is a separate change in the selector. The tests inject
previously unknown implementations to demonstrate this extension point.

State also uses composition, but represents lifecycle-dependent behavior and transitions.
Our policies do not describe lifecycle stages, own transitions, or replace themselves.
The selector chooses a policy from the current situation, and the caller installs it.
The existing `NEW`, `RESERVED` and `CANCELLED` party statuses belong to the earlier
assignment's lifecycle model; they do not determine which matching algorithm object exists.

Template Method puts a fixed algorithm skeleton in a superclass and allows subclasses to
override selected steps. Here there is no shared algorithm superclass or inherited skeleton.
Each strategy owns its selection logic, and runtime replacement changes behavior through an
interface reference. Shared pool filtering only enforces domain constraints; it does not call
subclass hooks. This keeps the independent algorithms small and allows their data dependencies,
such as server utilization, to be replaced without modifying the contexts.

### Before and after refactoring

The player family was first committed with all three algorithms in one
`ConditionalPlayerMatching.select()` switch. The next commit extracted the branches into
three strategy classes and moved construction choices into the selector.
The context API and **the entire `PlayerStrategyTest.java` file are identical** on both commits.
All 42 tests present at that stage pass before and after the refactor.

- [Before: conditional algorithms, `ebfded4`](https://github.com/AlmazCode/SDP-A5/commit/ebfded42276c855ed7cb6cb623ed048ae08d482e)
- [After: extracted strategies, `bfb4c78`](https://github.com/AlmazCode/SDP-A5/commit/bfb4c782c1d61c1c203c66eb49e4489c6f464458)

Both refactoring commits are preserved in this standalone Assignment 5 repository.

Inspect the refactoring locally:

```sh
git show ebfded4:src/main/java/matchmaking/strategy/player/ConditionalPlayerMatching.java
git diff ebfded4 bfb4c78 -- src/main/java/matchmaking/strategy/player
git diff ebfded4 bfb4c78 -- src/test/java/matchmaking/strategy/player/PlayerStrategyTest.java
```

The final command produces no output because the behavioral tests were not changed.
To independently test either commit without modifying the current working directory:

```sh
snapshot=$(mktemp -d)
git archive ebfded4 | tar -x -C "$snapshot"
mvn -f "$snapshot/pom.xml" test
# Repeat with bfb4c78 in a new temporary directory for the after version.
```

### Assignment 5 tests and defense

```sh
mvn clean verify
```

The complete suite has 62 tests: 27 existing tests plus 35 Assignment 5 cases.
`PlayerStrategyTest` and `ServerStrategyTest` cover each algorithm, every selector rule,
rule priority, boundary values, empty eligible pools, ties, input immutability and runtime switching.
Both families have an `@ParameterizedTest` checking their common eligibility contract.
Server tests cover fixed fake readings, changing readings, full servers and invalid measurements.
`StrategyDemoTest` checks console output plus the saved match produced through the existing facade.
JaCoCo enforces at least 80% line coverage per package.

For live coding, add a class implementing either strategy interface and inject it through
`setStrategy()`. Change automatic selection by editing a selector rule and its test.
Swap the data source by passing another `ServerLoadSource` to `ServerStrategySelector`.

## Assignment 4: Facade

## Run

```sh
./run.sh
```

After building:

```sh
java -jar target/matchmaking-1.0.jar
```

Data is saved in `data/`. To start fresh, exit the app and delete this folder. Use one app process per folder.

## Structure

| Step | Service | Rule | Entity | Storage |
| --- | --- | --- | --- | --- |
| A | PartyFormation | SkillRatingService | Party | PartyRepository |
| B | ServerAllocator | LatencyChecker | ServerAllocation | AllocationRepository |
| C | SessionService | AntiCheatScanner | GameSession | SessionLogger |

A reserves two players with ratings from 0 to 5000 and a difference of at most 300. B allocates a server if latency is at most 100 ms. C confirms the session if no cheat is detected. Latency and the cheat flag are entered in the menu.

Each subsystem has four classes and its own storage gateway. Subsystems do not call each other. The entities check their own status changes:

- Party: NEW → RESERVED → CANCELLED.
- ServerAllocation: NEW → ALLOCATED → RELEASED.
- GameSession: NEW → CONFIRMED or REJECTED.

`MatchmakingFacade` runs A → B → C and handles failures. `AdminFacade` shows saved records and cancels unfinished matches.

## Demo

Menu: 1 new match, 2 view records, 3 resume by ID, 4 cancel by ID, 0 exit.

For option 1, enter these values in order:

| Case | Rating 1 | Rating 2 | Latency | Cheat y/n | Pause |
| --- | ---: | ---: | ---: | --- | ---: |
| Success | 1000 | 1100 | 50 | n | 0 |
| B fails: cancel A | 1000 | 1100 | 150 | n | 0 |
| C fails: release B, cancel A | 1000 | 1100 | 50 | y | 0 |
| Invalid rating: nothing reserved | -1 | 1100 | 50 | n | 0 |
| Stop after A | 1000 | 1100 | 50 | n | 1 |
| Stop after B | 1000 | 1100 | 50 | y | 2 |

For the restart demo, use pause 1 or 2, copy the match ID, exit and run the app again. Option 2 shows saved records; option 3 continues the match. Option 4 cancels a paused match.

## Storage and rollback

Each match has CSV files in `data/parties`, `data/allocations`, `data/sessions` and `data/chains`. Repositories read files on every call. Writes use a temporary file, flush it and replace the old record.

The chain saves its input, stage, error and rollback order. Stages: PENDING_A, PENDING_B, PENDING_C, COMPLETED, COMPENSATING, COMPENSATED.

If B fails, A becomes CANCELLED. If C fails, B becomes RELEASED before A becomes CANCELLED. C keeps its REJECTED record. The facade checks saved entity statuses to choose what to undo.

On restart, an already saved step is reused. This also works when a step was saved before the chain journal was updated. If a write fails during rollback, the chain stays COMPENSATING. Fix the disk problem and resume the match. Confirmed sessions cannot be cancelled through the admin facade.

`MatchmakingException` covers invalid ratings, high latency and cheat detection. Disk errors use `UncheckedIOException`. Recovery is started through the menu.

## Principle of Least Knowledge

Before: the client creates and calls all three services and must handle their errors.

```java
PartyFormation parties = new PartyFormation(new PartyRepository(store), new SkillRatingService());
ServerAllocator servers = new ServerAllocator(new AllocationRepository(store), new LatencyChecker());
SessionService sessions = new SessionService(new SessionLogger(store), new AntiCheatScanner());
parties.reserve(id, 1000, 1100);
servers.allocate(id, 50);
sessions.confirm(id, false);
// B fails: parties.cancel(id).
// C fails: servers.release(id), then parties.cancel(id).
```

After: the client calls the facades.

```java
MatchmakingFacade matchmaking = new MatchmakingFacade(store);
AdminFacade admin = new AdminFacade(store);
matchmaking.startMatch(1000, 1100, 50, false, 0);
System.out.println(admin.inspect());
```

The client does not need to know the order of the steps or how to undo them. Each subsystem can still be used directly.

## Facade vs Adapter

Facade gives the client one operation over three subsystems. Here, `startMatch` reserves players, allocates a server and confirms a session. It also handles failed steps and saved progress. `AdminFacade` gives a separate interface for viewing and cancelling matches.

Adapter changes an incompatible interface to fit the client's interface. For example, it could wrap a vendor's server API. These subsystems already have usable interfaces; the task is to coordinate them. That is why this project uses Facade.

## Tests

```sh
mvn test
```

The original 27 tests remain in the suite. JaCoCo checks at least 80% line coverage per package.
Report: `target/site/jacoco/index.html`.

F.I.R.S.T.: local files keep tests fast; each test has its own `@TempDir`; inputs are fixed; JUnit checks the results; tests are committed with the code. `matchWith(...)` is the test helper for creating a match.

Tests cover both rollback depths, restarts, failed disk writes, input limits, entity transitions and the menu. `eachSubsystemCanBeUsedWithoutAnyFacade` uses all three subsystems directly:

```sh
mvn -Djacoco.skip=true -Dtest=MatchmakingTest#eachSubsystemCanBeUsedWithoutAnyFacade test
```

[Assignment 4 report](output/pdf/SDP_Assignment_4_Sabirzhanov_Emil.pdf).
