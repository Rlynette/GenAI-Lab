# BE/readme_summarizer.jac
# Minimal, parser-safe readme summarizer walker.
# - Reads fields.repo_path (HTTP), falls back to env(REPO_URL).
# - Calls py_module.project_summary.build_project_summary(path) (if importable).
# - Returns project_summary or an error report.

walker readme_summarizer {
    entry {
        # resolve path: prefer fields.repo_path, then env(REPO_URL)
        path = "";
        if (fields.repo_path != null) { path = fields.repo_path; };
        if (path == "") { path = env(REPO_URL); };

        if (path == "") {
            report [ { error: "no repo_path provided and REPO_URL not set" } ];
        } else {
            report [ { info: "readme_summarizer: starting for " + path } ];

            # call python helper inside try/catch so server returns friendly JSON on failure
            try {
                summary = py_module.project_summary.build_project_summary(path);
                report [ { project_summary: summary } ];
            } catch (e) {
                report [ { error: str(e) } ];
            };
        };
    };
}
