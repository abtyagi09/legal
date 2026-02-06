# SQLite MCP Integration

## Overview

The legal agent now uses **SQLite with Model Context Protocol (MCP)** for data persistence instead of the mock API. This provides:

- **Real database storage** for cases, attorneys, clients, and invoices
- **MCP-based access** using industry-standard protocol
- **Better performance** with indexed queries
- **Production-ready** data persistence

## Architecture

```
Legal Agent
    ↓
Database Tools (database_tools.py)
    ↓
MCP Client (mcp_client.py)
    ↓
SQLite MCP Server (@modelcontextprotocol/server-sqlite)
    ↓
legal_cases.db
```

## Database Schema

### Tables

#### `attorneys`
- `id` TEXT PRIMARY KEY
- `name` TEXT
- `specialty` TEXT
- `hourly_rate` REAL
- `years_experience` INTEGER
- `bar_number` TEXT
- `email` TEXT
- `phone` TEXT
- `available` INTEGER (0=no, 1=yes)

#### `clients`
- `id` TEXT PRIMARY KEY
- `name` TEXT
- `email` TEXT
- `phone` TEXT
- `company` TEXT
- `created_date` TEXT

#### `cases`
- `id` TEXT PRIMARY KEY
- `case_number` TEXT UNIQUE
- `title` TEXT
- `type` TEXT
- `status` TEXT
- `filed_date` TEXT
- `attorney_id` TEXT (FK → attorneys)
- `client` TEXT
- `next_hearing` TEXT
- `estimated_value` REAL

#### `invoices`
- `id` TEXT PRIMARY KEY
- `invoice_number` TEXT UNIQUE
- `client_name` TEXT
- `date` TEXT
- `status` TEXT (PAID/OUTSTANDING)
- `total` REAL

#### `invoice_items`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `invoice_id` TEXT (FK → invoices)
- `description` TEXT
- `amount` REAL

#### `legal_rates`
- `id` INTEGER PRIMARY KEY AUTOINCREMENT
- `service` TEXT
- `rate` REAL
- `unit` TEXT (default: 'hour')

## Setup

### 1. Create Database

```bash
python setup_database.py
```

This creates `legal_cases.db` and populates it with:
- 5 attorneys
- 4 clients
- 4 cases
- 3 invoices with items
- 7 legal service rates

### 2. MCP Configuration

Located in `.mcp/config.json`:

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sqlite",
        "C:\\agents\\legal\\legal_cases.db"
      ]
    }
  }
}
```

### 3. Dependencies

- Python: `mcp>=1.0.0` (already installed)
- Node.js: Required for MCP server (included in Docker)
- NPM package: `@modelcontextprotocol/server-sqlite` (auto-installed by npx)

## Usage

### Database Tools API

The agent automatically uses database tools for:

```python
# Case operations
await db_tools.search_cases_db(query="Smith")
await db_tools.get_case_details_db(case_number="2025-CV-10001")
await db_tools.create_legal_case_db(
    title="New Case",
    case_type="Contract Dispute",
    client="John Doe",
    attorney_id="att-001"
)
await db_tools.update_case_status_db(
    case_number="2025-CV-10001",
    status="Active"
)

# Attorney operations
await db_tools.get_attorney_info_db(attorney_id="att-001")

# Invoice operations
await db_tools.search_invoices_db(query="TechSolutions")
await db_tools.get_invoice_db(invoice_number="INV-2026-001")

# Rates
await db_tools.get_legal_rates_db()
```

### Fallback Behavior

If database tools are unavailable, the agent automatically falls back to integration_actions (API-based).

## Sample Data

### Attorneys
- Sarah Johnson - Corporate Law ($500/hr, 15 years)
- Michael Chen - Intellectual Property ($450/hr, 12 years)
- Emily Rodriguez - Employment Law ($425/hr, 10 years)
- David Kim - Real Estate ($400/hr, 8 years)
- Jessica Williams - Contract Law ($475/hr, 14 years)

### Cases
- Smith v. Jones (Contract Dispute, Active)
- ABC Corp v. XYZ Inc (IP, Active)
- Employee Dispute Matter (Employment, Closed)
- Property Line Dispute (Real Estate, Active)

### Invoices
- INV-2026-001: TechSolutions ($5,700, PAID)
- INV-2026-002: ABC Corporation ($13,600, OUTSTANDING)
- INV-2026-003: TechStart Industries ($4,300, OUTSTANDING)

## Testing

### Test Database Queries

```bash
# Use SQLite CLI
sqlite3 legal_cases.db

# Query cases
SELECT * FROM cases WHERE status = 'Active';

# Query with join
SELECT c.case_number, c.title, a.name as attorney 
FROM cases c 
JOIN attorneys a ON c.attorney_id = a.id;

# Invoice totals by status
SELECT status, SUM(total) 
FROM invoices 
GROUP BY status;
```

### Test Agent

Ask the agent:
- "Show me all active cases"
- "Get details for case 2025-CV-10001"
- "Create a new case for client Jane Doe"
- "Find invoices for TechSolutions"
- "What are the legal service rates?"

## Deployment

The database is included in the Docker image:

```dockerfile
COPY --chown=agentuser:agentuser legal_cases.db ./
```

For production:
1. Use Azure SQL Database or PostgreSQL
2. Mount persistent volume for SQLite
3. Implement database migrations
4. Add backup strategy

## Migration from Mock API

The agent prioritizes database tools over API calls:

1. Check if database tools available
2. If yes → Use database
3. If no → Fall back to integration_actions (API)

To switch back to API-only:
- Remove `database_tools.py`
- Agent will automatically use integration_actions

## Benefits over Mock API

✅ **Persistent storage** - Data survives restarts  
✅ **Relational queries** - JOIN operations, complex filters  
✅ **Transaction support** - ACID compliance  
✅ **Better performance** - Indexed searches  
✅ **Production-ready** - Real database vs. in-memory  
✅ **MCP standard** - Industry protocol for AI-database interaction  
✅ **Easier testing** - Direct SQL access for debugging  

## Next Steps

1. **Add more data** - Populate with realistic case history
2. **Implement migrations** - Version control for schema changes
3. **Add indexes** - Optimize common queries
4. **Set up backups** - Automated backup strategy
5. **Consider PostgreSQL** - For multi-user scenarios
6. **Add audit logs** - Track all database modifications
