# Comparison: Pylint vs. Ruff Rule Coverage

This document outlines the differences in rule coverage between Pylint and Ruff. While Ruff has successfully implemented a substantial portion of Pylint's rule set (under the `PL` prefix), there are fundamental architectural differences and design decisions that result in a significant number of Pylint rules not being supported by Ruff.

---

## Architectural Difference

| Dimension | Pylint | Ruff |
| :--- | :--- | :--- |
| **Language** | Written in Python | Written in Rust |
| **Analysis Scope** | Cross-file dependency analysis and module-level graphing. | Single-file isolation (highly parallelizable). |
| **Evaluation Model** | AST parsing combined with dynamic type inference (`astroid` library). | Abstract Syntax Tree (AST) pattern matching. |
| **Type Awareness** | Resolves class hierarchies, method signatures, and attribute access. | Syntax-only; does not track variable types or dynamic values. |
| **Extensibility** | Supports custom Python plugins (checkers). | First-party rules only; no runtime plugin system. |

---

## Unsupported Pylint Rules in Ruff

Below is the complete list of all **273** Pylint rules that are **not supported** by Ruff, categorized by Pylint's rule types.

### Fatal (F) Rules (5 rules)

| Code | Symbol | Message Format | Description |
| :--- | :--- | :--- | :--- |
| `F0001` | `fatal` | `%s` | Used when an error occurred preventing the analysis of a               module (unable to find it for instance). |
| `F0002` | `astroid-error` | `%s: %s` | Used when an unexpected error occurred while building the Astroid  representation. This is usually accompanied by a traceback. Please report such errors ! |
| `F0010` | `parse-error` | `error while code parsing: %s` | Used when an exception occurred while building the Astroid representation which could be handled by astroid. |
| `F0011` | `config-parse-error` | `error while parsing the configuration: %s` | Used when an exception occurred while parsing a pylint configuration file. |
| `F0202` | `method-check-failed` | `Unable to check methods signature (%s / %s)` | Used when Pylint has been unable to check methods signature compatibility for an unexpected reason. Please report this kind if you don't make sense of it. |

---

### Info (I) Rules (9 rules)

| Code | Symbol | Message Format | Description |
| :--- | :--- | :--- | :--- |
| `I0001` | `raw-checker-failed` | `Unable to run raw checkers on built-in module %s` | Used to inform that a built-in module has not been checked using the raw checkers. |
| `I0010` | `bad-inline-option` | `Unable to consider inline option %r` | Used when an inline option is either badly formatted or can't be used inside modules. |
| `I0011` | `locally-disabled` | `Locally disabling %s (%s)` | Used when an inline option disables a message or a messages category. |
| `I0013` | `file-ignored` | `Ignoring entire file` | Used to inform that the file will not be checked |
| `I0020` | `suppressed-message` | `Suppressed %s (from line %d)` | A message was triggered on a line, but suppressed explicitly by a disable= comment in the file. This message is not generated for messages that are ignored due to configuration settings. |
| `I0021` | `useless-suppression` | `Useless suppression of %s` | Reported when a message is explicitly disabled for a line or a block of code, but never triggered. |
| `I0022` | `deprecated-pragma` | `Pragma "%s" is deprecated, use "%s" instead` | Some inline pylint options have been renamed or reworked, only the most recent form should be used. NOTE:skip-all is only available with pylint >= 0.26 |
| `I0023` | `use-symbolic-message-instead` | `%s` | Used when a message is enabled or disabled by id. |
| `I1101` | `c-extension-no-member` | `%s %r has no %r member%s, but source is unavailable. Consider adding this module to extension-pkg-allow-list if you want to perform analysis based on run-time introspection of living objects.` | Used when a variable is accessed for non-existent member of C extension. Due to unavailability of source static analysis is impossible, but it may be performed by introspecting living objects in run-time. |

---

### Convention (C) Rules (33 rules)

| Code | Symbol | Message Format | Description |
| :--- | :--- | :--- | :--- |
| `C0103` | `invalid-name` | `%s name "%s" doesn't conform to %s` | Used when the name doesn't conform to naming rules associated to its type (constant, variable, class...). |
| `C0104` | `disallowed-name` | `Disallowed name "%s"` | Used when the name matches bad-names or bad-names-rgxs- (unauthorized names). |
| `C0114` | `missing-module-docstring` | `Missing module docstring` | Used when a module has no docstring. Empty modules do not require a docstring. |
| `C0115` | `missing-class-docstring` | `Missing class docstring` | Used when a class has no docstring. Even an empty class must have a docstring. |
| `C0116` | `missing-function-docstring` | `Missing function or method docstring` | Used when a function or method has no docstring. Some special methods like __init__ do not require a docstring. |
| `C0117` | `unnecessary-negation` | `Consider changing "%s" to "%s"` | Used when a boolean expression contains an unneeded negation, e.g. when two negation operators cancel each other out. |
| `C0121` | `singleton-comparison` | `Comparison %s should be %s` | Used when an expression is compared to singleton values like True, False or None. |
| `C0123` | `unidiomatic-typecheck` | `Use isinstance() rather than type() for a typecheck.` | The idiomatic way to perform an explicit typecheck in Python is to use isinstance(x, Y) rather than type(x) == Y, type(x) is Y. Though there are unusual situations where these give different results. |
| `C0200` | `consider-using-enumerate` | `Consider using enumerate instead of iterating with range and len` | Emitted when code that iterates with range and len is encountered. Such code can be simplified by using the enumerate builtin. |
| `C0201` | `consider-iterating-dictionary` | `Consider iterating the dictionary directly instead of calling .keys()` | Emitted when the keys of a dictionary are iterated through the ``.keys()`` method or when ``.keys()`` is used for a membership check. It is enough to iterate through the dictionary itself, ``for key in dictionary``. For membership checks, ``if key in dictionary`` is faster. |
| `C0202` | `bad-classmethod-argument` | `Class method %s should have %s as first argument` | Used when a class method has a first argument named differently than the value specified in valid-classmethod-first-arg option (default to "cls"), recommended to easily differentiate them from regular instance methods. |
| `C0203` | `bad-mcs-method-argument` | `Metaclass method %s should have %s as first argument` | Used when a metaclass method has a first argument named differently than the value specified in valid-classmethod-first-arg option (default to "cls"), recommended to easily differentiate them from regular instance methods. |
| `C0204` | `bad-mcs-classmethod-argument` | `Metaclass class method %s should have %s as first argument` | Used when a metaclass class method has a first argument named differently than the value specified in valid-metaclass-classmethod-first-arg option (default to "mcs"), recommended to easily differentiate them from regular instance methods. |
| `C0209` | `consider-using-f-string` | `Formatting a regular string which could be an f-string` | Used when we detect a string that is being formatted with format() or % which could potentially be an f-string. The use of f-strings is preferred. Requires Python 3.6 and ``py-version >= 3.6``. |
| `C0302` | `too-many-lines` | `Too many lines in module (%s/%s)` | Used when a module has too many lines, reducing its readability. |
| `C0304` | `missing-final-newline` | `Final newline missing` | Used when the last line in a file is missing a newline. |
| `C0305` | `trailing-newlines` | `Trailing newlines` | Used when there are trailing blank lines in a file. |
| `C0321` | `multiple-statements` | `More than one statement on a single line` | Used when more than on statement are found on the same line. |
| `C0325` | `superfluous-parens` | `Unnecessary parens after %r keyword` | Used when a single item in parentheses follows an if, for, or other keyword. |
| `C0327` | `mixed-line-endings` | `Mixed line endings LF and CRLF` | Used when there are mixed (LF and CRLF) newline signs in a file. |
| `C0328` | `unexpected-line-ending-format` | `Unexpected line ending format. There is '%s' while it should be '%s'.` | Used when there is different newline than expected. |
| `C0401` | `wrong-spelling-in-comment` | `Wrong spelling of a word '%s' in a comment: %s %s Did you mean: '%s'?` | Used when a word in comment is not spelled correctly. |
| `C0402` | `wrong-spelling-in-docstring` | `Wrong spelling of a word '%s' in a docstring: %s %s Did you mean: '%s'?` | Used when a word in docstring is not spelled correctly. |
| `C0403` | `invalid-characters-in-docstring` | `Invalid characters %r in a docstring` | Used when a word in docstring cannot be checked by enchant. |
| `C0410` | `multiple-imports` | `Multiple imports on one line (%s)` | Used when import statement importing multiple modules is detected. |
| `C0411` | `wrong-import-order` | `%s should be placed before %s` | Used when PEP8 import order is not respected (standard imports first, then third-party libraries, then local imports). |
| `C0412` | `ungrouped-imports` | `Imports from package %s are not grouped` | Used when imports are not grouped by packages. |
| `C0413` | `wrong-import-position` | `Import "%s" should be placed at the top of the module` | Used when code and imports are mixed. |
| `C1803` | `use-implicit-booleaness-not-comparison` | `"%s" can be simplified to "%s", if it is strictly a sequence, as an empty %s is falsey` | Empty sequences are considered false in a boolean context. Following this check blindly in weakly typed code base can create hard to debug issues. If the value can be something else that is falsey but not a sequence (for example ``None``, an empty string, or ``0``) the code will not be equivalent. |
| `C1804` | `use-implicit-booleaness-not-comparison-to-string` | `"%s" can be simplified to "%s", if it is strictly a string, as an empty string is falsey` | Empty string are considered false in a boolean context. Following this check blindly in weakly typed code base can create hard to debug issues. If the value can be something else that is falsey but not a string (for example ``None``, an empty sequence, or ``0``) the code will not be equivalent. |
| `C1805` | `use-implicit-booleaness-not-comparison-to-zero` | `"%s" can be simplified to "%s", if it is strictly an int, as 0 is falsey` | 0 is considered false in a boolean context. Following this check blindly in weakly typed code base can create hard to debug issues. If the value can be something else that is falsey but not an int (for example ``None``, an empty string, or an empty sequence) the code will not be equivalent. |
| `C2503` | `bad-file-encoding` | `PEP8 recommends UTF-8 as encoding for Python files` | PEP8 recommends UTF-8 default encoding for Python files. See https://peps.python.org/pep-0008/#source-file-encoding |
| `C3001` | `unnecessary-lambda-assignment` | `Lambda expression assigned to a variable. Define a function using the "def" keyword instead.` | Used when a lambda expression is assigned to variable rather than defining a standard function with the "def" keyword. |

---

### Refactor (R) Rules (32 rules)

| Code | Symbol | Message Format | Description |
| :--- | :--- | :--- | :--- |
| `R0022` | `useless-option-value` | `Useless option value for '%s', %s` | Used when a value for an option that is now deleted from pylint is encountered. |
| `R0123` | `literal-comparison` | `In '%s', use '%s' when comparing constant literals not '%s' ('%s')` | Used when comparing an object to a literal, which is usually what you do not want to do, since you can compare to a different literal than what was expected altogether. |
| `R0401` | `cyclic-import` | `Cyclic import (%s)` | Used when a cyclic import between two or more modules is detected. |
| `R0801` | `duplicate-code` | `Similar lines in %s files %s` | Indicates that a set of similar lines has been detected among multiple file. This usually means that the code should be refactored to avoid this duplication. |
| `R0901` | `too-many-ancestors` | `Too many ancestors (%s/%s)` | Used when class has too many parent classes, try to reduce this to get a simpler (and so easier to use) class. |
| `R0902` | `too-many-instance-attributes` | `Too many instance attributes (%s/%s)` | Used when class has too many instance attributes, try to reduce this to get a simpler (and so easier to use) class. |
| `R0903` | `too-few-public-methods` | `Too few public methods (%s/%s)` | Used when class has too few public methods, so be sure it's really worth it. |
| `R1703` | `simplifiable-if-statement` | `The if statement can be replaced with %s` | Used when an if statement can be replaced with 'bool(test)'. |
| `R1705` | `no-else-return` | `Unnecessary "%s" after "return", %s` | Used in order to highlight an unnecessary block of code following an if, or a try/except containing a return statement. As such, it will warn when it encounters an else following a chain of ifs, all of them containing a return statement. |
| `R1707` | `trailing-comma-tuple` | `Disallow trailing comma tuple` | In Python, a tuple is actually created by the comma symbol, not by the parentheses. Unfortunately, one can actually create a tuple by misplacing a trailing comma, which can lead to potential weird bugs in your code. You should always use parentheses explicitly for creating a tuple. |
| `R1709` | `simplify-boolean-expression` | `Boolean expression may be simplified to %s` | Emitted when redundant pre-python 2.5 ternary syntax is used. |
| `R1710` | `inconsistent-return-statements` | `Either all return statements in a function should return an expression, or none of them should.` | According to PEP8, if any return statement returns an expression, any return statements where no value is returned should explicitly state this as return None, and an explicit return statement should be present at the end of the function (if reachable) |
| `R1713` | `consider-using-join` | `Consider using str.join(sequence) for concatenating strings from an iterable` | Using str.join(sequence) is faster, uses less memory and increases readability compared to for-loop iteration. |
| `R1715` | `consider-using-get` | `Consider using dict.get for getting values from a dict if a key is present or a default if not` | Using the builtin dict.get for getting a value from a dictionary if a key is present or a default if not, is simpler and considered more idiomatic, although sometimes a bit slower |
| `R1717` | `consider-using-dict-comprehension` | `Consider using a dictionary comprehension` | Emitted when we detect the creation of a dictionary using the dict() callable and a transient list. Although there is nothing syntactically wrong with this code, it is hard to read and can be simplified to a dict comprehension. Also it is faster since you don't need to create another transient list |
| `R1718` | `consider-using-set-comprehension` | `Consider using a set comprehension` | Although there is nothing syntactically wrong with this code, it is hard to read and can be simplified to a set comprehension. Also it is faster since you don't need to create another transient list |
| `R1719` | `simplifiable-if-expression` | `The if expression can be replaced with %s` | Used when an if expression can be replaced with 'bool(test)' or simply 'test' if the boolean cast is implicit. |
| `R1720` | `no-else-raise` | `Unnecessary "%s" after "raise", %s` | Used in order to highlight an unnecessary block of code following an if, or a try/except containing a raise statement. As such, it will warn when it encounters an else following a chain of ifs, all of them containing a raise statement. |
| `R1723` | `no-else-break` | `Unnecessary "%s" after "break", %s` | Used in order to highlight an unnecessary block of code following an if containing a break statement. As such, it will warn when it encounters an else following a chain of ifs, all of them containing a break statement. |
| `R1724` | `no-else-continue` | `Unnecessary "%s" after "continue", %s` | Used in order to highlight an unnecessary block of code following an if containing a continue statement. As such, it will warn when it encounters an else following a chain of ifs, all of them containing a continue statement. |
| `R1725` | `super-with-arguments` | `Consider using Python 3 style super() without arguments` | Emitted when calling the super() builtin with the current class and instance. On Python 3 these arguments are the default and they can be omitted. |
| `R1726` | `simplifiable-condition` | `Boolean condition "%s" may be simplified to "%s"` | Emitted when a boolean condition is able to be simplified. |
| `R1727` | `condition-evals-to-constant` | `Boolean condition '%s' will always evaluate to '%s'` | Emitted when a boolean condition can be simplified to a constant value. |
| `R1728` | `consider-using-generator` | `Consider using a generator instead '%s(%s)'` | If your container can be large using a generator will bring better performance. |
| `R1729` | `use-a-generator` | `Use a generator instead '%s(%s)'` | Comprehension inside of 'any', 'all', 'max', 'min' or 'sum' is unnecessary. A generator would be sufficient and faster. |
| `R1731` | `consider-using-max-builtin` | `Consider using '%s' instead of unnecessary if block` | Using the max builtin instead of a conditional improves readability and conciseness. |
| `R1732` | `consider-using-with` | `Consider using 'with' for resource-allocating operations` | Emitted if a resource-allocating assignment or call may be replaced by a 'with' block. By using 'with' the release of the allocated resources is ensured even in the case of an exception. |
| `R1734` | `use-list-literal` | `Consider using [] instead of list()` | Emitted when using list() to create an empty list instead of the literal []. The literal is faster as it avoids an additional function call. |
| `R1735` | `use-dict-literal` | `Consider using '%s' instead of a call to 'dict'.` | Emitted when using dict() to create a dictionary instead of a literal '{ ... }'. The literal is faster as it avoids an additional function call. |
| `R1737` | `use-yield-from` | `Use 'yield from' directly instead of yielding each element one by one` | Yielding directly from the iterator is faster and arguably cleaner code than yielding each element one by one in the loop. |
| `R1905` | `match-class-bind-self` | `Use '%s() as %s' instead` | Match class patterns are faster if the name binding happens for the whole pattern and any lookup for `__match_args__` can be avoided. |
| `R1906` | `match-class-positional-attributes` | `Use keyword attributes instead of positional ones (%s)` | Keyword attributes are more explicit and slightly faster since CPython can skip the `__match_args__` lookup. |

---

### Warning (W) Rules (104 rules)

| Code | Symbol | Message Format | Description |
| :--- | :--- | :--- | :--- |
| `W0012` | `unknown-option-value` | `Unknown option value for '%s', expected a valid pylint message and got '%s'` | Used when an unknown value is encountered for an option. |
| `W0101` | `unreachable` | `Unreachable code` | Used when there is some code behind a "return" or "raise" statement, which will never be accessed. |
| `W0102` | `dangerous-default-value` | `Dangerous default value %s as argument` | Used when a mutable value as list or dictionary is detected in a default value for an argument. |
| `W0104` | `pointless-statement` | `Statement seems to have no effect` | Used when a statement doesn't have (or at least seems to) any effect. |
| `W0105` | `pointless-string-statement` | `String statement has no effect` | Used when a string is used as a statement (which of course has no effect). This is a particular case of W0104 with its own message so you can easily disable it if you're using those strings as documentation, instead of comments. |
| `W0106` | `expression-not-assigned` | `Expression "%s" is assigned to nothing` | Used when an expression that is not a function call is assigned to nothing. Probably something else was intended. |
| `W0107` | `unnecessary-pass` | `Unnecessary pass statement` | Used when a "pass" statement can be removed without affecting the behaviour of the code. |
| `W0109` | `duplicate-key` | `Duplicate key %r in dictionary` | Used when a dictionary expression binds the same key multiple times. |
| `W0122` | `exec-used` | `Use of exec` | Raised when the 'exec' statement is used. It's dangerous to use this function for a user input, and it's also slower than actual code in general. This doesn't mean you should never use it, but you should consider alternatives first and restrict the functions available. |
| `W0123` | `eval-used` | `Use of eval` | Used when you use the "eval" function, to discourage its usage. Consider using `ast.literal_eval` for safely evaluating strings containing Python expressions from untrusted sources. |
| `W0124` | `confusing-with-statement` | `Following "as" with another context manager looks like a tuple.` | Emitted when a `with` statement component returns multiple values and uses name binding with `as` only for a part of those values, as in with ctx() as a, b. This can be misleading, since it's not clear if the context manager returns a tuple or if the node without a name binding is another context manager. |
| `W0125` | `using-constant-test` | `Using a conditional statement with a constant value` | Emitted when a conditional statement (If or ternary if) uses a constant value for its test. This might not be what the user intended to do. |
| `W0126` | `missing-parentheses-for-call-in-test` | `Using a conditional statement with potentially wrong function or method call due to missing parentheses` | Emitted when a conditional statement (If or ternary if) seems to wrongly call a function due to missing parentheses |
| `W0134` | `return-in-finally` | `'return' shadowed by the 'finally' clause.` | Emitted when a 'return' statement is found in a 'finally' block. This will overwrite the return value of a function and should be avoided. |
| `W0135` | `contextmanager-generator-missing-cleanup` | `The context used in function %r will not be exited.` | Used when a contextmanager is used inside a generator function and the cleanup is not handled. |
| `W0137` | `break-in-finally` | `'break' discouraged inside 'finally' clause` | Emitted when the `break` keyword is found inside a finally clause. This will raise a SyntaxWarning starting in Python 3.14. |
| `W0143` | `comparison-with-callable` | `Comparing against a callable, did you omit the parenthesis?` | This message is emitted when pylint detects that a comparison with a callable was made, which might suggest that some parenthesis were omitted, resulting in potential unwanted behaviour. |
| `W0150` | `lost-exception` | `%s statement in finally block may swallow exception` | Used when a break or a return statement is found inside the finally clause of a try...finally block: the exceptions raised in the try clause will be silently swallowed instead of being re-raised. |
| `W0199` | `assert-on-tuple` | `Assert called on a populated tuple. Did you mean 'assert x,y'?` | A call of assert on a tuple will always evaluate to true if the tuple is not empty, and will always evaluate to false if it is. |
| `W0201` | `attribute-defined-outside-init` | `Attribute %r defined outside __init__` | Used when an instance attribute is defined outside the __init__ method. |
| `W0212` | `protected-access` | `Access to a protected member %s of a client class` | Used when a protected member (i.e. class member with a name beginning with an underscore) is accessed outside the class or a descendant of the class where it's defined. |
| `W0213` | `implicit-flag-alias` | `Flag member %(overlap)s shares bit positions with %(sources)s` | Used when multiple integer values declared within an enum.IntFlag class share a common bit position. |
| `W0221` | `arguments-differ` | `%s %s %r method` | Used when a method has a different number of arguments than in the implemented interface or in an overridden method. Extra arguments with default values are ignored. |
| `W0222` | `signature-differs` | `Signature differs from %s %r method` | Used when a method signature is different than in the implemented interface or in an overridden method. |
| `W0223` | `abstract-method` | `Method %r is abstract in class %r but is not overridden in child class %r` | Used when an abstract method (i.e. raise NotImplementedError) is not overridden in concrete class. |
| `W0231` | `super-init-not-called` | `__init__ method from base class %r is not called` | Used when an ancestor class method has an __init__ method which is not called by a derived class. |
| `W0233` | `non-parent-init-called` | `__init__ method from a non direct base class %r is called` | Used when an __init__ method is called on a class which is not in the direct ancestors for the analysed class. |
| `W0236` | `invalid-overridden-method` | `Method %r was expected to be %r, found it instead as %r` | Used when we detect that a method was overridden in a way that does not match its base class which could result in potential bugs at runtime. |
| `W0237` | `arguments-renamed` | `%s %s %r method` | Used when a method parameter has a different name than in the implemented interface or in an overridden method. |
| `W0238` | `unused-private-member` | `Unused private member `%s.%s`` | Emitted when a private member of a class is defined but not used. |
| `W0239` | `overridden-final-method` | `Method %r overrides a method decorated with typing.final which is defined in class %r` | Used when a method decorated with typing.final has been overridden. |
| `W0240` | `subclassed-final-class` | `Class %r is a subclass of a class decorated with typing.final: %r` | Used when a class decorated with typing.final has been subclassed. |
| `W0246` | `useless-parent-delegation` | `Useless parent or super() delegation in method %r` | Used whenever we can detect that an overridden method is useless, relying on parent or super() delegation to do the same thing as another method from the MRO. |
| `W0301` | `unnecessary-semicolon` | `Unnecessary semicolon` | Used when a statement is ended by a semi-colon (";"), which isn't necessary (that's python, not C ;). |
| `W0311` | `bad-indentation` | `Bad indentation. Found %s %s, expected %s` | Used when an unexpected number of indentation's tabulations or spaces has been found. |
| `W0401` | `wildcard-import` | `Wildcard import %s` | Used when `from module import *` is detected. |
| `W0404` | `reimported` | `Reimport %r (imported line %s)` | Used when a module is imported more than once. |
| `W0407` | `preferred-module` | `Prefer importing %r instead of %r` | Used when a module imported has a preferred replacement module. |
| `W0410` | `misplaced-future` | `__future__ import is not the first non docstring statement` | Python 2.5 and greater require __future__ import to be the first non docstring statement in the module. |
| `W0416` | `shadowed-import` | `Shadowed %r (imported line %s)` | Used when a module is aliased with a name that shadows another import. |
| `W0511` | `fixme` | `%s` | Used when a warning note as FIXME or XXX is detected. |
| `W0601` | `global-variable-undefined` | `Global variable %r undefined at the module level` | Used when a variable is defined through the "global" statement but the variable is not defined in the module scope. |
| `W0613` | `unused-argument` | `Unused argument %r` | Used when a function or method argument is not used. |
| `W0614` | `unused-wildcard-import` | `Unused import(s) %s from wildcard import of %s` | Used when an imported module or variable is not used from a `'from X import *'` style import. |
| `W0621` | `redefined-outer-name` | `Redefining name %r from outer scope (line %s)` | Used when a variable's name hides a name defined in an outer scope or except handler. |
| `W0622` | `redefined-builtin` | `Redefining built-in %r` | Used when a variable or function override a built-in. |
| `W0631` | `undefined-loop-variable` | `Using possibly undefined loop variable %r` | Used when a loop variable (i.e. defined by a for loop or a list comprehension or a generator expression) is used outside the loop. |
| `W0632` | `unbalanced-tuple-unpacking` | `Possible unbalanced tuple unpacking with sequence %s: left side has %d label%s, right side has %d value%s` | Used when there is an unbalanced tuple unpacking in assignment |
| `W0640` | `cell-var-from-loop` | `Cell variable %s defined in loop` | A variable used in a closure is defined in a loop. This will result in all closures using the same value for the closed-over variable. |
| `W0641` | `possibly-unused-variable` | `Possibly unused variable %r` | Used when a variable is defined but might not be used. The possibility comes from the fact that locals() might be used, which could consume or not the said variable |
| `W0644` | `unbalanced-dict-unpacking` | `Possible unbalanced dict unpacking with %s: left side has %d label%s, right side has %d value%s` | Used when there is an unbalanced dict unpacking in assignment or for loop |
| `W0705` | `duplicate-except` | `Catching previously caught exception type %s` | Used when an except catches a type that was already caught by a previous handler. |
| `W0706` | `try-except-raise` | `The except handler raises immediately` | Used when an except handler uses raise as its first or only operator. This is useless because it raises back the exception immediately. Remove the raise operator or the entire try-except-raise block! |
| `W0707` | `raise-missing-from` | `Consider explicitly re-raising using %s'%s from %s'` | Python's exception chaining shows the traceback of the current exception, but also of the original exception. When you raise a new exception after another exception was caught it's likely that the second exception is a friendly re-wrapping of the first exception. In such cases `raise from` provides a better link between the two tracebacks in the final error. |
| `W0715` | `raising-format-tuple` | `Exception arguments suggest string formatting might be intended` | Used when passing multiple arguments to an exception constructor, the first of them a string literal containing what appears to be placeholders intended for formatting |
| `W0716` | `wrong-exception-operation` | `Invalid exception operation. %s` | Used when an operation is done against an exception, but the operation is not valid for the exception in question. Usually emitted when having binary operations between exceptions in except handlers. |
| `W0718` | `broad-exception-caught` | `Catching too general exception %s` | If you use a naked ``except Exception:`` clause, you might end up catching exceptions other than the ones you expect to catch. This can hide bugs or make it harder to debug programs when unrelated errors are hidden. |
| `W0719` | `broad-exception-raised` | `Raising too general exception: %s` | Raising exceptions that are too generic force you to catch exceptions generically too. It will force you to use a naked ``except Exception:`` clause. You might then end up catching exceptions other than the ones you expect to catch. This can hide bugs or make it harder to debug programs when unrelated errors are hidden. |
| `W1113` | `keyword-arg-before-vararg` | `Keyword argument before variable positional arguments list in the definition of %s function` | When defining a keyword argument before variable positional arguments, one can end up in having multiple values passed for the aforementioned parameter in case the method is called with keyword arguments. |
| `W1114` | `arguments-out-of-order` | `Positional arguments appear to be out of order` | Emitted  when the caller's argument names fully match the parameter names in the function signature but do not have the same order. |
| `W1115` | `non-str-assignment-to-dunder-name` | `Non-string value assigned to __name__` | Emitted when a non-string value is assigned to __name__ |
| `W1116` | `isinstance-second-argument-not-valid-type` | `Second argument of isinstance is not a type` | Emitted when the second argument of an isinstance call is not a type. |
| `W1117` | `kwarg-superseded-by-positional-arg` | `%r will be included in %r since a positional-only parameter with this name already exists` | Emitted when a function is called with a keyword argument that has the same name as a positional-only parameter and the function contains a keyword variadic parameter dict. |
| `W1201` | `logging-not-lazy` | `Use %s formatting in logging functions` | Used when a logging statement has a call form of "logging.<logging method>(format_string % (format_args...))". Use another type of string formatting instead. You can use % formatting but leave interpolation to the logging function by passing the parameters as arguments. If logging-fstring-interpolation is disabled then you can use fstring formatting. If logging-format-interpolation is disabled then you can use str.format. |
| `W1202` | `logging-format-interpolation` | `Use %s formatting in logging functions` | Used when a logging statement has a call form of "logging.<logging method>(format_string.format(format_args...))". Use another type of string formatting instead. You can use % formatting but leave interpolation to the logging function by passing the parameters as arguments. If logging-fstring-interpolation is disabled then you can use fstring formatting. If logging-not-lazy is disabled then you can use % formatting as normal. |
| `W1203` | `logging-fstring-interpolation` | `Use %s formatting in logging functions` | Used when a logging statement has a call form of "logging.<logging method>(f"...")".Use another type of string formatting instead. You can use % formatting but leave interpolation to the logging function by passing the parameters as arguments. If logging-format-interpolation is disabled then you can use str.format. If logging-not-lazy is disabled then you can use % formatting as normal. |
| `W1300` | `bad-format-string-key` | `Format string dictionary key should be a string, not %s` | Used when a format string that uses named conversion specifiers is used with a dictionary whose keys are not all strings. |
| `W1301` | `unused-format-string-key` | `Unused key %r in format string dictionary` | Used when a format string that uses named conversion specifiers is used with a dictionary that contains keys not required by the format string. |
| `W1302` | `bad-format-string` | `Invalid format string` | Used when a PEP 3101 format string is invalid. |
| `W1303` | `missing-format-argument-key` | `Missing keyword argument %r for format string` | Used when a PEP 3101 format string that uses named fields doesn't receive one or more required keywords. |
| `W1304` | `unused-format-string-argument` | `Unused format argument %r` | Used when a PEP 3101 format string that uses named fields is used with an argument that is not required by the format string. |
| `W1305` | `format-combined-specification` | `Format string contains both automatic field numbering and manual field specification` | Used when a PEP 3101 format string contains both automatic field numbering (e.g. '{}') and manual field specification (e.g. '{0}'). |
| `W1306` | `missing-format-attribute` | `Missing format attribute %r in format specifier %r` | Used when a PEP 3101 format string uses an attribute specifier ({0.length}), but the argument passed for formatting doesn't have that attribute. |
| `W1307` | `invalid-format-index` | `Using invalid lookup key %r in format specifier %r` | Used when a PEP 3101 format string uses a lookup specifier ({a[1]}), but the argument passed for formatting doesn't contain or doesn't have that key as an attribute. |
| `W1308` | `duplicate-string-formatting-argument` | `Duplicate string formatting argument %r, consider passing as named argument` | Used when we detect that a string formatting is repeating an argument instead of using named string arguments |
| `W1309` | `f-string-without-interpolation` | `Using an f-string that does not have any interpolated variables` | Used when we detect an f-string that does not use any interpolation variables, in which case it can be either a normal string or a bug in the code. |
| `W1310` | `format-string-without-interpolation` | `Using formatting for a string that does not have any interpolated variables` | Used when we detect a string that does not have any interpolation variables, in which case it can be either a normal string without formatting or a bug in the code. |
| `W1401` | `anomalous-backslash-in-string` | `Anomalous backslash in string: '%s'. String constant might be missing an r prefix.` | Used when a backslash is in a literal string but not as an escape. |
| `W1402` | `anomalous-unicode-escape-in-string` | `Anomalous Unicode escape in byte string: '%s'. String constant might be missing an r or u prefix.` | Used when an escape like \u is encountered in a byte string where it has no effect. |
| `W1404` | `implicit-str-concat` | `Implicit string concatenation found in %s` | String literals are implicitly concatenated in a literal iterable definition : maybe a comma is missing ? |
| `W1405` | `inconsistent-quotes` | `Quote delimiter %s is inconsistent with the rest of the file` | Quote delimiters are not used consistently throughout a module (with allowances made for avoiding unnecessary escaping). |
| `W1406` | `redundant-u-string-prefix` | `The u prefix for strings is no longer necessary in Python >=3.0` | Used when we detect a string with a u prefix. These prefixes were necessary in Python 2 to indicate a string was Unicode, but since Python 3.0 strings are Unicode by default. |
| `W1502` | `boolean-datetime` | `Using datetime.time in a boolean context.` | Using datetime.time in a boolean context can hide subtle bugs when the time they represent matches midnight UTC. This behaviour was fixed in Python 3.5. See https://bugs.python.org/issue13936 for reference. |
| `W1503` | `redundant-unittest-assert` | `Redundant use of %s with constant value %r` | The first argument of assertTrue and assertFalse is a condition. If a constant is passed as parameter, that condition will be always true. In this case a warning should be emitted. |
| `W1506` | `bad-thread-instantiation` | `threading.Thread needs the target function` | The warning is emitted when a threading.Thread class is instantiated without the target function being passed as a kwarg or as a second argument. By default, the first parameter is the group param, not the target param. |
| `W1515` | `forgotten-debug-statement` | `Leaving functions creating breakpoints in production code is not recommended` | Calls to breakpoint(), sys.breakpointhook() and pdb.set_trace() should be removed from code that is not actively being debugged. |
| `W1518` | `method-cache-max-size-none` | `'lru_cache(maxsize=None)' or 'cache' will keep all method args alive indefinitely, including 'self'` | By decorating a method with lru_cache or cache the 'self' argument will be linked to the function and therefore never garbage collected. Unless your instance will never need to be garbage collected (singleton) it is recommended to refactor code to avoid this pattern or add a maxsize to the cache. The default value for maxsize is 128. |
| `W2301` | `unnecessary-ellipsis` | `Unnecessary ellipsis constant` | Used when the ellipsis constant is encountered and can be avoided. A line of code consisting of an ellipsis is unnecessary if there is a docstring on the preceding line or if there is a statement in the same scope. |
| `W2402` | `non-ascii-file-name` | `%s name "%s" contains a non-ASCII character.` | Under python 3.5, PEP 3131 allows non-ascii identifiers, but not non-ascii file names.Since Python 3.5, even though Python supports UTF-8 files, some editors or tools don't. |
| `W2601` | `using-f-string-in-unsupported-version` | `F-strings are not supported by all versions included in the py-version setting` | Used when the py-version set by the user is lower than 3.6 and pylint encounters an f-string. |
| `W2602` | `using-final-decorator-in-unsupported-version` | `typing.final is not supported by all versions included in the py-version setting` | Used when the py-version set by the user is lower than 3.8 and pylint encounters a ``typing.final`` decorator. |
| `W2603` | `using-exception-groups-in-unsupported-version` | `Exception groups are not supported by all versions included in the py-version setting` | Used when the py-version set by the user is lower than 3.11 and pylint encounters ``except*`` or `ExceptionGroup``. |
| `W2604` | `using-generic-type-syntax-in-unsupported-version` | `Generic type syntax (PEP 695) is not supported by all versions included in the py-version setting` | Used when the py-version set by the user is lower than 3.12 and pylint encounters generic type syntax. |
| `W2605` | `using-assignment-expression-in-unsupported-version` | `Assignment expression is not supported by all versions included in the py-version setting` | Used when the py-version set by the user is lower than 3.8 and pylint encounters an assignment expression (walrus) operator. |
| `W2606` | `using-positional-only-args-in-unsupported-version` | `Positional-only arguments are not supported by all versions included in the py-version setting` | Used when the py-version set by the user is lower than 3.8 and pylint encounters positional-only arguments. |
| `W3101` | `missing-timeout` | `Missing timeout argument for method '%s' can cause your program to hang indefinitely` | Used when a method needs a 'timeout' parameter in order to avoid waiting for a long time. If no timeout is specified explicitly the default value is used. For example for 'requests' the program will never time out (i.e. hang indefinitely). |
| `W3601` | `bad-chained-comparison` | `Suspicious %s-part chained comparison using semantically incompatible operators (%s)` | Used when there is a chained comparison where one expression is part of two comparisons that belong to different semantic groups ("<" does not mean the same thing as "is", chaining them in "0 < x is None" is probably a mistake). |
| `W4701` | `modified-iterating-list` | `Iterated list '%s' is being modified inside for loop body, consider iterating through a copy of it instead.` | Emitted when items are added or removed to a list being iterated through. Doing so can result in unexpected behaviour, that is why it is preferred to use a copy of the list. |
| `W4901` | `deprecated-module` | `Deprecated module %r` | A module marked as deprecated is imported. |
| `W4902` | `deprecated-method` | `Using deprecated method %s()` | The method is marked as deprecated and will be removed in the future. |
| `W4903` | `deprecated-argument` | `Using deprecated argument %s of method %s()` | The argument is marked as deprecated and will be removed in the future. |
| `W4904` | `deprecated-class` | `Using deprecated class %s of module %s` | The class is marked as deprecated and will be removed in the future. |
| `W4905` | `deprecated-decorator` | `Using deprecated decorator %s()` | The decorator is marked as deprecated and will be removed in the future. |
| `W4906` | `deprecated-attribute` | `Using deprecated attribute %r` | The attribute is marked as deprecated and will be removed in the future. |

---

### Error (E) Rules (90 rules)

| Code | Symbol | Message Format | Description |
| :--- | :--- | :--- | :--- |
| `E0011` | `unrecognized-inline-option` | `Unrecognized file option %r` | Used when an unknown inline option is encountered. |
| `E0013` | `bad-plugin-value` | `Plugin '%s' is impossible to load, is it installed ? ('%s')` | Used when a bad value is used in 'load-plugins'. |
| `E0014` | `bad-configuration-section` | `Out-of-place setting encountered in top level configuration-section '%s' : '%s'` | Used when we detect a setting in the top level of a toml configuration that shouldn't be there. |
| `E0015` | `unrecognized-option` | `Unrecognized option found: %s` | Used when we detect an option that we do not recognize. |
| `E0102` | `function-redefined` | `%s already defined line %s` | Used when a function / class / method is redefined. |
| `E0103` | `not-in-loop` | `%r not properly in loop` | Used when break or continue keywords are used outside a loop. |
| `E0106` | `return-arg-in-generator` | `Return with argument inside generator` | Used when a "return" statement with an argument is found in a generator function or method (e.g. with some "yield" statements). |
| `E0107` | `nonexistent-operator` | `Use of the non-existent %s operator` | Used when you attempt to use the C-style pre-increment or pre-decrement operator -- and ++, which doesn't exist in Python. |
| `E0108` | `duplicate-argument-name` | `Duplicate argument name %r in function definition` | Duplicate argument names in function definitions are syntax errors. |
| `E0110` | `abstract-class-instantiated` | `Abstract class %r with abstract methods instantiated` | Used when an abstract class with `abc.ABCMeta` as metaclass has abstract methods and is instantiated. |
| `E0111` | `bad-reversed-sequence` | `The first reversed() argument is not a sequence` | Used when the first argument to reversed() builtin isn't a sequence (does not implement __reversed__, nor __getitem__ and __len__ |
| `E0112` | `too-many-star-expressions` | `More than one starred expression in assignment` | Emitted when there are more than one starred expressions (`*x`) in an assignment. This is a SyntaxError. |
| `E0113` | `invalid-star-assignment-target` | `Starred assignment target must be in a list or tuple` | Emitted when a star expression is used as a starred assignment target. |
| `E0114` | `star-needs-assignment-target` | `Can use starred expression only in assignment target` | Emitted when a star expression is not used in an assignment target. |
| `E0119` | `misplaced-format-function` | `format function is not called on str` | Emitted when format function is not called on str object. e.g doing print("value: {}").format(123) instead of print("value: {}".format(123)). This might not be what the user intended to do. |
| `E0202` | `method-hidden` | `An attribute defined in %s line %s hides this method` | Used when a class defines a method which is hidden by an instance attribute from an ancestor class or set by some client code. |
| `E0203` | `access-member-before-definition` | `Access to member %r before its definition line %s` | Used when an instance member is accessed before it's actually assigned. |
| `E0211` | `no-method-argument` | `Method %r has no argument` | Used when a method which should have the bound instance as first argument has no argument defined. |
| `E0213` | `no-self-argument` | `Method %r should have "self" as first argument` | Used when a method has an attribute different the "self" as first argument. This is considered as an error since this is a so common convention that you shouldn't break it! |
| `E0236` | `invalid-slots-object` | `Invalid object %r in __slots__, must contain only non empty strings` | Used when an invalid (non-string) object occurs in __slots__. |
| `E0238` | `invalid-slots` | `Invalid __slots__ object` | Used when an invalid __slots__ is found in class. Only a string, an iterable or a sequence is permitted. |
| `E0239` | `inherit-non-class` | `Inheriting %r, which is not a class.` | Used when a class inherits from something which is not a class. |
| `E0240` | `inconsistent-mro` | `Inconsistent method resolution order for class %r` | Used when a class has an inconsistent method resolution order. |
| `E0242` | `class-variable-slots-conflict` | `Value %r in slots conflicts with class variable` | Used when a value in __slots__ conflicts with a class variable, property or method. |
| `E0243` | `invalid-class-object` | `Invalid assignment to '__class__'. Should be a class definition but got a '%s'` | Used when an invalid object is assigned to a __class__ property. Only a class is permitted. |
| `E0244` | `invalid-enum-extension` | `Extending inherited Enum class "%s"` | Used when a class tries to extend an inherited Enum class. Doing so will raise a TypeError at runtime. |
| `E0245` | `declare-non-slot` | `No such name %r in __slots__` | Raised when a type annotation on a class is absent from the list of names in __slots__, and __slots__ does not contain a __dict__ entry. |
| `E0301` | `non-iterator-returned` | `__iter__ returns non-iterator` | Used when an __iter__ method returns something which is not an iterable (i.e. has no `__next__` method) |
| `E0306` | `invalid-repr-returned` | `__repr__ does not return str` | Used when a __repr__ method returns something which is not a string |
| `E0310` | `invalid-length-hint-returned` | `__length_hint__ does not return non-negative integer` | Used when a __length_hint__ method returns something which is not a non-negative integer |
| `E0311` | `invalid-format-returned` | `__format__ does not return str` | Used when a __format__ method returns something which is not a string |
| `E0312` | `invalid-getnewargs-returned` | `__getnewargs__ does not return a tuple` | Used when a __getnewargs__ method returns something which is not a tuple |
| `E0313` | `invalid-getnewargs-ex-returned` | `__getnewargs_ex__ does not return a tuple containing (tuple, dict)` | Used when a __getnewargs_ex__ method returns something which is not of the form tuple(tuple, dict) |
| `E0401` | `import-error` | `Unable to import %s` | Used when pylint has been unable to import a module. |
| `E0402` | `relative-beyond-top-level` | `Attempted relative import beyond top-level package` | Used when a relative import tries to access too many levels in the current package. |
| `E0601` | `used-before-assignment` | `Using variable %r before assignment` | Emitted when a local variable is accessed before its assignment took place. Assignments in try blocks are assumed not to have occurred when evaluating associated except/finally blocks. Assignments in except blocks are assumed not to have occurred when evaluating statements outside the block, except when the associated try block contains a return statement. |
| `E0602` | `undefined-variable` | `Undefined variable %r` | Used when an undefined variable is accessed. |
| `E0603` | `undefined-all-variable` | `Undefined variable name %r in __all__` | Used when an undefined variable name is referenced in __all__. |
| `E0606` | `possibly-used-before-assignment` | `Possibly using variable %r before assignment` | Emitted when a local variable is accessed before its assignment took place in both branches of an if/else switch. |
| `E0611` | `no-name-in-module` | `No name %r in module %r` | Used when a name cannot be found in a module. |
| `E0633` | `unpacking-non-sequence` | `Attempting to unpack a non-sequence%s` | Used when something which is not a sequence is used in an unpack assignment |
| `E0701` | `bad-except-order` | `Bad except clauses order (%s)` | Used when except clauses are not in the correct order (from the more specific to the more generic). If you don't fix the order, some exceptions may not be caught by the most specific handler. |
| `E0702` | `raising-bad-type` | `Raising %s while only classes or instances are allowed` | Used when something which is neither a class nor an instance is raised (i.e. a `TypeError` will be raised). |
| `E0705` | `bad-exception-cause` | `Exception cause set to something which is not an exception, nor None` | Used when using the syntax "raise ... from ...", where the exception cause is not an exception, nor None. |
| `E0710` | `raising-non-exception` | `Raising a class which doesn't inherit from BaseException` | Used when a class which doesn't inherit from BaseException is raised. |
| `E0711` | `notimplemented-raised` | `NotImplemented raised - should raise NotImplementedError` | Used when NotImplemented is raised instead of NotImplementedError |
| `E0712` | `catching-non-exception` | `Catching an exception which doesn't inherit from Exception: %s` | Used when a class which doesn't inherit from Exception is used as an exception in an except clause. |
| `E1003` | `bad-super-call` | `Bad first argument %r given to super()` | Used when another argument than the current class is given as first argument of the super builtin. |
| `E1101` | `no-member` | `%s %r has no %r member%s` | Used when a variable is accessed for a nonexistent member. |
| `E1102` | `not-callable` | `%s is not callable` | Used when an object being called has been inferred to a non callable object. |
| `E1111` | `assignment-from-no-return` | `Assigning result of a function call, where the function has no return` | Used when an assignment is done on a function call but the inferred function doesn't return anything. |
| `E1120` | `no-value-for-parameter` | `No value for argument %s in %s call` | Used when a function call passes too few arguments. |
| `E1121` | `too-many-function-args` | `Too many positional arguments for %s call` | Used when a function call passes too many positional arguments. |
| `E1123` | `unexpected-keyword-arg` | `Unexpected keyword argument %r in %s call` | Used when a function call passes a keyword argument that doesn't correspond to one of the function's parameter names. |
| `E1124` | `redundant-keyword-arg` | `Argument %r passed by position and keyword in %s call` | Used when a function call would result in assigning multiple values to a function parameter, one value from a positional argument and one from a keyword argument. |
| `E1125` | `missing-kwoa` | `Missing mandatory keyword argument %r in %s call` | Used when a function call does not pass a mandatory keyword-only argument. |
| `E1126` | `invalid-sequence-index` | `Sequence index is not an int, slice, or instance with __index__` | Used when a sequence type is indexed with an invalid type. Valid types are ints, slices, and objects with an __index__ method. |
| `E1127` | `invalid-slice-index` | `Slice index is not an int, None, or instance with __index__` | Used when a slice index is not an integer, None, or an object with an __index__ method. |
| `E1128` | `assignment-from-none` | `Assigning result of a function call, where the function returns None` | Used when an assignment is done on a function call but the inferred function returns nothing but None. |
| `E1129` | `not-context-manager` | `Context manager '%s' doesn't implement __enter__ and __exit__.` | Used when an instance in a with statement doesn't implement the context manager protocol(__enter__/__exit__). |
| `E1130` | `invalid-unary-operand-type` | `%s` | Emitted when a unary operand is used on an object which does not support this type of operation. |
| `E1131` | `unsupported-binary-operation` | `%s` | Emitted when a binary arithmetic operation between two operands is not supported. |
| `E1133` | `not-an-iterable` | `Non-iterable value %s is used in an iterating context` | Used when a non-iterable value is used in place where iterable is expected |
| `E1134` | `not-a-mapping` | `Non-mapping value %s is used in a mapping context` | Used when a non-mapping value is used in place where mapping is expected |
| `E1135` | `unsupported-membership-test` | `Value '%s' doesn't support membership test` | Emitted when an instance in membership test expression doesn't implement membership protocol (__contains__/__iter__/__getitem__). |
| `E1136` | `unsubscriptable-object` | `Value '%s' is unsubscriptable` | Emitted when a subscripted value doesn't support subscription (i.e. doesn't define __getitem__ method or __class_getitem__ for a class). |
| `E1137` | `unsupported-assignment-operation` | `%r does not support item assignment` | Emitted when an object does not support item assignment (i.e. doesn't define __setitem__ method). |
| `E1138` | `unsupported-delete-operation` | `%r does not support item deletion` | Emitted when an object does not support item deletion (i.e. doesn't define __delitem__ method). |
| `E1139` | `invalid-metaclass` | `Invalid metaclass %r used` | Emitted whenever we can detect that a class is using, as a metaclass, something which might be invalid for using as a metaclass. |
| `E1143` | `unhashable-member` | `'%s' is unhashable and can't be used as a %s in a %s` | Emitted when a dict key or set member is not hashable (i.e. doesn't define __hash__ method). |
| `E1144` | `invalid-slice-step` | `Slice step cannot be 0` | Used when a slice step is 0 and the object doesn't implement a custom __getitem__ method. |
| `E1145` | `async-context-manager-with-regular-with` | `Context manager '%s' is async and should be used with 'async with'.` | Used when an async context manager is used with a regular 'with' statement instead of 'async with'. |
| `E1200` | `logging-unsupported-format` | `Unsupported logging format character %r (%#02x) at index %d` | Used when an unsupported format character is used in a logging statement format string. |
| `E1201` | `logging-format-truncated` | `Logging format string ends in middle of conversion specifier` | Used when a logging statement format string terminates before the end of a conversion specifier. |
| `E1301` | `truncated-format-string` | `Format string ends in middle of conversion specifier` | Used when a format string terminates before the end of a conversion specifier. |
| `E1302` | `mixed-format-string` | `Mixing named and unnamed conversion specifiers in format string` | Used when a format string contains both named (e.g. '%(foo)d') and unnamed (e.g. '%d') conversion specifiers.  This is also used when a named conversion specifier contains * for the minimum field width and/or precision. |
| `E1303` | `format-needs-mapping` | `Expected mapping for format string, not %s` | Used when a format string that uses named conversion specifiers is used with an argument that is not a mapping. |
| `E1304` | `missing-format-string-key` | `Missing key %r in format string dictionary` | Used when a format string that uses named conversion specifiers is used with a dictionary that doesn't contain all the keys required by the format string. |
| `E1305` | `too-many-format-args` | `Too many arguments for format string` | Used when a format string that uses unnamed conversion specifiers is given too many arguments. |
| `E1306` | `too-few-format-args` | `Not enough arguments for format string` | Used when a format string that uses unnamed conversion specifiers is given too few arguments |
| `E1701` | `not-async-context-manager` | `Async context manager '%s' doesn't implement __aenter__ and __aexit__.` | Used when an async context manager is used with an object that does not implement the async context management protocol. |
| `E1901` | `bare-name-capture-pattern` | `The name capture `case %s` makes the remaining patterns unreachable. Use a dotted name (for example an enum) to fix this.` | Emitted when a name capture pattern is used in a match statement and there are case statements below it. |
| `E1902` | `invalid-match-args-definition` | ``__match_args__` must be a tuple of strings.` | Emitted if `__match_args__` isn't a tuple of strings required for match. |
| `E1903` | `too-many-positional-sub-patterns` | `%s expects %d positional sub-patterns (given %d)` | Emitted when the number of allowed positional sub-patterns exceeds the number of allowed sub-patterns specified in `__match_args__`. |
| `E1904` | `multiple-class-sub-patterns` | `Multiple sub-patterns for attribute %s` | Emitted when there is more than one sub-pattern for a specific attribute in a class pattern. |
| `E2501` | `invalid-unicode-codec` | `UTF-16 and UTF-32 aren't backward compatible. Use UTF-8 instead` | For compatibility use UTF-8 instead of UTF-16/UTF-32. See also https://bugs.python.org/issue1503789 for a history of this issue. And https://softwareengineering.stackexchange.com/questions/102205/ for some possible problems when using UTF-16 for instance. |
| `E2511` | `invalid-character-carriage-return` | `Invalid unescaped character carriage-return, use "\r" instead.` | Moves the cursor to the start of line, subsequent characters overwrite the start of the line. |
| `E3102` | `positional-only-arguments-expected` | ``%s()` got some positional-only arguments passed as keyword arguments: %s` | Emitted when positional-only arguments have been passed as keyword arguments. Remove the keywords for the affected arguments in the function call. |
| `E3701` | `invalid-field-call` | `Invalid usage of field(), %s` | The dataclasses.field() specifier should only be used as the value of an assignment within a dataclass, or within the make_dataclass() function. |
| `E4702` | `modified-iterating-dict` | `Iterated dict '%s' is being modified inside for loop body, iterate through a copy of it instead.` | Emitted when items are added or removed to a dict being iterated through. Doing so raises a RuntimeError. |

---
