# Feature: Agentic debugging
  Debug MCP lets an agent discover a paused pytest-bdd failure, inspect BDD context, and write a structured investigation artifact before the test continues.

## Scenario: Enabled debug MCP session publishes discovery endpoints
* Given a debug MCP session on worker "gw0"
* When the worker announces debug MCP discovery
* Then the debug MCP root discovery lists worker "gw0"
* And worker "gw0" exposes mcp-pdb and sidecar endpoints

## Scenario Outline: Failed pytest phases are held independently
* Given a debug MCP session on worker "gw0"
* And a debug MCP session on worker "gw1"
* When worker "gw0" holds a "<phase>" failure
* And worker "gw1" announces debug MCP discovery
* Then worker "gw0" is holding a "<phase>" failure
* And worker "gw1" is waiting for a failure

## Examples:
    | phase    |
    | setup    |
    | call     |
    | teardown |

## Scenario: Investigation artifacts are written as JSON and Markdown
* Given a debug MCP session on worker "gw0"
* And worker "gw0" holds a "call" failure
* When the agent writes a valid investigation artifact
* Then the investigation artifact JSON is accepted
* And the investigation artifact Markdown is created

## Scenario: Invalid investigation artifacts are rejected
* Given a debug MCP session on worker "gw0"
* And worker "gw0" holds a "call" failure
* When the agent writes an invalid investigation artifact
* Then the investigation artifact is rejected

## Scenario: BDD metadata is included in investigation artifacts
* Given a debug MCP session on worker "gw0"
* And worker "gw0" holds a "call" failure with BDD metadata
* When the agent writes a valid investigation artifact
* Then the investigation artifact JSON contains BDD metadata

## Scenario: xdist root discovery references all worker sessions
* Given a debug MCP session on worker "gw0"
* And a debug MCP session on worker "gw1"
* When worker "gw0" announces debug MCP discovery
* And worker "gw1" announces debug MCP discovery
* Then the debug MCP root discovery lists worker "gw0"
* And the debug MCP root discovery lists worker "gw1"
