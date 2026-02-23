# Sample Do's and Don'ts Guidelines

## Code Quality Do's

### DO: Follow Clean Code Principles
- Write self-documenting code with clear variable and function names
- Keep functions small and focused on a single responsibility
- Use meaningful comments for complex logic only
- Follow consistent naming conventions throughout the codebase

### DO: Implement Proper Error Handling
- Use try-catch blocks for operations that may fail
- Provide meaningful error messages
- Log errors appropriately for debugging
- Handle edge cases and validate inputs

### DO: Write Secure Code
- Validate and sanitize all user inputs
- Use parameterized queries to prevent SQL injection
- Implement proper authentication and authorization
- Store sensitive data securely (encrypted)
- Keep dependencies up to date

### DO: Follow Best Practices
- Write unit tests for critical functionality
- Document public APIs and complex functions
- Use version control effectively with meaningful commit messages
- Perform code reviews before merging
- Follow the DRY (Don't Repeat Yourself) principle

### DO: Optimize Performance
- Use appropriate data structures and algorithms
- Avoid unnecessary database queries
- Implement caching where appropriate
- Profile code to identify bottlenecks

## Code Quality Don'ts

### DON'T: Write Spaghetti Code
- Avoid deeply nested conditionals (max 3 levels)
- Don't create functions longer than 50 lines
- Avoid circular dependencies
- Don't mix business logic with presentation logic

### DON'T: Ignore Security
- Never hardcode credentials or API keys
- Don't expose sensitive information in logs or error messages
- Avoid using deprecated or vulnerable libraries
- Don't trust user input without validation

### DON'T: Skip Testing
- Don't deploy code without testing
- Avoid writing tests that don't actually test functionality
- Don't ignore failing tests
- Don't skip edge case testing

### DON'T: Create Technical Debt
- Avoid "quick fixes" that compromise code quality
- Don't leave commented-out code in production
- Avoid magic numbers and strings (use constants)
- Don't ignore code smells and refactoring opportunities

### DON'T: Violate Standards
- Don't mix coding styles in the same project
- Avoid inconsistent naming conventions
- Don't ignore linting warnings
- Avoid non-standard project structures

## Architecture Do's

### DO: Design for Maintainability
- Use modular architecture with clear separation of concerns
- Implement proper abstraction layers
- Follow SOLID principles
- Design for extensibility

### DO: Document Architecture
- Maintain up-to-date architecture diagrams
- Document design decisions and rationale
- Provide clear API documentation
- Include setup and deployment instructions

## Architecture Don'ts

### DON'T: Create Tight Coupling
- Avoid direct dependencies between unrelated modules
- Don't create god objects or classes
- Avoid global state when possible
- Don't bypass abstraction layers

### DON'T: Over-Engineer
- Avoid premature optimization
- Don't add features that aren't required
- Avoid unnecessary complexity
- Don't use design patterns inappropriately

## Example Violations

### Bad Example (Multiple Don'ts violated):
```python
# Hardcoded credentials (Security Don't)
db_password = "admin123"

# Function too long, no error handling (Quality Don'ts)
def process_user_data(data):
    # 100+ lines of code
    # No try-catch
    # No input validation
    result = execute_query(f"SELECT * FROM users WHERE id = {data['id']}")  # SQL injection risk
    return result
```

### Good Example (Following Do's):
```python
import os
from typing import Dict, Optional

# Secure credential management (Security Do)
DB_PASSWORD = os.getenv('DB_PASSWORD')

# Clear function name, proper error handling (Quality Do's)
def get_user_by_id(user_id: int) -> Optional[Dict]:
    """
    Retrieve user data by ID with proper validation and error handling.
    
    Args:
        user_id: The unique identifier for the user
        
    Returns:
        User data dictionary or None if not found
        
    Raises:
        ValueError: If user_id is invalid
    """
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Invalid user ID")
    
    try:
        # Parameterized query (Security Do)
        result = execute_query(
            "SELECT * FROM users WHERE id = ?", 
            (user_id,)
        )
        return result
    except DatabaseError as e:
        logger.error(f"Database error retrieving user {user_id}: {e}")
        return None
```

## Compliance Checklist

- [ ] All user inputs are validated and sanitized
- [ ] No hardcoded credentials or sensitive data
- [ ] Error handling implemented for all critical operations
- [ ] Functions are small and focused (< 50 lines)
- [ ] Code follows consistent naming conventions
- [ ] Security best practices followed
- [ ] No deeply nested conditionals (max 3 levels)
- [ ] Dependencies are up to date
- [ ] Code is properly documented
- [ ] Tests cover critical functionality
