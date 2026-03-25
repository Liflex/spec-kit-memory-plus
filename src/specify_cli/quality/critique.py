"""
Critique

Generates targeted feedback for failed rules.
"""

from typing import List, Dict, Union
from specify_cli.quality.models import FailedRule, CritiqueResult


class Critique:
    """Generate critique for failed rules"""

    # Rule-specific fix instructions
    FIX_INSTRUCTIONS = {
        # API Spec rules
        "correctness.endpoints": (
            "Add the missing CRUD endpoint:\n"
            "1. Identify the missing operation (GET, POST, PUT, DELETE)\n"
            "2. Create the endpoint function\n"
            "3. Add proper routing and documentation"
        ),
        "correctness.status_codes": (
            "Add missing HTTP status codes:\n"
            "1. Include 200 for successful operations\n"
            "2. Include 201 for resource creation\n"
            "3. Include 400 for client errors\n"
            "4. Include 404 for not found\n"
            "5. Include 500 for server errors"
        ),
        "correctness.content_types": (
            "Specify Content-Type headers:\n"
            "1. Add 'Content-Type: application/json' for JSON responses\n"
            "2. Add 'Content-Type: text/html' for HTML responses"
        ),
        "correctness.auth": (
            "Document authentication requirements:\n"
            "1. Specify auth method (Bearer token, API key, OAuth)\n"
            "2. Show example Authorization header\n"
            "3. Document how to obtain credentials"
        ),
        "quality.parameters": (
            "Document request parameters:\n"
            "1. List all query parameters\n"
            "2. List all path parameters\n"
            "3. List all body fields with types"
        ),
        "quality.responses": (
            "Document response schemas:\n"
            "1. Define response body structure\n"
            "2. Specify field types and constraints\n"
            "3. Include example responses"
        ),

        # Code Gen rules
        "correctness.tests": (
            "Add unit tests:\n"
            "1. Create test file in tests/\n"
            "2. Write test cases for each function\n"
            "3. Mock external dependencies\n"
            "4. Cover success and failure cases"
        ),
        "quality.error_handling": (
            "Improve error handling:\n"
            "1. Wrap risky operations in try/except\n"
            "2. Validate inputs before processing\n"
            "3. Return meaningful error messages\n"
            "4. Log errors for debugging"
        ),
        "quality.readability": (
            "Improve code readability:\n"
            "1. Add comments explaining complex logic\n"
            "2. Add docstrings to functions/classes\n"
            "3. Use descriptive variable names\n"
            "4. Break up long functions"
        ),
        "correctness.type_hints": (
            "Add type hints:\n"
            "1. Add type annotations to function parameters\n"
            "2. Add return type annotations\n"
            "3. Use typing module for complex types"
        ),
        "correctness.structure": (
            "Improve code structure:\n"
            "1. Group related code into classes/modules\n"
            "2. Separate concerns (models, services, handlers)\n"
            "3. Follow project structure conventions"
        ),
        "security.input_validation": (
            "Add input validation:\n"
            "1. Validate parameter types and ranges\n"
            "2. Sanitize user input\n"
            "3. Check for required fields\n"
            "4. Handle edge cases"
        ),
        "security.secrets": (
            "Remove hardcoded secrets:\n"
            "1. Move secrets to environment variables\n"
            "2. Use config files (gitignored)\n"
            "3. Use secret management service\n"
            "4. Document required environment variables"
        ),
        "performance.complexity": (
            "Reduce code complexity:\n"
            "1. Extract helper methods for nested logic\n"
            "2. Use early returns to reduce nesting\n"
            "3. Consider using design patterns"
        ),
        "quality.logging": (
            "Add logging:\n"
            "1. Add log statements for key operations\n"
            "2. Use appropriate log levels (INFO, ERROR, DEBUG)\n"
            "3. Include contextual information"
        ),
        "correctness.imports": (
            "Clean up imports:\n"
            "1. Remove unused imports\n"
            "2. Group standard library imports\n"
            "3. Group third-party imports\n"
            "4. Follow import organization conventions"
        ),
        "performance.caching": (
            "Add caching for expensive operations:\n"
            "1. Identify slow/repeated operations\n"
            "2. Add caching decorator (e.g., @lru_cache)\n"
            "3. Set appropriate cache size/ttl"
        ),

        # Security rules (security.yml template)
        "security.no_hardcoded_secrets": (
            "Remove hardcoded secrets:\n"
            "1. Move passwords, API keys, tokens to environment variables\n"
            "2. Use a secret manager (Vault, AWS Secrets Manager)\n"
            "3. Add .env to .gitignore\n"
            "4. Rotate any secrets that were committed"
        ),
        "security.sql_injection_prevention": (
            "Prevent SQL injection:\n"
            "1. Use parameterized queries or prepared statements\n"
            "2. Use ORM (SQLAlchemy, Prisma, etc.) instead of raw SQL\n"
            "3. Never concatenate user input into SQL strings\n"
            "4. Apply input validation on all user-supplied values"
        ),
        "security.xss_prevention": (
            "Prevent Cross-Site Scripting (XSS):\n"
            "1. Escape/encode all user-generated output\n"
            "2. Use Content Security Policy (CSP) headers\n"
            "3. Avoid innerHTML; use textContent or safe rendering\n"
            "4. Use a template engine with auto-escaping"
        ),
        "security.authentication": (
            "Implement authentication:\n"
            "1. Add auth middleware/guard on protected endpoints\n"
            "2. Verify tokens/sessions on each request\n"
            "3. Use bcrypt/argon2 for password hashing\n"
            "4. Implement secure login/logout flows"
        ),
        "security.authorization": (
            "Implement authorization checks:\n"
            "1. Verify user permissions before resource access\n"
            "2. Use role-based (RBAC) or attribute-based (ABAC) access control\n"
            "3. Check ownership for user-specific resources\n"
            "4. Return 403 Forbidden for unauthorized access"
        ),
        "security.https_only": (
            "Enforce HTTPS:\n"
            "1. Add HTTP-to-HTTPS redirect\n"
            "2. Set HSTS header (Strict-Transport-Security)\n"
            "3. Mark cookies as Secure\n"
            "4. Use TLS 1.2+ for all connections"
        ),
        "security.csrf_protection": (
            "Add CSRF protection:\n"
            "1. Generate and validate CSRF tokens on forms\n"
            "2. Set SameSite attribute on cookies (Lax or Strict)\n"
            "3. Verify Origin/Referer headers on state-changing requests\n"
            "4. Use framework CSRF middleware (e.g., csurf, Django CSRF)"
        ),
        "security.error_handling": (
            "Implement secure error handling:\n"
            "1. Return generic error messages to clients\n"
            "2. Never expose stack traces in production\n"
            "3. Log detailed errors server-side only\n"
            "4. Use different error detail levels for dev vs prod"
        ),
        "security.dependencies": (
            "Audit and update dependencies:\n"
            "1. Run npm audit / pip-audit / safety check\n"
            "2. Update packages with known vulnerabilities\n"
            "3. Pin dependency versions in lock files\n"
            "4. Set up automated dependency scanning (Dependabot, Snyk)"
        ),
        "security.cors_configuration": (
            "Configure CORS properly:\n"
            "1. Restrict allowed origins (no wildcard * in production)\n"
            "2. Specify allowed methods and headers explicitly\n"
            "3. Handle credentials correctly (Access-Control-Allow-Credentials)\n"
            "4. Use CORS middleware with strict configuration"
        ),
        "security.csp_headers": (
            "Add Content Security Policy headers:\n"
            "1. Set default-src 'self' as baseline\n"
            "2. Restrict script-src to trusted sources\n"
            "3. Disable unsafe-inline and unsafe-eval where possible\n"
            "4. Use nonce or hash for inline scripts if needed"
        ),
        "security.rate_limiting": (
            "Implement rate limiting:\n"
            "1. Add rate limiter middleware (express-rate-limit, slowapi)\n"
            "2. Set per-IP or per-user request limits\n"
            "3. Return 429 Too Many Requests with Retry-After header\n"
            "4. Apply stricter limits on auth endpoints"
        ),
        "security.jwt_token_handling": (
            "Handle JWT tokens securely:\n"
            "1. Validate signature and expiration on every request\n"
            "2. Store tokens in httpOnly cookies (not localStorage)\n"
            "3. Set short expiration times with refresh token rotation\n"
            "4. Never include sensitive data in JWT payload"
        ),
        "security.api_key_management": (
            "Manage API keys securely:\n"
            "1. Scope keys with minimal required permissions\n"
            "2. Implement key rotation policy\n"
            "3. Store keys in environment variables or secret manager\n"
            "4. Never commit keys to source control"
        ),
        "security.env_variable_usage": (
            "Use environment variables for configuration:\n"
            "1. Load secrets from env vars or secret manager\n"
            "2. Never set default values for secrets in code\n"
            "3. Add .env files to .gitignore\n"
            "4. Document required env vars in README or .env.example"
        ),
        "security.secret_rotation": (
            "Implement secret rotation:\n"
            "1. Document rotation schedule for keys and certificates\n"
            "2. Automate rotation where possible (AWS Secrets Manager)\n"
            "3. Monitor certificate expiration dates\n"
            "4. Support graceful key rollover (accept old + new during transition)"
        ),

        # GraphQL security rules (Exp 23)
        "security.graphql_query_depth_limiting": (
            "Limit GraphQL query depth:\n"
            "1. Install depth-limiting middleware (graphql-depth-limit, etc.)\n"
            "2. Set max depth to 5-7 levels based on schema complexity\n"
            "3. Return clear error message when depth exceeded\n"
            "4. Log depth limit violations for monitoring"
        ),
        "security.graphql_query_complexity_analysis": (
            "Add query complexity analysis:\n"
            "1. Assign cost values to fields based on data fetching impact\n"
            "2. Set maximum complexity limit per query (e.g., 1000)\n"
            "3. Use complexity analysis library (graphql-validation-complexity)\n"
            "4. Return complexity score in query response extensions"
        ),
        "security.graphql_introspection_disabled": (
            "Disable introspection in production:\n"
            "1. Check NODE_ENV/environment before enabling introspection\n"
            "2. Set introspection: false in production server config\n"
            "3. Use plugin to conditionally disable __schema queries\n"
            "4. Keep introspection enabled in development/staging only"
        ),
        "security.graphql_rate_limiting": (
            "Implement complexity-based rate limiting:\n"
            "1. Calculate query cost based on field complexity weights\n"
            "2. Set per-user/per-IP cost budget per time window\n"
            "3. Track cumulative query cost, not just request count\n"
            "4. Return 429 with cost details when budget exceeded"
        ),
        "security.graphql_batch_query_limiting": (
            "Limit batch query operations:\n"
            "1. Set maximum operations per batch request (5-10)\n"
            "2. Validate array length before processing batch\n"
            "3. Apply per-operation cost analysis within batch\n"
            "4. Return clear error when batch limit exceeded"
        ),
        "security.graphql_persisted_queries": (
            "Enable persisted queries:\n"
            "1. Implement APQ (Automatic Persisted Queries) with SHA256 hashing\n"
            "2. Use query allowlist in production for trusted queries only\n"
            "3. Register queries at build time or via admin API\n"
            "4. Reject unknown query documents in production mode"
        ),
        "security.graphql_field_authorization": (
            "Add field-level authorization:\n"
            "1. Use auth directives (@auth, @hasRole) on sensitive fields\n"
            "2. Implement graphql-shield or similar for field-level rules\n"
            "3. Check permissions in resolver, not just at endpoint level\n"
            "4. Return null or error for unauthorized field access"
        ),
        "security.graphql_mutation_idempotency": (
            "Support mutation idempotency:\n"
            "1. Accept clientMutationId or Idempotency-Key in mutations\n"
            "2. Store mutation results keyed by idempotency token\n"
            "3. Return cached result for duplicate mutation requests\n"
            "4. Set TTL for idempotency records (e.g., 24 hours)"
        ),

        # Testing rules (testing.yml template, Exp 30)
        "correctness.test_structure": (
            "Follow Arrange-Act-Assert test structure:\n"
            "1. Arrange: set up test data and dependencies\n"
            "2. Act: execute the operation under test\n"
            "3. Assert: verify expected outcomes\n"
            "4. Use describe/it blocks for clear test organization"
        ),
        "correctness.assertions": (
            "Add meaningful assertions:\n"
            "1. Use specific assertions (assertEqual, toBe) not generic assert True\n"
            "2. Add descriptive messages to assertions\n"
            "3. Assert on specific values, not just truthiness\n"
            "4. One logical assertion per test (or closely related group)"
        ),
        "quality.test_isolation": (
            "Ensure test isolation:\n"
            "1. Use setUp/tearDown or beforeEach/afterEach for shared setup\n"
            "2. Use fixtures (@pytest.fixture) for reusable test data\n"
            "3. Mock external dependencies (DB, API, filesystem)\n"
            "4. Each test must pass independently of execution order"
        ),
        "correctness.edge_cases": (
            "Add edge case tests:\n"
            "1. Test null/None/undefined inputs\n"
            "2. Test empty strings, empty arrays, zero values\n"
            "3. Test boundary conditions (min, max, overflow)\n"
            "4. Test invalid/malformed inputs"
        ),
        "quality.mocks_usage": (
            "Use mocks correctly:\n"
            "1. Mock external dependencies, not code under test\n"
            "2. Use unittest.mock.patch or jest.mock for module mocking\n"
            "3. Verify mock interactions (assert_called_with, toHaveBeenCalledWith)\n"
            "4. Reset mocks between tests to prevent leakage"
        ),
        "correctness.error_tests": (
            "Test error handling:\n"
            "1. Use pytest.raises() or assertRaises() for expected exceptions\n"
            "2. Test error messages and error types\n"
            "3. Test failure paths, not just happy paths\n"
            "4. Verify error recovery behavior"
        ),
        "quality.coverage": (
            "Improve test coverage:\n"
            "1. Configure coverage tool (pytest-cov, istanbul/nyc)\n"
            "2. Set minimum coverage threshold (80%+)\n"
            "3. Cover branches, not just lines\n"
            "4. Focus on critical paths and business logic"
        ),
        "testing.e2e_coverage": (
            "Add E2E tests for critical user journeys:\n"
            "1. Use Playwright, Cypress, or Puppeteer\n"
            "2. Test login, purchase, form submission flows\n"
            "3. Use data-testid selectors for stability\n"
            "4. Run E2E tests in CI pipeline"
        ),
        "testing.component_testing": (
            "Add component unit tests:\n"
            "1. Use @testing-library/react (or framework equivalent)\n"
            "2. Use user-centric queries (getByRole, getByLabelText)\n"
            "3. Test component rendering and user interactions\n"
            "4. Avoid testing implementation details"
        ),

        # Frontend rules (frontend.yml template)
        "correctness.components": (
            "Use component-based architecture:\n"
            "1. Export components as named or default exports\n"
            "2. One component per file (single responsibility)\n"
            "3. Use functional components with hooks\n"
            "4. Keep components focused and composable"
        ),
        "correctness.state_management": (
            "Implement proper state management:\n"
            "1. Use useState for local component state\n"
            "2. Use useReducer for complex state logic\n"
            "3. Avoid direct state mutations (use immutable updates)\n"
            "4. Lift state up when shared between components"
        ),
        "quality.props_validation": (
            "Add props validation:\n"
            "1. Define TypeScript interfaces for component props\n"
            "2. Or use PropTypes for runtime validation\n"
            "3. Mark required vs optional props\n"
            "4. Provide default values for optional props"
        ),
        "correctness.routing": (
            "Configure routing properly:\n"
            "1. Define route structure with React Router or framework router\n"
            "2. Add 404/not-found route handler\n"
            "3. Use lazy loading for route components\n"
            "4. Implement route guards for protected pages"
        ),
        "quality.responsive": (
            "Add responsive design:\n"
            "1. Use CSS media queries for breakpoints\n"
            "2. Use responsive utility classes (Tailwind, Bootstrap)\n"
            "3. Test on mobile, tablet, and desktop viewports\n"
            "4. Use relative units (rem, %, vw) instead of fixed px"
        ),
        "accessibility.alt_text": (
            "Add alt text for images:\n"
            "1. Add descriptive alt attributes to all <img> tags\n"
            "2. Use empty alt='' for decorative images\n"
            "3. Describe image content, not filename\n"
            "4. Keep alt text concise but meaningful"
        ),
        "performance.lazy_loading": (
            "Implement lazy loading:\n"
            "1. Use React.lazy() for route-level code splitting\n"
            "2. Add dynamic import() for heavy components\n"
            "3. Wrap lazy components in <Suspense> with fallback\n"
            "4. Lazy load images below the fold"
        ),
        "quality.semantic_html": (
            "Use semantic HTML elements:\n"
            "1. Use <header>, <nav>, <main>, <footer> for page structure\n"
            "2. Use <section>, <article>, <aside> for content grouping\n"
            "3. Use <button> for actions, <a> for navigation\n"
            "4. Avoid excessive <div> nesting (div soup)"
        ),
        "quality.css_organization": (
            "Organize CSS properly:\n"
            "1. Use CSS Modules or styled-components for scoping\n"
            "2. Avoid global style pollution\n"
            "3. Follow consistent naming convention (BEM, utility-first)\n"
            "4. Co-locate styles with components"
        ),
        "performance.react_hooks_optimization": (
            "Optimize React hooks usage:\n"
            "1. Use useMemo for expensive computations\n"
            "2. Use useCallback for event handlers passed as props\n"
            "3. Add correct dependency arrays to useEffect\n"
            "4. Avoid creating objects/arrays in render"
        ),
        "correctness.error_boundaries": (
            "Add error boundaries:\n"
            "1. Create ErrorBoundary component with componentDidCatch\n"
            "2. Wrap route-level and critical components\n"
            "3. Show user-friendly error UI with retry option\n"
            "4. Log errors to monitoring service"
        ),
        "quality.component_composition": (
            "Use component composition:\n"
            "1. Prefer composition over inheritance\n"
            "2. Use children prop for flexible content injection\n"
            "3. Use render props or hooks for shared logic\n"
            "4. Create reusable compound components"
        ),
        "quality.api_integration": (
            "Implement proper API integration:\n"
            "1. Handle loading, error, and success states\n"
            "2. Use React Query, SWR, or RTK Query for data fetching\n"
            "3. Add error boundaries for failed API calls\n"
            "4. Implement retry logic for transient failures"
        ),
        "quality.form_validation": (
            "Add client-side form validation:\n"
            "1. Use controlled inputs with onChange handlers\n"
            "2. Validate on blur and on submit\n"
            "3. Show inline error messages near fields\n"
            "4. Use validation library (Zod, Yup, react-hook-form)"
        ),
        "quality.environment_config": (
            "Use environment-based configuration:\n"
            "1. Store API URLs in environment variables\n"
            "2. Use .env files with REACT_APP_ or VITE_ prefix\n"
            "3. Never hardcode secrets in frontend code\n"
            "4. Add .env.example with placeholder values"
        ),
        "quality.state_persistence": (
            "Implement state persistence properly:\n"
            "1. Wrap localStorage/sessionStorage in try/catch\n"
            "2. Handle storage quota exceeded errors\n"
            "3. Validate stored data before use (schema check)\n"
            "4. Provide fallback defaults when storage is unavailable"
        ),

        # Docs rules
        "correctness.title": (
            "Add document title:\n"
            "1. Add # Title at the top\n"
            "2. Make it descriptive and clear"
        ),
        "correctness.purpose": (
            "Add purpose/overview section:\n"
            "1. Add ## Overview or ## Introduction\n"
            "2. Explain what this documentation covers\n"
            "3. Mention target audience"
        ),
        "quality.installation": (
            "Add installation instructions:\n"
            "1. Add ## Installation section\n"
            "2. List prerequisites\n"
            "3. Provide step-by-step instructions"
        ),
        "quality.usage": (
            "Add usage examples:\n"
            "1. Add ## Usage section\n"
            "2. Include code examples in ``` blocks\n"
            "3. Show common use cases"
        ),
        "correctness.links": (
            "Add valid links:\n"
            "1. Use [text](url) format for links\n"
            "2. Include relevant external references\n"
            "3. Verify all links are accessible"
        ),
        "quality.structure": (
            "Improve heading hierarchy:\n"
            "1. Use # for main title\n"
            "2. Use ## for major sections\n"
            "3. Use ### for subsections\n"
            "4. Don't skip levels"
        ),
        "correctness.spelling": (
            "Fix spelling errors:\n"
            "1. Review for common typos\n"
            "2. Use spell checker\n"
            "3. Ask someone to review"
        ),
        "quality.code_blocks": (
            "Format code blocks:\n"
            "1. Use ```language for code\n"
            "2. Specify language (python, bash, etc.)\n"
            "3. Ensure code is syntactically correct"
        ),

        # Config rules
        "correctness.syntax": (
            "Fix file syntax:\n"
            "1. Validate YAML/JSON syntax\n"
            "2. Use linter/formatter\n"
            "3. Check for matching brackets/quotes"
        ),
        "correctness.required_fields": (
            "Add required fields:\n"
            "1. Check schema or documentation\n"
            "2. Add all required keys\n"
            "3. Use appropriate values"
        ),
        "correctness.field_types": (
            "Fix field value types:\n"
            "1. Check expected types for each field\n"
            "2. Convert strings to numbers/booleans as needed\n"
            "3. Use quotes for strings"
        ),
        "quality.comments": (
            "Add comments for complex settings:\n"
            "1. Explain non-obvious settings\n"
            "2. Add inline comments for tricky values\n"
            "3. Document any overrides"
        ),
        "correctness.paths": (
            "Fix file paths:\n"
            "1. Verify referenced files exist\n"
            "2. Use relative paths when possible\n"
            "3. Check path separators for OS"
        ),
        "quality.defaults": (
            "Add default values:\n"
            "1. Provide sensible defaults for optional fields\n"
            "2. Document what the default is\n"
            "3. Use production-safe defaults"
        ),
        "quality.environment_vars": (
            "Use environment variables:\n"
            "1. Replace hardcoded values with ${VAR}\n"
            "2. Add ${VAR:-default} for defaults\n"
            "3. Document required environment variables"
        ),

        # Backend template rules (backend.yml)
        "correctness.api_structure": (
            "Follow RESTful API structure:\n"
            "1. Map HTTP methods correctly (GET=read, POST=create, PUT=update, DELETE=remove)\n"
            "2. Use resource-based URLs (/users, /orders)\n"
            "3. Return appropriate status codes per method\n"
            "4. Separate route definitions from handler logic"
        ),
        "correctness.service_layer": (
            "Extract business logic to service layer:\n"
            "1. Create service classes for domain operations\n"
            "2. Move business logic out of controllers/routes\n"
            "3. Keep controllers thin (validate, delegate, respond)\n"
            "4. Inject repositories/dependencies into services"
        ),
        "correctness.dependency_injection": (
            "Use dependency injection:\n"
            "1. Accept dependencies via constructor parameters\n"
            "2. Use DI container (e.g., inversify, tsyringe, FastAPI Depends)\n"
            "3. Avoid direct instantiation of services inside other services\n"
            "4. Register dependencies in composition root"
        ),
        "quality.error_responses": (
            "Implement proper error responses:\n"
            "1. Return consistent error format: {error: {code, message, details}}\n"
            "2. Use appropriate HTTP status codes (400, 404, 422, 500)\n"
            "3. Include request_id for traceability\n"
            "4. Hide internal details in production"
        ),
        "correctness.validation": (
            "Add input validation:\n"
            "1. Validate all request parameters before processing\n"
            "2. Use schema validation (Zod, Joi, Pydantic, class-validator)\n"
            "3. Return 400/422 with field-level error details\n"
            "4. Sanitize inputs to prevent injection attacks"
        ),
        "performance.async_operations": (
            "Use async/await for I/O operations:\n"
            "1. Mark I/O-bound functions as async\n"
            "2. Use await for database queries, HTTP calls, file I/O\n"
            "3. Use asyncio.gather() or Promise.all() for parallel operations\n"
            "4. Avoid blocking calls in async context"
        ),
        "quality.http_status_codes": (
            "Use correct HTTP status codes:\n"
            "1. 200 OK for successful GET/PUT, 201 Created for POST\n"
            "2. 204 No Content for successful DELETE\n"
            "3. 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found\n"
            "4. 422 Unprocessable Entity for validation, 429 Too Many Requests"
        ),
        "correctness.content_negotiation": (
            "Implement content negotiation:\n"
            "1. Check Accept header to determine response format\n"
            "2. Set Content-Type header on all responses\n"
            "3. Support application/json as primary format\n"
            "4. Return 406 Not Acceptable for unsupported formats"
        ),
        "quality.resource_naming": (
            "Follow RESTful resource naming:\n"
            "1. Use plural nouns for collections (/users, /orders)\n"
            "2. Use kebab-case for multi-word URLs (/order-items)\n"
            "3. Limit nesting to 2-3 levels (/users/{id}/orders)\n"
            "4. Use query parameters for filtering, not nested paths"
        ),
        "quality.rate_limiting": (
            "Add rate limiting:\n"
            "1. Install rate limiting middleware (express-rate-limit, slowapi)\n"
            "2. Set per-IP or per-user request limits\n"
            "3. Apply stricter limits on auth and write endpoints\n"
            "4. Return 429 with Retry-After header when exceeded"
        ),
        "quality.cors_configuration": (
            "Configure CORS properly:\n"
            "1. Specify explicit allowed origins (avoid wildcard '*' in production)\n"
            "2. List allowed methods (GET, POST, PUT, DELETE)\n"
            "3. Set allowed headers explicitly\n"
            "4. Handle credentials with Access-Control-Allow-Credentials"
        ),
        "quality.security_headers": (
            "Add security headers:\n"
            "1. X-Content-Type-Options: nosniff\n"
            "2. X-Frame-Options: DENY or SAMEORIGIN\n"
            "3. Strict-Transport-Security for HTTPS\n"
            "4. Content-Security-Policy with restrictive defaults"
        ),
        "quality.domain_errors": (
            "Separate domain errors from validation errors:\n"
            "1. Use 400 for malformed requests, 422 for business rule violations\n"
            "2. Create domain-specific error classes (InsufficientFunds, NotFound)\n"
            "3. Map domain errors to HTTP status codes in error handler\n"
            "4. Include error code for machine-readable identification"
        ),
        "quality.error_consistency": (
            "Use consistent error response format:\n"
            "1. Define standard error schema: {error: {code, message, details}}\n"
            "2. Include request_id in every error response\n"
            "3. Use error middleware to catch and format all errors\n"
            "4. Document error codes in API docs"
        ),
        "security.stack_trace_sanitization": (
            "Hide stack traces in production:\n"
            "1. Check NODE_ENV/environment before including stack traces\n"
            "2. Return generic error message to clients in production\n"
            "3. Log full stack trace server-side only\n"
            "4. Use request_id to correlate client errors with server logs"
        ),
        "quality.api_versioning": (
            "Implement API versioning:\n"
            "1. Choose versioning strategy: URL path (/v1/), header, or query param\n"
            "2. Apply version prefix to all routes\n"
            "3. Document deprecation timeline for old versions\n"
            "4. Support at least one previous version during migration"
        ),
        "correctness.schema_validation": (
            "Add request/response schema validation:\n"
            "1. Define schemas with Zod, Joi, JSON Schema, or class-validator\n"
            "2. Validate request body, query params, and path params\n"
            "3. Validate response format in tests (contract testing)\n"
            "4. Auto-generate API docs from schemas (OpenAPI/Swagger)"
        ),
        "quality.idempotency": (
            "Implement idempotent operations:\n"
            "1. Ensure GET, PUT, DELETE are naturally idempotent\n"
            "2. Add Idempotency-Key header support for POST\n"
            "3. Store and return cached results for duplicate requests\n"
            "4. Set TTL for idempotency records (e.g., 24 hours)"
        ),

        # Backend GraphQL rules (backend.yml)
        "quality.graphql_n_plus1_prevention": (
            "Prevent GraphQL N+1 queries:\n"
            "1. Use DataLoader (JS) or dataloader (Python) for batching\n"
            "2. Batch related entity fetches per request\n"
            "3. Add DataLoader to request context for per-request caching\n"
            "4. Monitor query count per request to detect regressions"
        ),
        "quality.graphql_error_handling": (
            "Implement structured GraphQL errors:\n"
            "1. Include message, locations, path in all errors\n"
            "2. Add extensions.code for machine-readable error classification\n"
            "3. Mask internal errors (DB, stack traces) from client responses\n"
            "4. Use formatError hook to sanitize before sending"
        ),
        "quality.graphql_pagination": (
            "Add connection-based pagination:\n"
            "1. Implement Relay connection spec (edges, nodes, pageInfo)\n"
            "2. Support cursor-based pagination with first/after, last/before\n"
            "3. Include hasNextPage, hasPreviousPage in pageInfo\n"
            "4. Default to reasonable page size (10-25 items)"
        ),
        "quality.graphql_subscriptions_auth": (
            "Secure GraphQL subscriptions:\n"
            "1. Authenticate on WebSocket connection initialization\n"
            "2. Check authorization for each subscription field\n"
            "3. Validate token expiration during long-lived connections\n"
            "4. Close connection on auth failure with descriptive error"
        ),
        "quality.graphql_description_documentation": (
            "Document GraphQL schema:\n"
            "1. Add description to all types, fields, and arguments\n"
            "2. Mark deprecated fields with @deprecated(reason: '...')\n"
            "3. Document expected input formats in argument descriptions\n"
            "4. Use schema comments for internal documentation"
        ),
        "quality.graphql_federation_consistency": (
            "Ensure GraphQL Federation consistency:\n"
            "1. Add @key directives on all entity types\n"
            "2. Use @extends correctly for external types\n"
            "3. Implement __resolveReference for all entities\n"
            "4. Test cross-service entity resolution"
        ),
        # Database Phase B rules (Exp 41)
        "performance.denormalization": (
            "Apply denormalization for read-heavy queries:\n"
            "1. Identify slow queries with multiple JOINs\n"
            "2. Create materialized views for complex aggregations\n"
            "3. Add summary/cache tables for frequently accessed data\n"
            "4. Consider CQRS pattern for read/write separation"
        ),
        "quality.migrations": (
            "Ensure migrations are ordered and reversible:\n"
            "1. Add up()/down() or upgrade/downgrade methods\n"
            "2. Use migration framework (Alembic, Knex, Django migrations)\n"
            "3. Number/timestamp migrations for ordering\n"
            "4. Test rollback before deploying"
        ),
        "quality.constraints": (
            "Name and document constraints:\n"
            "1. Use descriptive constraint names (ck_users_age, chk_price_positive)\n"
            "2. Add CHECK constraints for business rules\n"
            "3. Document constraint purpose with comments\n"
            "4. Use domain constraints for reusable validation"
        ),
        "quality.transaction_boundaries": (
            "Define transaction boundaries properly:\n"
            "1. Wrap multi-step operations in BEGIN/COMMIT/ROLLBACK\n"
            "2. Use SAVEPOINT for partial rollback\n"
            "3. Add error handling with rollback on failure\n"
            "4. Use framework transaction support (@atomic, with session.begin())"
        ),
        "quality.query_isolation": (
            "Prevent N+1 query problem:\n"
            "1. Use JOINs instead of separate queries in loops\n"
            "2. Use eager loading (select_related, prefetch_related, includes)\n"
            "3. Use DataLoader for GraphQL batch resolution\n"
            "4. Monitor query count per request"
        ),
        "correctness.unique_constraints": (
            "Add UNIQUE constraints on business keys:\n"
            "1. Add UNIQUE on email, username, slug columns\n"
            "2. Use composite UNIQUE for multi-column uniqueness\n"
            "3. Handle duplicate key errors gracefully\n"
            "4. Consider partial unique indexes for conditional uniqueness"
        ),
        "security.sensitive_data": (
            "Protect sensitive data:\n"
            "1. Hash passwords with bcrypt/argon2 (never store plaintext)\n"
            "2. Encrypt PII at rest (AES-256, pgcrypto)\n"
            "3. Mask sensitive fields in query results\n"
            "4. Use column-level encryption for tokens and secrets"
        ),
        "quality.connection_pooling": (
            "Configure connection pooling:\n"
            "1. Set max_connections based on expected concurrency\n"
            "2. Configure idle_timeout to release unused connections\n"
            "3. Use PgBouncer or HikariCP for production pooling\n"
            "4. Monitor pool utilization and adjust limits"
        ),
        "quality.backup_strategy": (
            "Define backup and recovery strategy:\n"
            "1. Set up automated backups (pg_dump, mysqldump, WAL archiving)\n"
            "2. Define retention policy (daily, weekly, monthly)\n"
            "3. Test restore procedure regularly\n"
            "4. Document RPO/RTO targets"
        ),

        "performance.graphql_query_cost_analysis": (
            "Implement query cost analysis:\n"
            "1. Assign cost weights to fields based on data fetching impact\n"
            "2. Set maximum cost limit per query (e.g., 1000)\n"
            "3. Return cost in response extensions for client awareness\n"
            "4. Log high-cost queries for optimization opportunities"
        ),

        # Config Phase B rules (Exp 42)
        "quality.defaults": (
            "Add default values for optional fields:\n"
            "1. Use ${VAR:-default} syntax for env-based defaults\n"
            "2. Provide sensible defaults for optional settings\n"
            "3. Document what the default is and why\n"
            "4. Use production-safe defaults"
        ),
        "quality.environment_vars": (
            "Use environment variables for configuration:\n"
            "1. Reference env vars with ${VAR_NAME} syntax\n"
            "2. Use ${VAR:-default} for fallback values\n"
            "3. Use os.environ/process.env for programmatic access\n"
            "4. Document required env vars in .env.example"
        ),
        "correctness.value_ranges": (
            "Validate numeric values within ranges:\n"
            "1. Ensure port numbers are 1-65535\n"
            "2. Ensure timeouts are positive integers\n"
            "3. Ensure pool sizes and limits are reasonable\n"
            "4. Document min/max constraints for numeric fields"
        ),
        "correctness.enum_validation": (
            "Validate enum/choice fields:\n"
            "1. Use standard values for log_level (DEBUG, INFO, WARNING, ERROR)\n"
            "2. Use standard values for environment (development, staging, production)\n"
            "3. Define allowed values with choices/enum/Literal\n"
            "4. Validate at startup that config values match allowed choices"
        ),
        "quality.env_separation": (
            "Separate environment-specific configurations:\n"
            "1. Create config files per environment (config.dev.yml, config.prod.yml)\n"
            "2. Use .env.development, .env.production files\n"
            "3. Set NODE_ENV/FLASK_ENV/APP_ENV appropriately\n"
            "4. Never use production secrets in development config"
        ),
        "security.secret_references": (
            "Use secret manager references:\n"
            "1. Replace plaintext secrets with ${SECRET_NAME} references\n"
            "2. Use Vault, AWS Secrets Manager, or GCP Secret Manager\n"
            "3. Use !vault for Ansible, ssm:/ for AWS SSM\n"
            "4. Never store actual secret values in config files"
        ),
        "security.sensitive_fields": (
            "Protect sensitive configuration fields:\n"
            "1. Mark sensitive fields with sensitive: true (Terraform)\n"
            "2. Encrypt sensitive values with ENC[], KMS, or pgcrypto\n"
            "3. Redact sensitive values in logs and output\n"
            "4. Use environment variables for passwords, tokens, API keys"
        ),
        "performance.optimizations": (
            "Configure performance-related settings:\n"
            "1. Set appropriate timeout values for connections\n"
            "2. Configure connection pool sizes (max_connections, pool_size)\n"
            "3. Set cache TTL and buffer sizes\n"
            "4. Configure worker/thread counts for concurrency"
        ),
    }

    def __init__(self, max_issues: int = 5):
        """Initialize critique generator

        Args:
            max_issues: Maximum issues to generate (default: 5)
        """
        self.max_issues = max_issues

    def generate(
        self,
        failed_rules: Union[List[FailedRule], List[Dict]],
        artifact: str
    ) -> CritiqueResult:
        """Generate critique with fix instructions

        Args:
            failed_rules: List of FailedRule or dicts with rule_id, reason, category?, weight?
            artifact: Artifact content

        Returns:
            CritiqueResult with issues and fix instructions
        """
        # Normalize input: accept both FailedRule and dict (Exp 40)
        normalized = []
        for fr in failed_rules:
            if isinstance(fr, FailedRule):
                normalized.append(fr)
            else:
                normalized.append(FailedRule(
                    rule_id=fr["rule_id"],
                    reason=fr["reason"],
                    category=fr.get("category", "general"),
                    weight=fr.get("weight", 1),
                ))

        # Exp 37: Sort by weight (descending) so high-impact rules are addressed first
        sorted_rules = sorted(
            normalized,
            key=lambda r: r.weight,
            reverse=True,
        )

        # Limit to max_issues (now prioritized by weight)
        limited_rules = sorted_rules[:self.max_issues]

        issues = []
        for failed in limited_rules:
            fix_instruction = self._generate_fix_instruction(
                failed.rule_id, failed.reason, artifact
            )

            issues.append({
                "rule_id": failed.rule_id,
                "reason": failed.reason,
                "category": failed.category,
                "fix": fix_instruction,
            })

        return CritiqueResult(
            issues=issues,
            total_failed=len(failed_rules),
            addressed=len(limited_rules),
            skipped=len(failed_rules) - len(limited_rules),
        )

    def _generate_fix_instruction(
        self,
        rule_id: str,
        reason: str,
        artifact: str
    ) -> str:
        """Generate specific fix instruction for a rule

        Args:
            rule_id: Rule that failed
            reason: Why it failed
            artifact: Artifact content

        Returns:
            Fix instruction string
        """
        # Use rule-specific instruction if available
        if rule_id in self.FIX_INSTRUCTIONS:
            return self.FIX_INSTRUCTIONS[rule_id]

        # Generic fix instruction
        return (
            f"Fix issue: {reason}\n"
            f"1. Identify the problem area in the artifact\n"
            f"2. Apply the fix based on the rule: {rule_id}\n"
            f"3. Verify the change addresses the failed check"
        )
