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

	gherkin "github.com/cucumber/gherkin/go/v42"
	messages "github.com/cucumber/messages/go/v34"
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
	return parseAndSerialize(
		C.GoStringN(source, length),
		gherkin.NewLanguageMatcher(gherkin.DialectsBuiltin(), gherkin.DefaultDialect),
	)
}

//export ParseGherkinMarkdown
func ParseGherkinMarkdown(source *C.char, length C.int) *C.char {
	return parseAndSerialize(C.GoStringN(source, length), newMarkdownMatcher())
}

//export FreeCString
func FreeCString(source *C.char) {
	if source != nil {
		C.free(unsafe.Pointer(source))
	}
}

//export Version
func Version() *C.char {
	return C.CString("v42.0.1")
}

func parseAndSerialize(input string, matcher gherkin.Matcher) (result *C.char) {
	defer func() {
		if recovered := recover(); recovered != nil {
			result = serializeFailure(failure{
				ErrorType: "runtime",
				Message:   fmt.Sprintf("Go parser panic: %v", recovered),
			})
		}
	}()

	builder := gherkin.NewAstBuilder((&messages.Incrementing{}).NewId)
	parser := gherkin.NewParser(builder)
	parser.StopAtFirstError(false)
	if err := parser.Parse(gherkin.NewScanner(strings.NewReader(input)), matcher); err != nil {
		return serializeFailure(failure{
			ErrorType: "syntax",
			Errors:    []parserError{{Message: err.Error()}},
		})
	}
	document := builder.GetGherkinDocument()
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
