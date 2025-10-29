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
