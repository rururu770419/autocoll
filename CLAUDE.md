# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Autocoll** is a multi-store management system for pickup/dispatch operations, designed for adult entertainment establishments. The system manages staff, casts, customers, courses, hotels, schedules, reservations, and financial transactions across multiple stores.

**Tech Stack:**
- Backend: Flask (Python)
- Database: PostgreSQL with psycopg3
- Frontend: Vanilla JavaScript with Bootstrap
- Scheduler: APScheduler for automated notifications
- External APIs: Twilio (voice calls), LINE Bot API (messaging)

## Key Development Commands

### Running the Application
```bash
# Start the Flask server (runs on port 5001)
python app.py
```

### Database Management
```bash
# Check database connection and tables
python check_db.py

# Direct PostgreSQL access
# Connection details in config.py:
# - Database: pickup_system
# - User: postgres
# - Port: 5432
```

### Testing the Scheduler
```bash
# Test the notification scheduler independently
python scheduler.py
```

## Architecture Overview

### Multi-Store Architecture

The system supports multiple stores through a `store_id` column in all tables. URLs are prefixed with store codes:
- `/nagano/...` → store_id: 1
- `/isesaki/...` → store_id: 2
- `/globalwork/...` → store_id: 3

**Critical:** All database queries MUST filter by `store_id` to maintain data isolation between stores.

Store mapping is managed in `database/connection.py:109-129` via the `get_store_id()` function.

### Database Layer

**Connection Pattern (REQUIRED):**
```python
from database.connection import get_db

db = get_db()
cursor = db.execute("SELECT * FROM users WHERE id = %s", (user_id,))
result = cursor.fetchone()  # Returns dict automatically
db.close()
```

**Critical Rules:**
1. Use `psycopg3` (imported as `psycopg`), NOT `psycopg2`
2. Use `get_db()` which returns a `PostgreSQLConnectionWrapper` with dict_row pre-configured
3. Results are dictionaries: access as `result['column_name']`, NOT `result.column_name`
4. Use `%s` for placeholders, NOT `?`
5. Always filter by `store_id` in WHERE clauses

The wrapper class (`database/connection.py:14-59`) provides SQLite-like `.execute()` method while using PostgreSQL.

### Route Registration Pattern

**DO NOT** use `register_XXX_routes(app)` pattern. Instead:

1. Define individual functions in route modules (e.g., `routes/discount.py`)
2. Import and register in `routes/main.py` using `main_routes.add_url_rule()`

Example:
```python
# routes/example.py
def example_management(store):
    return render_template('example.html', store=store)

# routes/main.py
from .example import example_management
main_routes.add_url_rule('/<store>/example', 'example_management',
                         example_management, methods=['GET'])
```

Exception: Some legacy routes still use Blueprint pattern (e.g., `ng_bp`, `cast_mypage_bp`).

### Frontend Architecture

**HTML Templates:**
- Base: `templates/base.html` (all pages extend this)
- Structure:
  ```html
  {% extends "base.html" %}
  {% block extra_head %} <!-- CSS here --> {% endblock %}
  {% block title %}タイトル{% endblock %}
  {% block content %} <!-- Main content --> {% endblock %}
  {% block extra_scripts %} <!-- JS here --> {% endblock %}
  ```

**CSS Scoping:**
- NEVER use tag selectors (e.g., `body {}`, `h1 {}`)
- ALWAYS use class-scoped selectors with unique prefixes (e.g., `.discount-container {}`)
- Main color: `#00BCD4` (cyan)
- Table header background: `#5a5a5a`

**JavaScript Pattern:**
- Each feature has its own JS file in `static/js/`
- Uses vanilla JavaScript with fetch API for AJAX calls
- Common pattern: load data on page load, provide CRUD operations via API endpoints

### Notification System

**Scheduler (`scheduler.py`):**
- Runs every 5 minutes via APScheduler
- Checks `pickup_records` table for upcoming pickups
- Sends Twilio voice calls to casts (if `auto_call_enabled=TRUE`)
- Sends LINE messages to staff (if `line_id` is set)
- Timing based on `notification_minutes_before` column

**Integration:**
- Scheduler starts automatically in `app.py:152` when Flask app runs
- Must run with `debug=False` to prevent duplicate scheduler instances
- Status endpoint: `/<store>/admin/scheduler/status`

### Common Patterns

**Store ID Resolution:**
```python
from database.connection import get_store_id
store_id = get_store_id(store_code)  # 'nagano' → 1
```

**Database Query with Store Filter:**
```python
cursor = db.execute("""
    SELECT * FROM customers
    WHERE store_id = %s AND customer_id = %s
""", (store_id, customer_id))
```

**API Response Format:**
```python
return {'success': True, 'data': result}
# or
return {'success': False, 'error': 'Error message'}, 400
```

## Design System (CRITICAL)

All new features MUST match existing design patterns. Reference `templates/options.html` and `static/js/options.js` as the canonical example.

### UI Components

**Toggle Switch (rounded):**
```css
.xxx-toggle-slider {
    border-radius: 24px;  /* Rounded, NOT square */
}
.xxx-toggle-checkbox:checked + .xxx-toggle-slider {
    background-color: #00BCD4;
}
```

**Status Badge (rounded button style):**
```css
.xxx-status-active {
    display: inline-block;
    padding: 4px 12px;
    background-color: #28a745;
    color: #ffffff;
    font-weight: bold;
    border-radius: 20px;
}
```

**Sort Buttons:**
- Use `{% if loop.first %}` for disabling "move up" button
- Use `{% if loop.last %}` for disabling "move down" button
- Both `disabled` attribute AND `.xxx-sort-btn-disabled` class required
- Icons: `fa-chevron-up`, `fa-chevron-down`

**Table Styling:**
- Header background: `#5a5a5a`
- Cell padding: `6px`
- Edit icon: `fa-pencil-alt` (color `#00BCD4`)
- Delete icon: `fa-trash-alt` (color `#dc3545`)

## Important Files

- `app.py` - Main Flask application entry point
- `config.py` - Database and API credentials (LINE, Twilio)
- `database/connection.py` - Database connection wrapper and store mapping
- `routes/main.py` - Central route registration
- `scheduler.py` - Background notification scheduler
- `docs/SKILL.md` - Comprehensive Japanese development guide (read this for detailed rules)

## Workflow for Adding New Features

1. **Database:** Create table with `store_id` column and index
2. **Database Module:** Create `database/xxx_db.py` with CRUD functions
3. **Route Module:** Create `routes/xxx.py` with view and API functions
4. **Register Routes:** Import and add routes in `routes/main.py`
5. **Template:** Create `templates/xxx.html` extending `base.html`
6. **CSS:** Add scoped styles in `<style>` block or separate file
7. **JavaScript:** Create `static/js/xxx.js` for client-side logic
8. **Test:** Verify across all store codes (nagano, isesaki, globalwork)

## Common Pitfalls

1. **DON'T** use `result.column_name` - use `result['column_name']`
2. **DON'T** add `row_factory=dict_row` to cursor - already configured in `get_db()`
3. **DON'T** forget `WHERE store_id = %s` in queries
4. **DON'T** use `register_XXX_routes(app)` pattern for new features
5. **DON'T** use square toggles or plain text status - use rounded buttons
6. **DON'T** copy design from just any page - use options.html as reference

## Store Addition Procedure

To add a new store:
1. Add mapping in `database/connection.py` `get_store_id()` function
2. Add entry in `DB_PATHS` dictionary with display name
3. Insert store record in `stores` table (if exists)
4. Test all features with new store code in URL
