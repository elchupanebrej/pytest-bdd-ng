package main

// Markdown token matcher.
//
// The Gherkin-in-Markdown semantics live in Python (pytest_cuke.markdown_token_matcher),
// which the Python parser mode uses as its reference. gherkin/go ships no Markdown
// matcher, so this file ports those semantics as a decorator over the stock matcher:
// headings carry titles, bulleted lines carry steps, fenced blocks are docstrings, and
// GFM table separators are comments. Keep this file in step with the Python matcher;
// the parity corpus is the drift detector.

import (
	"regexp"
	"sort"
	"strings"
	"unicode/utf8"

	gherkin "github.com/cucumber/gherkin/go/v42"
)

const markdownDialectName = "en"

var (
	markdownHeaderPrefix = regexp.MustCompile(`^(#{1,6}\s)`)
	markdownBulletPrefix = regexp.MustCompile(`^(\s*[*+-]\s*)`)
	markdownTableRow     = regexp.MustCompile(`^\s\s\s?\s?\s?\|`)
	markdownTableSep     = regexp.MustCompile(`^:?-+:?$`)
	markdownTagPattern   = regexp.MustCompile("`(@[^`]+)`")
)

type markdownMatcher struct {
	base                     gherkin.Matcher
	dialect                  *gherkin.Dialect
	stepKeywords             []string
	matchedFeatureLine       bool
	activeDocStringSeparator string
	indentToRemove           int
}

func newMarkdownMatcher() gherkin.Matcher {
	dialect := gherkin.DialectsBuiltin().GetDialect(markdownDialectName)
	return &markdownMatcher{
		base:         gherkin.NewLanguageMatcher(gherkin.DialectsBuiltin(), markdownDialectName),
		dialect:      dialect,
		stepKeywords: markdownStepKeywords(dialect),
	}
}

// markdownStepKeywords keeps the Python matcher's ordering and drops the bare "* "
// keyword, which Markdown steps reach through the bullet prefix instead.
func markdownStepKeywords(dialect *gherkin.Dialect) []string {
	keywords := make([]string, 0, len(dialect.StepKeywords()))
	for _, keyword := range dialect.StepKeywords() {
		if keyword != "* " {
			keywords = append(keywords, keyword)
		}
	}
	sort.SliceStable(keywords, func(i, j int) bool {
		return len(keywords[i]) > len(keywords[j])
	})
	return keywords
}

func (m *markdownMatcher) Reset() {
	m.base.Reset()
	m.matchedFeatureLine = false
	m.activeDocStringSeparator = ""
	m.indentToRemove = 0
}

func (m *markdownMatcher) newToken(line *gherkin.Line, matchedIndent int) *gherkin.Token {
	return &gherkin.Token{
		GherkinDialect: markdownDialectName,
		Location:       &gherkin.Location{Line: line.LineNumber, Column: matchedIndent + 1},
	}
}

func (m *markdownMatcher) MatchFeatureLine(line *gherkin.Line) (bool, *gherkin.Token, error) {
	if m.matchedFeatureLine {
		return false, nil, nil
	}
	text := line.TrimmedLineText
	if !strings.HasPrefix(text, "# ") || strings.HasPrefix(text, "##") {
		return false, nil, nil
	}
	name := strings.TrimSpace(text[len("# "):])
	for _, keyword := range m.dialect.FeatureKeywords() {
		lowerName := strings.ToLower(name)
		lowerKeyword := strings.ToLower(keyword)
		if strings.HasPrefix(lowerName, lowerKeyword+":") {
			name = strings.TrimSpace(name[len(keyword)+1:])
			break
		}
		if strings.HasPrefix(lowerName, lowerKeyword) {
			name = strings.TrimSpace(name[len(keyword):])
			break
		}
	}
	token := m.newToken(line, line.Indent())
	token.Type = gherkin.TokenTypeFeatureLine
	token.Keyword = "Feature"
	token.Text = name
	m.matchedFeatureLine = true
	return true, token, nil
}

func (m *markdownMatcher) MatchRuleLine(line *gherkin.Line) (bool, *gherkin.Token, error) {
	return m.matchTitleLine(line, m.dialect.RuleKeywords(), gherkin.TokenTypeRuleLine)
}

func (m *markdownMatcher) MatchBackgroundLine(line *gherkin.Line) (bool, *gherkin.Token, error) {
	return m.matchTitleLine(line, m.dialect.BackgroundKeywords(), gherkin.TokenTypeBackgroundLine)
}

func (m *markdownMatcher) MatchScenarioLine(line *gherkin.Line) (bool, *gherkin.Token, error) {
	ok, token, err := m.matchTitleLine(line, m.dialect.ScenarioKeywords(), gherkin.TokenTypeScenarioLine)
	if ok || err != nil {
		return ok, token, err
	}
	return m.matchTitleLine(line, m.dialect.ScenarioOutlineKeywords(), gherkin.TokenTypeScenarioLine)
}

func (m *markdownMatcher) MatchExamplesLine(line *gherkin.Line) (bool, *gherkin.Token, error) {
	return m.matchTitleLine(line, m.dialect.ExamplesKeywords(), gherkin.TokenTypeExamplesLine)
}

func (m *markdownMatcher) MatchStepLine(line *gherkin.Line) (bool, *gherkin.Token, error) {
	return m.matchTitleLine(line, m.stepKeywords, gherkin.TokenTypeStepLine)
}

// matchTitleLine matches a title keyword after a Markdown heading or bullet prefix.
func (m *markdownMatcher) matchTitleLine(
	line *gherkin.Line,
	keywords []string,
	tokenType gherkin.TokenType,
) (bool, *gherkin.Token, error) {
	prefix := markdownHeaderPrefix
	suffix := gherkin.TitleKeywordSeparator
	if tokenType == gherkin.TokenTypeStepLine {
		prefix = markdownBulletPrefix
		suffix = ""
	}
	text := line.TrimmedLineText
	prefixEnd := prefix.FindStringIndex(text)
	if prefixEnd == nil {
		return false, nil, nil
	}
	rest := text[prefixEnd[1]:]
	for _, keyword := range keywords {
		if !strings.HasPrefix(rest, keyword+suffix) {
			continue
		}
		token := m.newToken(line, line.Indent()+prefixEnd[1])
		token.Type = tokenType
		token.Keyword = keyword
		token.Text = strings.TrimSpace(rest[len(keyword)+len(suffix):])
		if keywordType, isStep := m.dialect.KeywordTypes[keyword]; isStep {
			token.KeywordType = keywordType
		}
		return true, token, nil
	}
	return false, nil, nil
}

func (m *markdownMatcher) MatchTableRow(line *gherkin.Line) (bool, *gherkin.Token, error) {
	// Gherkin tables must be indented 2-5 spaces to be distinguishable from Markdown tables.
	if !markdownTableRow.MatchString(line.LineText) {
		return false, nil, nil
	}
	ok, token, err := m.base.MatchTableRow(line)
	if !ok || err != nil {
		return false, nil, err
	}
	if isGFMTableSeparator(token.Items) {
		return false, nil, nil
	}
	return true, token, nil
}

func (m *markdownMatcher) MatchComment(line *gherkin.Line) (bool, *gherkin.Token, error) {
	if !line.StartsWith("|") {
		return false, nil, nil
	}
	ok, baseToken, err := m.base.MatchTableRow(line)
	if err != nil {
		return false, nil, err
	}
	if !ok || !isGFMTableSeparator(baseToken.Items) {
		return false, nil, nil
	}
	token := m.newToken(line, line.Indent())
	token.Type = gherkin.TokenTypeComment
	token.Text = line.LineText
	return true, token, nil
}

func (m *markdownMatcher) MatchTagLine(line *gherkin.Line) (bool, *gherkin.Token, error) {
	text := line.TrimmedLineText
	matches := markdownTagPattern.FindAllStringSubmatchIndex(text, -1)
	if len(matches) == 0 {
		return false, nil, nil
	}
	token := m.newToken(line, line.Indent())
	token.Type = gherkin.TokenTypeTagLine
	for _, match := range matches {
		column := line.Indent() + utf8.RuneCountInString(text[:match[2]]) + 2
		token.Items = append(token.Items, &gherkin.LineSpan{Column: column, Text: text[match[2]:match[3]]})
	}
	return true, token, nil
}

func (m *markdownMatcher) MatchDocStringSeparator(line *gherkin.Line) (bool, *gherkin.Token, error) {
	if m.activeDocStringSeparator != "" {
		return m.matchDocStringSeparator(line, m.activeDocStringSeparator, false)
	}
	for _, separator := range []string{gherkin.DocstringSeparator, "````", gherkin.DocstringAlternativeSeparator} {
		ok, token, err := m.matchDocStringSeparator(line, separator, true)
		if ok || err != nil {
			return ok, token, err
		}
	}
	return false, nil, nil
}

func (m *markdownMatcher) matchDocStringSeparator(
	line *gherkin.Line,
	separator string,
	isOpen bool,
) (bool, *gherkin.Token, error) {
	if !line.StartsWith(separator) {
		return false, nil, nil
	}
	token := m.newToken(line, line.Indent())
	token.Type = gherkin.TokenTypeDocStringSeparator
	token.Keyword = separator
	if isOpen {
		token.Text = strings.TrimSpace(line.TrimmedLineText[len(separator):])
		m.activeDocStringSeparator = separator
		m.indentToRemove = line.Indent()
	} else {
		m.activeDocStringSeparator = ""
		m.indentToRemove = 0
	}
	return true, token, nil
}

func (m *markdownMatcher) MatchOther(line *gherkin.Line) (bool, *gherkin.Token, error) {
	token := m.newToken(line, 0)
	token.Type = gherkin.TokenTypeOther
	text := line.TrimmedLineText
	if m.indentToRemove >= 0 && m.indentToRemove <= line.Indent() {
		text = line.LineText[m.indentToRemove:]
	}
	token.Text = m.unescapeDocString(text)
	return true, token, nil
}

func (m *markdownMatcher) unescapeDocString(text string) string {
	if m.activeDocStringSeparator == gherkin.DocstringSeparator {
		return strings.ReplaceAll(text, `\"\"\"`, gherkin.DocstringSeparator)
	}
	if m.activeDocStringSeparator == gherkin.DocstringAlternativeSeparator {
		return strings.ReplaceAll(text, "\\`\\`\\`", gherkin.DocstringAlternativeSeparator)
	}
	return text
}

// MatchEmpty neuters any line that no other matcher claims, so Markdown prose is
// dropped instead of failing the parse.
func (m *markdownMatcher) MatchEmpty(line *gherkin.Line) (bool, *gherkin.Token, error) {
	result := line.IsEmpty()
	if !result {
		matched, err := m.matchesAnything(line)
		if err != nil {
			return false, nil, err
		}
		result = !matched
	}
	if !result {
		return false, nil, nil
	}
	token := m.newToken(line, 0)
	token.Type = gherkin.TokenTypeEmpty
	return true, token, nil
}

func (m *markdownMatcher) matchesAnything(line *gherkin.Line) (bool, error) {
	matchers := []func(*gherkin.Line) (bool, *gherkin.Token, error){
		m.MatchTagLine,
		m.MatchFeatureLine,
		m.MatchScenarioLine,
		m.MatchBackgroundLine,
		m.MatchExamplesLine,
		m.MatchRuleLine,
		m.MatchTableRow,
		m.MatchComment,
		m.MatchLanguage,
		m.MatchDocStringSeparator,
		m.MatchEOF,
		m.MatchStepLine,
	}
	for _, match := range matchers {
		ok, _, err := match(line)
		if err != nil {
			return false, err
		}
		if ok {
			return true, nil
		}
	}
	return false, nil
}

// MatchLanguage is deliberately inert: Markdown carries no `# language:` header, so
// users set the language globally, exactly as the Python matcher does.
func (m *markdownMatcher) MatchLanguage(*gherkin.Line) (bool, *gherkin.Token, error) {
	return false, nil, nil
}

func (m *markdownMatcher) MatchEOF(line *gherkin.Line) (bool, *gherkin.Token, error) {
	return m.base.MatchEOF(line)
}

func isGFMTableSeparator(cells []*gherkin.LineSpan) bool {
	for _, cell := range cells {
		if markdownTableSep.MatchString(cell.Text) {
			return true
		}
	}
	return false
}

var _ gherkin.Matcher = (*markdownMatcher)(nil)
