package main

/*
#include <stdlib.h>
*/
import "C"

import (
	"encoding/json"
	"fmt"
	"strings"
	"unsafe"

	gherkin "github.com/cucumber/gherkin/go/v28"
	messages "github.com/cucumber/messages/go/v24"
)

type parserError struct {
	Message string `json:"message"`
}

type failure struct {
	ErrorType string        `json:"errorType"`
	Message   string        `json:"message,omitempty"`
	Errors    []parserError `json:"errors,omitempty"`
}

//export ParseGherkinDocument
func ParseGherkinDocument(source *C.char, length C.int) *C.char {
	return parseAndSerialize(C.GoStringN(source, length))
}

//export ParseGherkinMarkdown
func ParseGherkinMarkdown(source *C.char, length C.int) *C.char {
	markdown := C.GoStringN(source, length)
	return parseAndSerialize(extractGherkinFromMarkdown(markdown))
}

//export FreeCString
func FreeCString(source *C.char) {
	if source != nil {
		C.free(unsafe.Pointer(source))
	}
}

//export Version
func Version() *C.char {
	return C.CString("v28.0.0")
}

func extractGherkinFromMarkdown(markdown string) string {
	lines := strings.Split(markdown, "\n")
	gherkinLines := make([]string, 0, len(lines))
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

func parseAndSerialize(input string) (result *C.char) {
	defer func() {
		if recovered := recover(); recovered != nil {
			result = serializeFailure(failure{
				ErrorType: "runtime",
				Message:   fmt.Sprintf("Go parser panic: %v", recovered),
			})
		}
	}()

	document, err := gherkin.ParseGherkinDocument(strings.NewReader(input), (&messages.Incrementing{}).NewId)
	if err != nil {
		return serializeFailure(failure{
			ErrorType: "syntax",
			Errors:    []parserError{{Message: err.Error()}},
		})
	}
	if document == nil || document.Feature == nil {
		return serializeFailure(failure{ErrorType: "empty", Message: "Go parser returned no Feature"})
	}

	jsonBytes, err := json.Marshal(document)
	if err != nil {
		return serializeFailure(failure{
			ErrorType: "runtime",
			Message:   "JSON serialization failed: " + err.Error(),
		})
	}
	return C.CString(string(jsonBytes))
}

func serializeFailure(value failure) *C.char {
	jsonBytes, err := json.Marshal(value)
	if err != nil {
		return C.CString(`{"errorType":"runtime","message":"native parser failed"}`)
	}
	return C.CString(string(jsonBytes))
}

func main() {}
