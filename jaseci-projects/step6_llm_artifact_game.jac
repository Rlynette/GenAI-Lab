# // step6_llm_artifact_game.jac
import random;

# byLLM integration — load actual LLM model
# You can change model_name depending on provider:
#   - "openai/gpt-4o-mini"
#   - "gemini/gemini-2.0-flash"
#   - "anthropic/claude-3.5-sonnet"
import from byllm.llm { Model }
glob llm = Model(model_name="gemini/gemini-2.0-flash", verbose=False);

# LLM-backed Jac function
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

with entry:__main__ {
    root spawn ArtifactGame("Collector-A");
    root spawn ArtifactGame("Collector-B");
    root spawn ArtifactGame("Collector-C");
}

# // stepB_llm_artifact_game.impl.jac
import random;

impl ArtifactGame.start {
    if not [root --> (`?location)] {
        let artifacts = ["Amulet", "Orb", "Crown", "Statue"];
        for i = 0 to i < len(artifacts) by i += 1 {
            root ++> location(artifact=artifacts[i], available=True);
        }
        print("🎮 AI-powered Artifact Hunt started.");
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
                # Found artifact
                print(f"🏺 {self.name} found the {here.artifact}!");
                print(artifact_hint(self.name, here.artifact, True));
                here.available = False;
                self.action = "collected";
            } else {
                # Searched but failed — request LLM hint
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
