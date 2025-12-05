<!--
  ============================================================================
  SYNC IMPACT REPORT
  ============================================================================

  Version Change: [INITIAL] → 1.0.0

  Modified Principles:
  - N/A (initial constitution)

  Added Sections:
  - Core Principles (5 principles tailored for personal research project)
  - Development Workflow
  - Governance

  Removed Sections:
  - N/A (initial constitution)

  Templates Requiring Updates:
  - ✅ .specify/templates/plan-template.md (reviewed - compatible)
  - ✅ .specify/templates/spec-template.md (reviewed - compatible)
  - ✅ .specify/templates/tasks-template.md (reviewed - updated OPTIONAL test guidance)

  Follow-up TODOs:
  - None - all placeholders filled

  ============================================================================
-->

# pihole-textual Constitution

## Core Principles

### I. Rapid Prototyping

Speed-to-market over perfection. This is a personal research project focused on validating ideas quickly. Prioritise:
- Working features over comprehensive documentation
- Iterative development over upfront design
- Quick feedback loops over elaborate planning
- Practical validation over theoretical completeness

**Rationale**: Research projects need velocity to test hypotheses and pivot quickly based on learnings.

### II. Pragmatic Testing

Tests are OPTIONAL and should only be written where they add clear value. For this personal research project:
- Manual testing is acceptable for validating functionality
- Write tests for complex logic that's hard to verify manually
- Integration tests preferred over unit tests when testing is done
- Full test coverage is NOT required - focus on critical paths only
- User validation and observable behaviour matter more than test metrics

**Rationale**: Test overhead can slow research velocity. Tests should enable faster iteration, not hinder it.

### III. Simplicity First

Apply YAGNI (You Aren't Gonna Need It) rigorously:
- Build only what's needed for current requirements
- Avoid abstractions until patterns emerge from real usage
- Prefer straightforward solutions over flexible architectures
- Delete unused code immediately - no "just in case" features
- Complexity must be justified by present need, not future speculation

**Rationale**: Over-engineering is the enemy of research projects. Simple code is easier to modify as understanding evolves.

### IV. Textual-First Development

Leverage the Textual framework's patterns and conventions:
- Follow Textual's reactive programming model
- Use Textual's built-in widgets before creating custom ones
- Structure apps following Textual's composition patterns
- Leverage Textual's CSS system for styling
- Use Textual's message passing for component communication

**Rationale**: Working with the framework's grain reduces friction and accelerates development.

### V. Observable Behaviour

Focus on user-visible functionality:
- Prioritise features that provide immediate user value
- Make application state visible and debuggable
- Log significant operations for troubleshooting
- Provide clear feedback for user actions
- Internal implementation quality matters less than external usability

**Rationale**: For a TUI application, the user experience is paramount. Internal elegance is secondary to observable usefulness.

## Development Workflow

### Iteration Cycle

1. **Specify**: Define minimal user-facing behaviour required
2. **Prototype**: Implement quickly, focusing on "does it work?"
3. **Validate**: Manual testing or minimal automated tests
4. **Ship**: Commit working features immediately
5. **Reflect**: Assess learnings, decide next iteration

### Quality Gates

- Feature MUST be manually tested before commit
- Code MUST be readable by future self (basic clarity standard)
- Breaking changes SHOULD be noted in commit messages
- Tests are OPTIONAL - include only when they accelerate iteration

### Documentation

- README with basic setup and usage is sufficient
- Inline comments only where logic isn't self-evident
- User-facing features documented as needed for testing
- Architecture documentation is optional

## Governance

### Authority

This constitution defines the development philosophy for pihole-textual. All development decisions should align with these principles, prioritising speed and practicality over process and perfection.

### Amendments

- Constitution can be updated as project needs evolve
- Version bumps follow semantic versioning:
  - **MAJOR**: Fundamental philosophy change (e.g., adding mandatory TDD)
  - **MINOR**: New principle added or existing principle significantly expanded
  - **PATCH**: Clarifications, wording improvements, minor refinements
- Amendments should be documented with rationale

### Compliance

- Review features against principles, especially Simplicity First
- Challenge complexity: "Do we really need this now?"
- Question testing overhead: "Does this test help us move faster?"
- Validate against user needs: "Does this improve observable behaviour?"

### When to Break the Rules

Rules can be broken when there's a clear reason:
- Document the exception and why it's needed
- Assess if exception reveals a principle that needs updating
- Prefer amending constitution over accumulating exceptions

**Version**: 1.0.0 | **Ratified**: 2025-12-05 | **Last Amended**: 2025-12-05
