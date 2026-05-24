# Threading

Use one [`Repo`](api/repo) session per thread. Do not share handles across threads without external locking (libfits v0 contract).

Each `Repo` wraps a single libfits session handle opened at construction and closed on `close()` or context-manager exit.
