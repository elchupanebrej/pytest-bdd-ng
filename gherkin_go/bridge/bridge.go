package main

import "C"
import (
	"encoding/json"
	"strings"
	"unsafe"

	"github.com/gofrs/uuid"
	gherkin "github.com/cucumber/gherkin/go/v28"
)

//export ParseGherkinDocument
func ParseGherkinDocument(text *C.char) *C.char {
	return parseAndSerialize(C.GoString(text))
}

//export ParseGherkinMarkdown
func ParseGherkinMarkdown(text *C.char) *C.char {
	markdown := C.GoString(text)
	gherkinText := extractGherkinFromMarkdown(markdown)
	return parseAndSerialize(gherkinText)
}

//export FreeCString
func FreeCString(s *C.char) {
	C.free(unsafe.Pointer(s))
}

//export Version
func Version() *C.char {
	return C.CString("v28.0.0")
}

func extractGherkinFromMarkdown(markdown string) string {
	lines := strings.Split(markdown, "\n")
	var gherkinLines []string
	inBlock := false
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if strings.HasPrefix(trimmed, "```gherkin") ||
			strings.HasPrefix(trimmed, "```feature") ||
			strings.HasPrefix(trimmed, "```cucumber") ||
			strings.HasPrefix(trimmed, "```Gherkin") {
			inBlock = true
			continue
		}
		if inBlock && strings.HasPrefix(trimmed, "```") {
			inBlock = false
			continue
		}
		if inBlock {
			gherkinLines = append(gherkinLines, line)
		}
	}
	if len(gherkinLines) == 0 {
		return markdown
	}
	return strings.Join(gherkinLines, "\n")
}

func parseAndSerialize(input string) *C.char {
	newId := func() string {
		return uuid.Must(uuid.NewV4()).String()
	}

	doc, err := gherkin.ParseGherkinDocument(strings.NewReader(input), newId)
	if err != nil {
		return serializeError(err)
	}

	jsonBytes, err := json.Marshal(doc)
	if err != nil {
		errs := []parseError{{
			Source:  source{URI: "", Location: location{Line: 0, Column: 0}},
			Message: "JSON serialization failed: " + err.Error(),
		}}
		jsonBytes, _ = json.Marshal(errs)
		return C.CString(string(jsonBytes))
	}

	return C.CString(string(jsonBytes))
}

func serializeError(err error) *C.char {
	type source struct {
		URI      string   `json:"uri"`
		Location location `json:"location"`
	}
	type location struct {
		Line   int `json:"line"`
		Column int `json:"column"`
	}
	type parseError struct {
		Source  source `json:"source"`
		Message string `json:"message"`
	}

	errs := []parseError{{
		Source: source{
			URI:      "",
			Location: location{Line: 0, Column: 0},
		},
		Message: err.Error(),
	}}

	jsonBytes, _ := json.Marshal(errs)
	return C.CString(string(jsonBytes))
}

func main() {}
