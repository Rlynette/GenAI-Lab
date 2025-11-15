# BE/analysis.jac
# Walkers to analyze repo, query CCG, and generate docs using python helpers.

import py_module.code_analyzer as ca;
import py_module.ccg_builder as ccg;
import py_module.docgen as dg;

# repo_analyze: run static analyzer and return JSON
walker repo_analyze {
    has repo_path: str = "";
    has depth: int = 1;

    can run with `root entry {
        p = self.repo_path if self.repo_path != "" else "";
        report [ { "info": "repo_analyze: starting; path_provided: " + p } ];
        analysis = ca.analyze_path(p);
        report [ { "analysis": analysis } ];
    }
}

# repo_query: build CCG and run simple queries (callers, callees, inherits)
walker repo_query {
    has repo_path: str = "";
    has depth: int = 1;
    has qtype: str = "";
    has target: str = "";

    can run with `root entry {
        p = self.repo_path if self.repo_path != "" else "";
        report [ { "info": "repo_query: starting; path_provided: " + p } ];
        analysis = ca.analyze_path(p);
        graph = ccg.build_ccg(p);

        ans = {};
        if self.qtype == "callers" {
            ans = ccg.query_callers(graph, self.target);
        } else {
            if self.qtype == "callees" {
                ans = ccg.query_callees(graph, self.target);
            } else {
                if self.qtype == "inherits" {
                    ans = ccg.query_inherits(graph, self.target);
                } else {
                    ans = { "error": "unknown qtype: " + self.qtype };
                }
            }
        }
        report [ { "result": ans } ];
    }
}

# repo_docgen: generate markdown README (write to disk if output_path provided)
walker repo_docgen {
    has repo_path: str = "";
    has depth: int = 1;
    has output_path: str = "";

    can run with `root entry {
        p = self.repo_path if self.repo_path != "" else "";
        report [ { "info": "repo_docgen: starting; path_provided: " + p } ];
        analysis = ca.analyze_path(p);
        graph = ccg.build_ccg(p);

        if self.output_path != "" {
            res = dg.build_and_write(analysis, graph, self.output_path);
            report [ { "result": res } ];
        } else {
            md = dg.generate_markdown(analysis, graph);
            report [ { "markdown": md } ];
        }
    }
}
