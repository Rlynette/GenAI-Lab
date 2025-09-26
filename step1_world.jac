# step1_world.jac — compatible with the Step-0 style that worked for you

walker build_world {
    with entry {
        # create a simple list of room names instead of declaring node types
        let rooms = ["Cave", "Forest", "Lake"];

        # report creation
        print(f"🌍 World created with {rooms[0]}, {rooms[1]}, {rooms[2]}.");
    }
}

