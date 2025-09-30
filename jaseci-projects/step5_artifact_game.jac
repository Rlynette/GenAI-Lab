# // step5_artifact_game.jac
import random;

walker ArtifactGame {
    has name: str;
    has action: str = "idle";   # default so spawn works without passing it

    can start with `root entry;
    can explore with location entry;
}

node location {
    has artifact: str;
    has available: bool;
}

with entry:__main__ {
    root spawn ArtifactGame("Collector-A");
    root spawn ArtifactGame("Collector-B");
    root spawn ArtifactGame("Collector-C");
}

# -----------------------------
# Implementation section
# -----------------------------

impl ArtifactGame.start {
    if not [root --> (`?location)] {
        let artifacts = ["Amulet", "Orb", "Crown", "Statue"];
        for i = 0 to i < 4 by i += 1 {
            root ++> location(artifact=artifacts[i], available=True);  # use True
        }
        print("🔧 Locations created for Artifact Hunt.");
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
                print(f"🏺 {self.name} found the {here.artifact}!");
                here.available = False;          # use False
                self.action = "collected";
            } else {
                print(f"🔎 {self.name} searched {here.artifact}'s location but found nothing.");
                self.action = "searched";
            }
        } else {
            print(f"🔒 {self.name} arrives: the {here.artifact} has already been collected.");
        }

        visit [-->];
    }
}
