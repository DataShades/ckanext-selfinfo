# Config Settings

This page describes all configuration options available for the Selftools module.

---

## Core Settings

### ckan.selftools.operations_pwd

**Type:** String
**Default:** None
**Required:** Recommended

Provides an additional security layer for operations like update, delete, and create in Selftools categories.

When configured, users must enter this password to perform destructive or modifying operations.

**Example:**

```ini
ckan.selftools.operations_pwd = secure_password_123
```

!!! warning "Security"
    Use a strong, unique password and store it securely. This password protects critical database and configuration operations.

---

### ckan.selftools.operations_limit

**Type:** Integer
**Default:** `100`
**Required:** Optional

Sets a limit for most operations like query, update, and delete to prevent performance issues and accidental bulk modifications.

**Example:**

```ini
ckan.selftools.operations_limit = 50
```

---

### ckan.selftools.categories

**Type:** Space-separated list
**Default:** `solr` (only Solr shown by default)
**Required:** Optional

Specifies which categories to display in Selftools. Available categories: `solr`, `db`, `redis`, `config`, `model`, `datastore`.

By default, only the `solr` category is enabled to provide a minimal initial setup. Add additional categories based on your needs.

**Example:**

```ini
# Enable all categories
ckan.selftools.categories = solr db redis config model datastore

# Enable only database and configuration tools
ckan.selftools.categories = db config
```

!!! tip "Performance"
    Enable only the categories you actively use to reduce interface complexity and improve performance.

---

## Security Settings

### ckan.selftools.tools_blacklist

**Type:** Space-separated list (format: `category.tool_name`)
**Default:** None
**Required:** Optional

Disables specific tools within categories without removing the entire category. Useful for restricting dangerous operations while keeping read-only access.

**Example:**

```ini
# Disable DB update and Redis delete tools
ckan.selftools.tools_blacklist = db.db_update redis.redis_delete
```

**Use cases:**

- Production environments where updates should only happen via controlled processes
- Multi-user setups where some operations should be restricted
- Compliance requirements limiting destructive actions

---

### ckan.selftools.config_blacklist

**Type:** Space-separated list
**Default:** Includes sensitive keys like `sqlalchemy.url`, database credentials, API tokens
**Required:** Optional

Prevents specific CKAN configuration parameters from being exposed in query results. Adds an additional security layer by hiding sensitive values.

The extension has a predefined list of sensitive configurations that are always hidden. This setting allows you to add custom parameters to the blacklist.

**Example:**

```ini
# Hide additional custom configuration keys
ckan.selftools.config_blacklist = ckan.my_custom_api_key ckan.third_party_token
```

!!! info "Default Blacklist"
    The following configurations are hidden by default:

    - `sqlalchemy.url`
    - Database connection strings
    - API keys and tokens
    - Password fields

---

### ckan.selftools.model_fields_blacklist

**Type:** Space-separated list (format: `ModelName.field_name`)
**Default:** `User.password User.apikey`
**Required:** Optional

Hides specific model field values in database query results. The field names will appear in results, but their values will be masked.

**Example:**

```ini
# Hide user emails and package names in query results
ckan.selftools.model_fields_blacklist = User.email Package.name User.password User.apikey
```

**Common use cases:**

- Protecting personally identifiable information (PII)
- Hiding internal identifiers
- Compliance with data privacy regulations

!!! note "Field Masking"
    Hidden fields are replaced with `[HIDDEN]` in query results. The field structure remains visible for schema understanding.

---

### ckan.selftools.model_key_encryption

**Type:** String (encryption key)
**Default:** None
**Required:** Optional

Encryption key used in the Model category to encrypt exported data and secure sensitive information.

When configured, model export operations will encrypt the output using this key.

**Example:**

```ini
ckan.selftools.model_key_encryption = my-secure-encryption-key-2024
```

!!! warning "Key Management"
    - Store encryption keys securely (environment variables, secret managers)
    - Use strong, randomly generated keys
    - Never commit encryption keys to version control
    - Keep backups of keys in secure locations

---

## Example Configurations

### Minimal Setup (Default)

```ini
# Only Solr category enabled, no additional security
```

### Production Environment

```ini
# Limited categories with strong security
ckan.selftools.categories = solr config redis
ckan.selftools.operations_pwd = strong_password_here
ckan.selftools.operations_limit = 50
ckan.selftools.tools_blacklist = db.db_update redis.redis_delete
ckan.selftools.config_blacklist = ckan.custom_api_token
```

### Development Environment

```ini
# All categories enabled for full access
ckan.selftools.categories = solr db redis config model datastore
ckan.selftools.operations_limit = 200
ckan.selftools.model_fields_blacklist = User.password User.apikey
```

### High-Security Setup

```ini
# Maximum restrictions for sensitive environments
ckan.selftools.categories = config
ckan.selftools.operations_pwd = very_strong_password
ckan.selftools.operations_limit = 10
ckan.selftools.tools_blacklist = config.config_update db.db_update db.db_delete redis.redis_delete
ckan.selftools.config_blacklist = ckan.custom_key ckan.api_token
ckan.selftools.model_fields_blacklist = User.email User.password User.apikey Package.name
ckan.selftools.model_key_encryption = encryption-key-2024
```
