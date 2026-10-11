"""Official message-driven Cucumber JUnit XML formatter adapter."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from pytest_cuke.compatibility.pytest import get_config_root_path
from pytest_cuke.cucumber_junit import configured_cucumber_junit_output_value
from pytest_cuke.formatter_api import FormatterRequest, FormatterSelection

if TYPE_CHECKING:
    from pytest_cuke.compatibility.pytest import Config


_JUNIT_ADAPTER = r"""
import { createInterface } from "node:readline";

import junitXmlFormatter from "@cucumber/junit-xml-formatter";

const input = createInterface({ input: process.stdin, crlfDelay: Infinity });
const messageHandlers = [];
const gherkinDocuments = [];
const picklesById = new Map();
const testCasesById = new Map();
const testCaseStarted = [];
const testCaseFinishedByStartedId = new Map();
let report = "";

function xmlAttribute(value) {
  return Array.from(String(value), (character) => {
    const codepoint = character.codePointAt(0);
    const isValid = codepoint === 0x9 || codepoint === 0xa || codepoint === 0xd
      || (codepoint >= 0x20 && codepoint <= 0xd7ff)
      || (codepoint >= 0xe000 && codepoint <= 0xfffd)
      || (codepoint >= 0x10000 && codepoint <= 0x10ffff);
    if (codepoint === undefined || !isValid) {
      return "\ufffd";
    }
    return character
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&apos;")
      .replaceAll("\n", "&#10;")
      .replaceAll("\r", "&#13;")
      .replaceAll("\t", "&#9;");
  }).join("");
}

function collectDocumentProperties(document, documentIndex) {
  const properties = [];
  const add = (name, value) => {
    properties.push(`<property name="${xmlAttribute(name)}" value="${xmlAttribute(value)}"/>`);
  };
  const encodeKeyPart = (value) => encodeURIComponent(String(value));
  const addTags = (prefix, tags) => {
    if (Array.isArray(tags) && tags.length) add(`${prefix}.tags`, JSON.stringify(tags.map((tag) => tag.name)));
  };
  const addSteps = (prefix, steps) => {
    for (const [index, step] of (steps ?? []).entries()) {
      const stepPrefix = `${prefix}.step.${index}`;
      if (typeof step.docString?.content === "string") add(`${stepPrefix}.docString`, step.docString.content);
      const rows = step.dataTable?.rows;
      if (Array.isArray(rows)) {
        add(`${stepPrefix}.dataTable`, JSON.stringify(rows.map((row) => row.cells.map((cell) => cell.value))));
      }
    }
  };
  const documentPrefix = `cucumber.${encodeKeyPart(document.uri ?? "unknown")}.document.${documentIndex}`;
  let scenarioIndex = 0;
  let ruleIndex = 0;
  const addScenario = (scenario) => {
    const index = scenarioIndex++;
    const kind = scenario.examples?.length ? "outline" : "scenario";
    const prefix = `${documentPrefix}.${kind}.${index}.${encodeKeyPart(scenario.name)}`;
    if (scenario.description) add(`${prefix}.description`, scenario.description);
    addTags(prefix, scenario.tags);
    addSteps(prefix, scenario.steps);
    for (const [index, examples] of (scenario.examples ?? []).entries()) {
      const examplesPrefix = `${prefix}.examples.${index}.${encodeKeyPart(examples.name)}`;
      addTags(examplesPrefix, examples.tags);
      const rows = [examples.tableHeader, ...(examples.tableBody ?? [])]
        .filter(Boolean)
        .map((row) => row.cells.map((cell) => cell.value));
      if (rows.length) add(`${examplesPrefix}.table`, JSON.stringify(rows));
    }
  };
  const addChildren = (children, prefix) => {
    for (const child of children ?? []) {
      if (child.rule) {
        const rule = child.rule;
        const rulePrefix = `${documentPrefix}.rule.${ruleIndex++}.${encodeKeyPart(rule.name)}`;
        if (rule.description) add(`${rulePrefix}.description`, rule.description);
        addTags(rulePrefix, rule.tags);
        addChildren(rule.children, rulePrefix);
      } else if (child.scenario) {
        addScenario(child.scenario);
      } else if (child.background) {
        addSteps(`${prefix}.background.${child.background.name}`, child.background.steps);
      }
    }
  };

  const feature = document.feature;
  if (!feature) return [];
  const featurePrefix = `${documentPrefix}.feature`;
  if (feature.description) add(`${featurePrefix}.description`, feature.description);
  addTags(featurePrefix, feature.tags);
  addChildren(feature.children, featurePrefix);
  if (properties.length) {
    properties.unshift(
      `<property name="${xmlAttribute(`${featurePrefix}.uri`)}" value="${xmlAttribute(document.uri ?? "")}"/>`,
    );
  }
  return properties;
}

function addDocumentProperties(xml) {
  const properties = gherkinDocuments
    .map((document, index) => collectDocumentProperties(document, index))
    .flat();
  if (!properties.length) return xml;
  const propertyLines = properties.map((property) => `    ${property}`).join("\n");
  const propertyBlock = `  <properties>\n${propertyLines}\n  </properties>\n`;
  const suiteMatch = /<testsuite(?=[\s>])/.exec(xml);
  if (!suiteMatch) throw new Error("Cucumber JUnit formatter emitted no testsuite element");
  const suiteStart = suiteMatch.index;
  const suiteStartEnd = xml.indexOf(">", suiteStart);
  if (suiteStartEnd < 0) throw new Error("Cucumber JUnit formatter emitted an incomplete testsuite element");
  const suiteOpening = xml.slice(suiteStart, suiteStartEnd + 1);
  if (suiteOpening.endsWith("/>")) {
    const opening = `${suiteOpening.slice(0, -2)}>`;
    return `${xml.slice(0, suiteStart)}${opening}\n${propertyBlock}</testsuite>`
      + xml.slice(suiteStartEnd + 1);
  }
  return `${xml.slice(0, suiteStartEnd + 1)}\n${propertyBlock}${xml.slice(suiteStartEnd + 1)}`;
}

function collectAstNodeLocations(node, locations) {
  if (Array.isArray(node)) {
    for (const child of node) collectAstNodeLocations(child, locations);
    return;
  }
  if (node === null || typeof node !== "object") return;
  if (typeof node.id === "string" && Number.isInteger(node.location?.line)) {
    locations.set(node.id, node.location);
  }
  for (const child of Object.values(node)) collectAstNodeLocations(child, locations);
}

function sourceLocationFor(pickle, locationsByUri) {
  const sourceUri = pickle.uri;
  if (typeof sourceUri !== "string") return undefined;
  const astNodeId = pickle.astNodeIds?.at(-1);
  const astLocation = locationsByUri.get(sourceUri)?.get(astNodeId);
  const line = pickle.location?.line ?? astLocation?.line;
  if (!Number.isInteger(line)) return undefined;
  return { uri: sourceUri, line };
}

function compareText(left, right) {
  if (left < right) return -1;
  if (left > right) return 1;
  return 0;
}

function orderedTestCaseSources() {
  const locationsByUri = new Map();
  for (const document of gherkinDocuments) {
    if (typeof document.uri !== "string") continue;
    let locations = locationsByUri.get(document.uri);
    if (!locations) {
      locations = new Map();
      locationsByUri.set(document.uri, locations);
    }
    collectAstNodeLocations(document, locations);
  }

  const started = testCaseStarted
    .filter((item) => !testCaseFinishedByStartedId.get(item.id)?.willBeRetried)
    .sort((left, right) => {
      const leftTime = left.timestamp.seconds * 1000 + left.timestamp.nanos / 1e6;
      const rightTime = right.timestamp.seconds * 1000 + right.timestamp.nanos / 1e6;
      return leftTime - rightTime || compareText(left.id, right.id);
    });

  const cases = started.map((item) => {
    const testCase = testCasesById.get(item.testCaseId);
    const pickle = picklesById.get(testCase?.pickleId);
    if (!pickle) return undefined;
    return { pickle, source: sourceLocationFor(pickle, locationsByUri) };
  });
  if (cases.some((item) => !item?.source)) return undefined;

  return cases
    .sort((left, right) => {
      const leftPickle = left.pickle;
      const rightPickle = right.pickle;
      if (leftPickle.uri !== rightPickle.uri) return leftPickle.uri.localeCompare(rightPickle.uri);
      if (!leftPickle.location) return rightPickle.location ? -1 : 0;
      if (!rightPickle.location) return 1;
      return leftPickle.location.line - rightPickle.location.line;
    })
    .map((item) => item.source);
}

function testcaseAttributes(tag) {
  return Object.fromEntries(
    [...tag.matchAll(/([A-Za-z_:][A-Za-z0-9_.:-]*)="([^"]*)"/g)]
      .map((match) => [match[1], match[2]]),
  );
}

function addDuplicateTestCaseSources(xml) {
  const tokenPattern = /<!\[CDATA\[[\s\S]*?\]\]>|<!--[\s\S]*?-->|<(?:[^>"']|"[^"]*"|'[^']*')*>/g;
  const tokens = [...xml.matchAll(tokenPattern)];
  const testcases = tokens.filter(({ 0: token }) => /^<testcase(?:\s|>)/.test(token));
  const identityCounts = new Map();
  for (const { 0: tag } of testcases) {
    const attributes = testcaseAttributes(tag);
    const identity = JSON.stringify([attributes.classname, attributes.name]);
    identityCounts.set(identity, (identityCounts.get(identity) ?? 0) + 1);
  }
  if (![...identityCounts.values()].some((count) => count > 1)) return xml;

  const sources = orderedTestCaseSources();
  if (!sources || sources.length !== testcases.length) {
    throw new Error("Cannot correlate duplicate Cucumber JUnit cases with source locations");
  }

  let testcaseIndex = 0;
  const replacements = new Map();
  for (const { 0: tag, index } of testcases) {
    const attributes = testcaseAttributes(tag);
    const identity = JSON.stringify([attributes.classname, attributes.name]);
    const source = sources[testcaseIndex++];
    if (identityCounts.get(identity) === 1) continue;
    const additions = [];
    if (attributes.file === undefined) additions.push(`file="${xmlAttribute(source.uri)}"`);
    if (attributes.line === undefined) additions.push(`line="${xmlAttribute(source.line)}"`);
    if (!additions.length) continue;
    const ending = tag.endsWith("/>") ? 2 : 1;
    replacements.set(index, `${tag.slice(0, -ending)} ${additions.join(" ")}${tag.slice(-ending)}`);
  }

  return xml.replace(tokenPattern, (tag, offset) => (
    replacements.get(offset) ?? tag
  ));
}

junitXmlFormatter.formatter({
  options: {},
  on: (type, handler) => {
    if (type !== "message") throw new Error(`Unsupported formatter event ${type}`);
    messageHandlers.push(handler);
  },
  write: (content) => {
    report += content;
  },
});

for await (const line of input) {
  if (!line.trim()) continue;
  const envelope = JSON.parse(line);
  if (envelope.gherkinDocument) gherkinDocuments.push(envelope.gherkinDocument);
  if (envelope.pickle) picklesById.set(envelope.pickle.id, envelope.pickle);
  if (envelope.testCase) testCasesById.set(envelope.testCase.id, envelope.testCase);
  if (envelope.testCaseStarted) testCaseStarted.push(envelope.testCaseStarted);
  if (envelope.testCaseFinished) {
    testCaseFinishedByStartedId.set(envelope.testCaseFinished.testCaseStartedId, envelope.testCaseFinished);
  }
  for (const handler of messageHandlers) handler(envelope);
}

process.stdout.write(addDuplicateTestCaseSources(addDocumentProperties(report)));
""".strip()


def _formatter_request(*, working_directory: Path, output_path: Path | None) -> FormatterRequest:
    return FormatterRequest(
        name="cucumber-junit",
        command=("node", "--input-type=module", "-e", _JUNIT_ADAPTER),
        output_path=output_path,
        working_directory=working_directory,
        required_executables=("node", "npm"),
        required_npm_packages=("@cucumber/junit-xml-formatter",),
        timeout_seconds=60.0,
    )


def selected_cucumber_junit_formatter_requests(config: Config) -> tuple[FormatterRequest, ...]:
    """Select the official message-driven JUnit XML formatter for a live pytest run."""
    output = configured_cucumber_junit_output_value(config)
    if output is None:
        return ()
    return (_formatter_request(working_directory=get_config_root_path(config), output_path=Path(output)),)


def replay_cucumber_junit_formatter_request(selection: FormatterSelection) -> FormatterRequest:
    """Build the formatter request used for standalone saved-stream conversion."""
    return _formatter_request(working_directory=selection.working_directory, output_path=selection.destination)


__all__ = ["replay_cucumber_junit_formatter_request", "selected_cucumber_junit_formatter_requests"]
