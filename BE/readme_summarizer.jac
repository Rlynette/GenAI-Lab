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
