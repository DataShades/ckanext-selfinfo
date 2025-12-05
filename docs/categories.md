## Categories

By default, Selfinfo displays only essential system information (`platform_info` and basic CKAN status) to provide a lightweight initial experience. You can expand the available data by configuring `ckan.selfinfo.categories_list` with the specific categories you need.

This approach allows you to:

- **Start simple** — New installations show only core metrics without overwhelming users
- **Add as needed** — Enable additional categories based on your specific monitoring requirements
- **Optimize performance** — Reduce data collection overhead by excluding unnecessary categories (e.g., skip Blueprint data on CKAN job workers, or Python modules on large projects)

See [Config Settings](config_settings.md) for configuration examples.

---

### Available Categories

Configure which categories to display using:

```ini
ckan.selfinfo.categories_list = platform_info ram_usage disk_usage
```

#### `platform_info`

**Default:** Enabled  
**Description:** Core system information including OS distribution, Python version, platform details, and Python environment prefix.

---

#### `python_modules`

**Default:** Disabled  
**Description:** Lists all installed Python packages (CKAN core, CKAN extensions, and other dependencies) with version information. Updates periodically to fetch latest available versions from PyPI. Useful for dependency auditing but can be resource-intensive for large projects.

---

#### `ram_usage`

**Default:** Disabled  
**Description:** Memory usage statistics including total RAM, used memory, percentage utilization, and top 10 processes consuming the most memory.

---

#### `disk_usage`

**Default:** Disabled  
**Description:** Disk space information for configured partitions. Shows total capacity, free space, and usage percentage. Partitions can be customized via `ckan.selfinfo.partitions` setting.

---

#### `git_info`

**Default:** Disabled  
**Description:** Git repository information for CKAN and installed extensions. Displays current branch, commit hash, detached HEAD status, tags, and remote URLs. Requires `ckan.selfinfo.ckan_repos_path` configuration.

---

#### `freeze`

**Default:** Disabled  
**Description:** Python package freeze output (equivalent to `pip freeze`). Lists all installed packages with exact versions in requirements.txt format. Useful for environment replication and dependency management.

---

#### `errors`

**Default:** Disabled  
**Description:** Application errors collected by Selfinfo's error handler. Stores recent errors in Redis with timestamps, URLs, and full stack traces. Maximum error count controlled by `ckan.selfinfo.errors_limit`.

---

#### `actions`

**Default:** Disabled  
**Description:** All registered CKAN API actions with their docstrings, allowed HTTP methods (GET/POST), side-effect-free status, and generated cURL examples. Includes information about chained actions.

---

#### `auth_actions`

**Default:** Disabled  
**Description:** Authorization functions registered in CKAN with their docstrings and chained status. Shows which auth functions control access to specific actions.

---

#### `blueprints`

**Default:** Disabled  
**Description:** Flask blueprints registered in the CKAN application. Lists all routes, their URL patterns, accepted HTTP methods, endpoint names, and associated view functions.

---

#### `helpers`

**Default:** Disabled  
**Description:** Template helper functions available in CKAN templates. Includes function names, docstrings, source file locations, and chained status. Excludes built-in Python functions.

---

#### `ckan_cli_commands`

**Default:** Disabled  
**Description:** Click-based CLI commands registered in CKAN (via `ckan` command). Shows command tree with subcommands, arguments, options, types, and help text.

---

#### `ckan_queues`

**Default:** Disabled  
**Description:** Background job queues managed by CKAN Jobs. Displays queue names, job counts, job details (ID, title, created date), and overflow indicators for queues with more than 100 jobs.

---

#### `ckan_solr_schema`

**Default:** Disabled  
**Description:** Solr schema XML used by CKAN for search indexing. Fetches the schema file directly from Solr admin API. Requires `ckan.selfinfo.solr_schema_filename` configuration.

---

### Example Configuration

**Minimal setup (default):**

```ini
# Only platform info and basic status (no explicit config needed)
```

**Production monitoring:**

```ini
ckan.selfinfo.categories_list = platform_info ram_usage disk_usage errors ckan_queues
```

**Development environment:**

```ini
ckan.selfinfo.categories_list = platform_info git_info freeze actions helpers blueprints
```

**Job worker instance:**

```ini
# Exclude UI-related categories
ckan.selfinfo.categories_list = platform_info ram_usage errors ckan_queues
```