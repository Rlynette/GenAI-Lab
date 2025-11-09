# BE/repo_mapper.jac
# Minimal repo_mapper walker using py_module.repo_utils

import py_module.repo_utils as repo;

walker repo_mapper {
    entry {
        u = "";
        if (fields.url != null) { u = fields.url; };
        if (u == "") {
            print("repo_mapper: starting; url=(empty, will use REPO_URL fallback)");
        } else {
            print("repo_mapper: starting; url=" + u);
        };

        cloned = repo.clone_repo(u, "tmp_clones");
        print("repo_mapper: cloned to " + cloned);

        # Depth: accept fields.depth (default 1), but keep it simple here
        depth = 1;
        if (fields.depth != null) { depth = fields.depth; };

        tree = repo.file_tree(cloned, depth);
        report [ { "cloned_path": cloned, "tree": tree } ];
    };
}
