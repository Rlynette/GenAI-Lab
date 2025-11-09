# BE/combined.jac — auto-generated (readme_summarizer + repo_mapper)
# NOTE: This file concatenates the two walker files so jac serve will expose both.

# ----- begin readme_summarizer -----
# BE/readme_summarizer.jac
# Minimal, parser-safe readme summarizer walker.
import py_module.project_summary as ps;

walker readme_summarizer {
  has repo_path: str = "";

  # single simple HTTP-capable entry node
  can run with `root entry {
    # prefer self.repo_path, else pass empty string to python helper
    path = self.repo_path if self.repo_path != "" else "";

    # info report to help debugging
    report [ { "info": "readme_summarizer: starting; path_provided: " + path } ];

    # call python helper; let python handle missing REPO_URL or exceptions
    summary = ps.build_project_summary(path);

    # return whatever the python helper returns (project_summary or error dict)
    report [ { "project_summary": summary } ];
  }
}

# ----- end readme_summarizer -----

# ----- begin repo_mapper -----
import py_module.repo_utils as repo;

walker repo_mapper {
    has url: str = "";
    has depth: int = 1;

    can run with `root entry {
        # decide URL (explicit field or fallback env)
        u = self.url if self.url != "" else "";
        if u == "" {
            # read fallback env in Python helper (repo.clone_repo will fallback if needed)
            print("repo_mapper: starting; url=(empty, will use REPO_URL fallback)");
        } else {
            print("repo_mapper: starting; url=" + u);
        }

        cloned = repo.clone_repo(u, "tmp_clones");
        print("repo_mapper: cloned to " + cloned);

        tree = {} if self.depth <= 0 else repo.file_tree(cloned, self.depth);

        # Use quoted string keys so runtime produces JSON keys (not variable lookups).
        report [ { "cloned_path": cloned, "tree": tree } ];
    }
}

# ----- end repo_mapper -----
