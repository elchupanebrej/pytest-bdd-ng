# Quickstart Guide: Architecture Documentation

## Getting Started

To work with the architecture documentation for pytest-bdd:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-org/pytest-bdd.git
   cd pytest-bdd
   ```

2. **Install documentation dependencies**:
   ```bash
   pip install -r docs/requirements.txt
   # Ensure sphinxcontrib-mermaid is installed
   pip install sphinxcontrib-mermaid
   ```

3. **Build the documentation**:
   ```bash
   cd docs
   make html
   ```

4. **View the architecture documentation**:
   Open `_build/html/architecture/index.html` in your web browser to see the architecture documentation set.

## Architecture Documentation Location

All architecture documents are located in:
- `docs/architecture/` - Contains all architecture documentation files
- Each file follows the naming pattern: `architecture-[aspect].md`
- Example: `architecture-project-structure.md`, `architecture-data-flow.md`

## Documentation Structure

The architecture documentation set includes:
- **Index page**: Overview of the documentation set and how to navigate it
- **Aspect-specific documents**: Each focusing on a distinct architectural viewpoint
- **Cross-references**: Links between related aspects for deeper understanding
- **Mermaid diagrams**: Visual representations embedded in each document

## Contributing

When adding or updating architecture documentation:

1. **Create/update files** in `docs/architecture/` following the naming convention
2. **Include at least one Mermaid diagram** per document using proper Mermaid syntax
3. **Add explanatory text** describing what the diagram represents
4. **Ensure technical accuracy** by validating against the actual implementation
5. **Update the index** if adding new major aspects
6. **Test the build** to ensure diagrams render correctly

## Diagram Guidelines

- Use appropriate Mermaid diagram types for the architectural aspect:
  - `flowchart` for component relationships and processes
  - `sequence` for data flows and execution paths
  - `class` for structural relationships (when appropriate)
  - `state` for lifecycle behaviors
- Keep diagrams focused on architectural concepts, not implementation details
- Include clear labels and explanations
- Validate that diagrams accurately represent the current system state
