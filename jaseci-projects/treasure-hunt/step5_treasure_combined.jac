import random

node Game {
    has rooms: list;
    has treasure_index: int;
    has player_pos: int;
    has won: bool;
    has keys_found: int;
    has doors_locked: list;

    can init;
    can play;
    can move;
    can search;
}

walker init {
    has rooms: list = ["Hall", "Kitchen", "Bedroom", "Garden"];
    has treasure_index: int;
    has player_pos: int = 0;
    has won: bool = false;
    has keys_found: int = 0;
    has doors_locked: list;

    init {
        root.rooms = rooms;
        root.treasure_index = random.randint(0, len(root.rooms) - 1);
        root.player_pos = 0;
        root.won = false;
        root.keys_found = 0;
        root.doors_locked = [random.choice([true, false]) for _ in root.rooms];
        print("Game initialized. Try to find the treasure!");
    }
}

walker play {
    start {
        print("Welcome to the Treasure Hunt!");
        print("Rooms:", root.rooms);
        print("Enter 'move' to go to the next room or 'search' to look for treasure/keys.");
    }
}

walker move {
    can player_input: str;

    start {
        if root.won {
            print("🎉 You already found the treasure! Start a new game to play again.");
            stop;
        }

        if root.player_pos < len(root.rooms) - 1 {
            if root.doors_locked[root.player_pos + 1] == true and root.keys_found == 0 {
                print("🚪 The next door is locked! You need a key.");
            } else {
                if root.doors_locked[root.player_pos + 1] == true and root.keys_found > 0 {
                    root.keys_found -= 1;
                    root.doors_locked[root.player_pos + 1] = false;
                    print("🔓 You used a key to unlock the door.");
                }
                root.player_pos += 1;
                print(f"➡️ You moved to {root.rooms[root.player_pos]}.");
            }
        } else {
            print("🚧 You are at the last room already.");
        }
    }
}

walker search {
    start {
        if root.won {
            print("🎉 You already found the treasure!");
            stop;
        }

        if root.player_pos == root.treasure_index {
            print("🎉 Congratulations! You found the treasure in", root.rooms[root.player_pos]);
            root.won = true;
        } else {
            # 30% chance to find a key
            if random.random() < 0.3 {
                root.keys_found += 1;
                print(f"🔑 You found a key! Total keys: {root.keys_found}");
            } else {
                print("❌ No treasure here. Keep looking.");
            }
        }
    }
}



# // step6_llm_artifact_game.jac
import random;

# /* byLLM integration - uncomment/adjust model_name as you prefer.
#    Model picks provider credentials from environment variables set in the shell
#    (e.g. OPENAI_API_KEY). */
import from byllm.llm { Model }
glob llm = Model(model_name="gemini/gemini-2.0-flash", verbose=False);

# /* LLM-backed Jac function. Jac will delegate these calls to byLLM. */
def artifact_hint(player: str, artifact: str, success: bool) -> str by llm();

walker ArtifactGame {
    has name: str;
    has action: str = "idle";

    can start with `root entry;
    can explore with location entry;
}

node location {
    has artifact: str;
    has available: bool;
}

# /* Spawn multiple collectors to demonstrate scale-agnostic behavior */
with entry:__main__ {
    root spawn ArtifactGame("Collector-A");
    root spawn ArtifactGame("Collector-B");
    root spawn ArtifactGame("Collector-C");
}

# // step6_llm_artifact_game.impl.jac
import random;

impl ArtifactGame.start {
    if not [root --> (`?location)] {
        let artifacts = ["Amulet", "Orb", "Crown", "Statue"];
        for i = 0 to i < len(artifacts) by i += 1 {
            root ++> location(artifact=artifacts[i], available=True);
        }
        print("🔧 Locations created for AI-Enhanced Artifact Hunt.");
    }

    next = [root --> (`?location)];
    visit next;
}

impl ArtifactGame.explore {
    if [-->] {
        visit [-->];
    } else {
        if here.available {
            if random.random() < 0.5 {
                # // Found the artifact
                print(f"🏺 {self.name} found the {here.artifact}!");
                # // Call LLM-backed function (synchronous). If byLLM/model fails it will raise.
                print(artifact_hint(self.name, here.artifact, True));
                here.available = False;
                self.action = "collected";
            } else {
                # // Searched but nothing found — request LLM hint
                print(f"🔎 {self.name} searched {here.artifact}'s location but found nothing.");
                print(artifact_hint(self.name, here.artifact, False));
                self.action = "searched";
            }
        } else {
            print(f"🔒 {self.name} arrives: the {here.artifact} has already been collected.");
        }

        visit [-->];
    }
}

