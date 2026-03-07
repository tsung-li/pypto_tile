# Code Review Skill for Pypto Tile DSL

This skill provides comprehensive code review guidance for the pypto-tile project, a Python binding for a tile DSL compiler similar to CuTile.

## What This Skill Checks

When reviewing code in this project, focus on these key areas:

### 1. Python-C++ Binding Safety

#### Memory Management

- [ ] Check for proper reference counting when converting between Python and C++ objects
- [ ] Ensure no dangling references to Python objects in IR structures
- [ ] Verify proper lifetime management of `Loc` objects and their function references
- [ ] Look for potential use-after-free bugs in AST node processing

#### Type Conversion

- [ ] Validate all Python-to-C++ type conversions use proper `typeof_pyval` or similar
- [ ] Check that constant folding uses `get_constant_value` with error handling
- [ ] Ensure type annotations match runtime behavior for binding code

#### Example Issues to Catch

```python
# BAD: Direct reference without lifetime management
def bad_example():
    return ast_node.lineno  # ast_node might be freed

# GOOD: Proper extraction and storage
def good_example(ctx, node):
    loc = ctx.get_loc(node)  # Creates owned Loc object
    return loc
```

### 2. AST Manipulation Safety

#### Node Validation

- [ ] Verify all AST nodes are validated before processing
- [ ] Check for proper error handling with `ctx.unsupported_syntax()`
- [ ] Ensure source location tracking uses correct line number calculations

#### Edge Cases

- [ ] Handle chained comparisons properly (see `_compare_expr`)
- [ ] Verify closure variable extraction handles edge cases
- [ ] Check that `__wrapped__` attribute handling doesn't break on decorators

#### Example Issues to Catch

```python
# BAD: No validation
def _bad_expr(node):
    return node.value  # Could be None or wrong type

# GOOD: Proper validation
def _good_expr(node, ctx):
    if not isinstance(node, ast.Constant):
        raise ctx.unsupported_syntax(node)
    return node.value
```

### 3. IR Construction Correctness

#### Block Management

- [ ] Ensure all blocks have proper `EndBranch` operations before branching
- [ ] Check that nested blocks are properly connected to parent blocks
- [ ] Verify variable scopes are correctly maintained across blocks

#### Operation Construction

- [ ] Validate all operation operands are `Var` objects, not raw Python values
- [ ] Check that result variables are created before being used as operands
- [ ] Ensure operation attributes are properly typed

#### Example Issues to Catch

```python
# BAD: Missing EndBranch
def bad_ifelse(cond, then_block, else_block):
    block.append(ops.IfElse(cond, then_block, else_block))
    # Missing EndBranch in then/else blocks!

# GOOD: Proper block termination
def good_ifelse(cond, then_block, else_block, loc):
    then_block.append(ops.EndBranch(loc, outputs=()))
    else_block.append(ops.EndBranch(loc, outputs=()))
    block.append(ops.IfElse(cond, then_block, else_block, loc))
```

### 4. Type System Integrity

#### Type Propagation

- [ ] Ensure type information is properly copied via `copy_type_information`
- [ ] Check that `try_get_type()` returns are always validated before use
- [ ] Verify constant vs non-const type distinction is maintained

#### Undefined Variables

- [ ] Check that undefined variables are marked correctly
- [ ] Ensure `get_type()` raises proper error for undefined vars
- [ ] Validate that loose types are used where appropriate

#### Example Issues to Catch

```python
# BAD: Not checking for None type
def bad_usage(var):
    ty = var.try_get_type()
    return ty.name  # Could crash if ty is None!

# GOOD: Proper None checking
def good_usage(var):
    ty = var.try_get_type()
    if ty is None:
        return "unknown"
    return ty.name
```

### 5. Error Handling Quality

#### Error Messages

- [ ] Ensure all errors include proper source location information
- [ ] Check that error messages are descriptive and actionable
- [ ] Verify `TileSyntaxError` and `TileTypeError` are used appropriately

#### Error Context

- [ ] Include the problematic syntax/operation in error messages
- [ ] Ensure call site information is preserved through the stack
- [ ] Check that error recovery doesn't leave IR in inconsistent state

#### Example Issues to Catch

```python
# BAD: Vague error message
raise TileSyntaxError("Invalid operation", loc)

# GOOD: Descriptive error with context
raise ctx.syntax_error(node, f"Unsupported operation: {type(node.op).__name__}")
```

### 6. Testing Best Practices

#### Compiler Testing

- [ ] Ensure tests cover both successful compilation and error cases
- [ ] Check that tests verify IR structure, not just "no errors"
- [ ] Test edge cases: empty functions, single statements, complex nesting

#### Test Structure

- [ ] Each test should be independent and not rely on test order
- [ ] Use descriptive test names that explain what is being tested
- [ ] Include assertions that verify the actual IR output structure

#### Example Test Pattern

```python
def test_arithmetic_addition():
    """Test that binary addition produces correct IR structure."""
    def test_func(x, y):
        return x + y

    result = compile(test_func, (2, 3), None)

    # Verify structure, not just existence
    assert result.root_block
    ops_list = list(result.root_block)
    assert len(ops_list) >= 2  # load, const, call sequence
```

### 7. Documentation Standards

#### Docstrings

- [ ] All public functions must have Google-style docstrings
- [ ] Include parameter types and return types
- [ ] Document any side effects or exceptions raised

#### Comments

- [ ] Comment non-obvious algorithms (e.g., line number calculations)
- [ ] Explain workarounds for Python AST limitations
- [ ] Document any assumptions about Python/C++ behavior

#### Example

```python
def _get_source_line_no(first_line_no: int, ast_line_no: int) -> int:
    """Convert AST line number to original source line number.

    Why -2?
       -1 because both first_line_no and ast_line_no are 1-based;
       another -1 to account for the "if True" line that we inserted.
    """
    return first_line_no + ast_line_no - 2
```

### 8. Performance Considerations

#### AST Processing

- [ ] Avoid redundant AST traversals
- [ ] Cache computed values when safe
- [ ] Use efficient data structures for variable lookups

#### IR Construction

- [ ] Minimize temporary variable creation
- [ ] Reuse operations when possible
- [ ] Consider memory overhead of nested blocks

## Common Issue Patterns

### Pattern 1: Missing Source Location

Symptom: Errors don't point to correct source line
Check: All operations should include `loc` parameter
Fix: Always pass `ctx.get_loc(node)` to operations

### Pattern 2: Incorrect Variable Scope

Symptom: Variables leak between blocks or functions
Check: Variable creation uses `ctx.define_var()` for parameters, `block.make_temp_var()` for temps
Fix: Use appropriate variable creation method for context

### Pattern 3: Incomplete Block Termination

Symptom: IR validation fails or crashes during lowering
Check: All blocks have proper termination (EndBranch, return, etc.)
Fix: Add termination ops before creating control flow

### Pattern 4: Type Assumptions

Symptom: Crashes when processing unexpected types
Check: All type assertions use isinstance checks
Fix: Add proper validation before type-dependent operations

## Review Process

1. First Pass - Architecture: Does the change fit the overall architecture?
2. Second Pass - Safety: Are there memory/type/lifetime issues?
3. Third Pass - Correctness: Does the IR match the intended semantics?
4. Fourth Pass - Testing: Are edge cases covered?
5. Fifth Pass - Documentation: Is the code understandable?

## Red Flags

🚩 Immediately Request Changes For

- Direct memory manipulation without proper lifecycle management
- Missing error handling for user-provided code
- Type coercion without validation
- Unreachable code (dead code) in hot paths
- Missing source location information in operations
- Tests that don't actually verify the behavior

⚠️ Discuss With Author

- Complex algorithms without explanatory comments
- New public APIs without docstrings
- Performance optimizations without benchmarks
- Changes to error handling behavior
- Modifications to core IR structures

## Project-Specific Guidelines

### For AST Processing Code

- Always use `ctx.get_loc(node)` for source locations
- Validate AST node types before accessing attributes
- Handle all possible AST node variants explicitly
- Use the handler dispatch pattern for extensibility

### For IR Construction

- Create result variables before operations that use them
- Ensure proper block termination before control flow
- Use `block.make_temp_var()` for temporaries, `ctx.define_var()` for named vars
- Check that all operands are `Var` objects, not Python values

### For Type System Code

- Always handle `None` return from `try_get_type()`
- Use `loose_type` for constexpr arguments
- Propagate type information via `copy_type_information()`
- Distinguish between compile-time and runtime types

### For Testing Code

- Test both success and error paths
- Verify IR structure, not just "no crash"
- Include edge cases (empty, single, complex cases)
- Use descriptive assertion messages

## Example Review Comments

### Critical Issues

```markdown
CRITICAL: Memory Safety Issue
This code stores a reference to `node` which may be freed after AST processing completes.
Please extract all needed information into a `Loc` object immediately.
```

### Style Issues

```markdown
SUGGESTION: Error Message Clarity
The error message "Invalid operation" is not very helpful. Please include the
operation type and context: f"Unsupported operation: {type(node.op).__name__} in {ctx.function}"
```

### Architecture Issues

```markdown
QUESTION: Design Decision
This changes the IR structure in a way that affects lowering. Have we
updated the C++ backend to handle this new operation format?
```

## Final Checklist

Before approving a PR, verify:

- [ ] All new code has appropriate error handling
- [ ] Source locations are preserved throughout
- [ ] Tests cover new functionality and edge cases
- [ ] Documentation is updated for API changes
- [ ] No memory safety issues introduced
- [ ] Type system integrity maintained
- [ ] IR construction is correct and verifiable
- [ ] Performance impact is acceptable or documented
