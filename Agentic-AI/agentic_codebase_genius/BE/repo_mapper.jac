import py_module.repo_utils as repo;

walker repo_mapper {
    can run with `root entry {
        print("repo_mapper: starting");

        cloned = repo.clone_repo("", dest_parent="tmp_clones");
        print("repo_mapper: cloned to " + cloned);

        tree = repo.file_tree(cloned, 2);
        print("repo_mapper: file tree keys preview -> " + (list(tree.keys())[0:10] |> str));

        print("repo_mapper: done");
    }
}
