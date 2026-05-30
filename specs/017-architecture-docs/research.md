# Research Findings: Architecture Documentation with Mermaid Diagrams

## Decision: Initial Architectural Aspects to Document

**Decision**: Focus on three core architectural aspects for initial documentation:
1. High-level project structure and component relationships
2. Data flow and execution paths for primary use cases
3. Plugin architecture and extension points

**Rationale**: These aspects provide the most value for the identified user stories:
- New developers need to understand overall structure first
- Maintenance developers benefit from seeing data flows when assessing change impacts
- Technical architects make decisions about evolution based on understanding plugin systems

**Alternatives Considered**:
- Documenting every internal module (rejected: too granular, overwhelming)
- Focusing only on runtime behavior (rejected: misses structural understanding)
- Starting with detailed class diagrams (rejected: too technical for initial audience)

## Decision: Documentation Location

**Decision**: Place architecture documents in `docs/architecture/` directory with individual Markdown files

**Rationale**:
- Follows existing documentation organization patterns in the project
- Keeps related documentation together
- Easy to discover for users browsing the documentation
- Compatible with existing Sphinx build system

**Alternatives Considered**:
- Adding to existing feature documentation (rejected: mixes conceptual and procedural docs)
- Creating a top-level ARCHITECTURE directory (rejected: inconsistent with current structure)
- Using wiki or external documentation system (rejected: reduces discoverability and version coupling)

## Decision: Diagram Detail Level

**Decision**: Use appropriate detail level for each diagram type:
- Component diagrams: Show major subsystems and their interfaces (not individual classes)
- Flow diagrams: Show key steps in primary use cases (not every function call)
- Plugin diagrams: Show extension points and lifecycles (not internal implementation)

**Rationale**:
- Matches the audience needs (architects, developers, maintainers)
- Provides value without overwhelming detail
- Stays focused on architectural concepts rather than implementation details
- Aligns with success criteria of comprehension in ≤2 hours

**Alternatives Considered**:
- Maximum detail showing all classes/methods (rejected: too verbose, loses architectural signal)
- Minimal detail with only boxes and labels (rejected: insufficient for understanding interactions)
- Varying detail per audience (rejected: creates inconsistency and maintenance burden)

## Decision: Mermaid Integration with Documentation Build

**Decision**: Use sphinxcontrib-mermaid extension to enable Mermaid diagram support in Sphinx builds

**Rationale**:
- Well-maintained extension specifically for Mermaid in Sphinx
- Compatible with existing RST-based documentation
- Supports all Mermaid diagram types needed
- Active community and good documentation

**Alternatives Considered**:
- Raw HTML embedding (rejected: fragile, breaks with theme changes)
- Pre-rendered SVGs (rejected: hard to maintain, version control issues)
- Custom Sphinx directive (rejected: reinventing existing solution)
- JavaScript-only client-side rendering (rejected: doesn't work in static HTML output)

## Decision: Organizational Pattern for Documentation Set

**Decision**: Use a structured approach with:
1. Index page explaining the architecture documentation set
2. Individual aspect documents following a consistent template
3. Cross-linking between related aspects
4. Clear naming convention: `architecture-[aspect].md`

**Rationale**:
- Provides navigational structure for users
- Maintains consistency across documents
- Enables incremental learning
- Scales well as more aspects are added

**Alternatives Considered**:
- Single large document (rejected: violates FR-001, hard to navigate)
- Wiki-style unstructured linking (rejected: difficult to maintain coherence)
- Tutorial-style progression (rejected: doesn't support reference use cases)
