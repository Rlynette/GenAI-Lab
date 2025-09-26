# /* step4_treasure_combined.jac
#    Treasure Hunt Game - Step 4 (Keys added)
# */

import random;

obj TreasureHunt {
    has rooms: list;
    has player_pos: int;
    has attempts: int;
    has won: bool;
    has treasure_index: int;
    has keys_found: int;

    def init;
    def play;
    def process_command(cmd: str);
    def move(direction: str);
    def search();
}

# /* Implementations */

impl TreasureHunt.init {
    self.rooms = ["Cave", "Forest", "Lake"];
    self.treasure_index = random.randint(0, len(self.rooms) - 1);
    self.player_pos = 0;
    self.won = False;
    self.attempts = 10;
    self.keys_found = 0;

    print(f"🎮 Welcome to the Treasure Hunt!");
    print(f"🌍 You start at {self.rooms[self.player_pos]}.");
}

impl TreasureHunt.play {
    self.init();

    while self.attempts > 0 and not self.won {
        cmd = input(f"You are in {self.rooms[self.player_pos]}. Enter command (move/search): ");
        self.process_command(cmd);
    }

    if not self.won {
        print("⛔ Game over! You didn't find the treasure.");
    }
}

impl TreasureHunt.process_command(cmd: str) {
    if cmd.lower() == "move" {
        dir = input("Enter direction (left/right): ");
        self.move(dir);
    } elif cmd.lower() == "search" {
        self.search();
    } else {
        print("❌ Invalid command. Type 'move' or 'search'.");
    }
}

impl TreasureHunt.move(direction: str) {
    if direction.lower() == "left" {
        self.player_pos = (self.player_pos - 1) % len(self.rooms);
    } elif direction.lower() == "right" {
        self.player_pos = (self.player_pos + 1) % len(self.rooms);
    } else {
        print("❌ Invalid direction. Use 'left' or 'right'.");
        return;
    }
    self.attempts -= 1;
    print(f"➡ You moved to {self.rooms[self.player_pos]}. Attempts left: {self.attempts}");
}

impl TreasureHunt.search {
    self.attempts -= 1;

    # 30% chance to find a key
    if random.random() < 0.3 {
        self.keys_found += 1;
        print(f"🔑 You found a key! Total keys: {self.keys_found}");
    }

    if self.player_pos == self.treasure_index {
        print(f"🏆 Congratulations! You found the treasure in {self.rooms[self.player_pos]}!");
        self.won = True;
    } else {
        print(f"🔍 No treasure here in {self.rooms[self.player_pos]}. Attempts left: {self.attempts}");
    }
}

# /* Run the game */
with entry {
    game = TreasureHunt();
    game.play();
}
