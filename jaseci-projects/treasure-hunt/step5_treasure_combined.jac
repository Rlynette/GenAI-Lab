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
