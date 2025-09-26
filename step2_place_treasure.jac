# step2_place_treasure.jac — compatible with your working Jac style

walker place_treasure {
    with entry {
        # rooms list must match Step 1
        let rooms = ["Cave", "Forest", "Lake"];

        # deterministic treasure placement for now (index 1 -> "Forest")
        let treasure_index = 1;
        let treasure = rooms[treasure_index];

        print(f"🎯 Treasure placed in: {treasure}");
    }
}
