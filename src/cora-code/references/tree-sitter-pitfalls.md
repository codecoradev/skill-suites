# Tree-sitter Pitfalls & Patterns (v0.26)

## Grammar Crate Versions

| Crate | Version | License |
|-------|---------|---------|
| `tree-sitter` | 0.26.x | MIT |
| `tree-sitter-rust` | 0.24.x | MIT |
| `tree-sitter-go` | 0.25.x | MIT |
| `tree-sitter-python` | 0.25.x | MIT |
| `tree-sitter-typescript` | 0.23.x | MIT |

All compile C code statically into the binary. 4 languages ≈ 454KB release binary.

## API: `Node` Traversal

### No `descendants()` method (v0.26)

Tree-sitter 0.26 removed `descendants()`. Use cursor-based DFS:

```rust
fn walk(node: &tree_sitter::Node, source: &str) {
    let mut cursor = node.walk();
    if cursor.goto_first_child() {
        loop {
            process(&cursor.node(), source);
            walk(&cursor.node(), source); // recurse
            if !cursor.goto_next_sibling() { break; }
        }
    }
}
```

### `row`/`column` are already `usize`

In v0.26, `start_position().row` and `.column` return `usize` directly. No `as usize` cast needed. Clippy flags unnecessary casts.

## API: Grammar Language Constant

Grammar crates expose `LANGUAGE` as a `Language` constant (not a `language()` function):

```rust
// CORRECT
Some(tree_sitter_rust::LANGUAGE.into())

// WRONG — doesn't exist
Some(tree_sitter_rust::language())
```

## API: Node Name Access — Field Names Are Unreliable

**Problem:** `child_by_field_name("name")` returns `None` for many grammars, even when the node clearly has a name child.

**Root cause:** Different grammar authors use different conventions. Rust grammar doesn't define a "name" field on `function_item` — the identifier is just a child with kind `"identifier"`, not a named field.

**Pattern — field-name-first + kind-fallback:**

```rust
fn node_name(node: &tree_sitter::Node<'a>, source: &str) -> String {
    // Try field-based access (works for some grammars)
    if let Some(n) = node.child_by_field_name("name") {
        return node_text(&n, source);
    }
    // Fallback: find by kind
    if let Some(n) = find_child_by_kind(node, &[
        "identifier", "type_identifier", "field_identifier"
    ]) {
        return node_text(&n, source);
    }
    String::new()
}

fn find_child_by_kind<'a>(parent: &tree_sitter::Node<'a>, kinds: &[&str]) -> Option<tree_sitter::Node<'a>> {
    let mut c = parent.walk();
    if c.goto_first_child() {
        loop {
            if kinds.contains(&c.node().kind()) {
                return Some(c.node());
            }
            if !c.goto_next_sibling() { break; }
        }
    }
    None
}
```

### Per-Grammar Name Kinds

| Grammar | Function name | Struct/Type name | Method name | Trait/Interface name |
|---------|--------------|-------------------|--------------|---------------------|
| Rust | `identifier` | `type_identifier` | `identifier` (inside `impl`) | `type_identifier` |
| Go | `identifier` (field: "name" exists) | `identifier` (inside `type_spec`) | `identifier` (field: "name" exists) | N/A |
| Python | `identifier` (field: "name" works) | `identifier` (field: "name" works) | `identifier` (field: "name" works) | N/A |
| TypeScript | `identifier` (field: "name" works) | `identifier` (field: "name" works) | `property_identifier` | `type_identifier` |

## TypeScript Grammar: `export_statement` Wrapping

**Problem:** All exported declarations are wrapped in `export_statement` nodes. Direct children of root are `export_statement`, not `function_declaration`/`class_declaration`.

```
program
  export_statement          ← root child
    export                  ← keyword
    function_declaration    ← actual declaration inside
      function
      identifier            ← name here
```

**Fix:** Unwrap `export_statement` by recursing into non-keyword children:

```rust
"export_statement" => {
    let mut c = node.walk();
    if c.goto_first_child() {
        loop {
            let inner = c.node();
            if inner.kind() != "export" && inner.kind() != ";" {
                process_ts_node(&inner, source, file_path, nodes, edges);
            }
            if !c.goto_next_sibling() { break; }
        }
    }
}
```

Also: `const` in TS is `lexical_declaration` (not `variable_declaration`). Handle both.

## Go Grammar: `const_spec` / `var_spec` Nesting

**Problem:** `const_declaration` and `var_declaration` nodes contain an intermediate `const_spec`/`var_spec` child. The actual `identifier` (the name) is inside this spec node, NOT directly under the declaration.

```
const_declaration           ← root child kind
  const                     ← keyword
  const_spec                ← intermediate node — name is HERE
    identifier              ← "DefaultPort"
    =
    integer_literal

var_declaration             ← root child kind
  var                       ← keyword
  var_spec                  ← intermediate node — name is HERE
    identifier              ← "db"
    :
    type_identifier         ← "sql.DB"
```

**Fix:** After matching `const_declaration`/`var_declaration`, walk into children looking for `const_spec`/`var_spec`, then extract the name from there:

```rust
"const_declaration" => {
    let mut cc = child.walk();
    if cc.goto_first_child() {
        loop {
            if cc.node().kind() == "const_spec" {
                let name = node_name(&cc.node(), source);
                // ... create AstNode
            }
            if !cc.goto_next_sibling() { break; }
        }
    }
}
```

## Feature Flag Pattern

```toml
[features]
tree-sitter = [
    "dep:tree-sitter",
    "dep:tree-sitter-rust",
    "dep:tree-sitter-go",
    "dep:tree-sitter-python",
    "dep:tree-sitter-typescript",
]

[dependencies]
tree-sitter = { version = "0.26", optional = true }
tree-sitter-rust = { version = "0.24", optional = true }
# ...
```

Module gating: `#![cfg(feature = "tree-sitter")]` at top of file + `#[cfg(feature = "tree-sitter")] mod ast;` in parent.

Default build overhead: ~0.1s (zero tree-sitter code compiled). With feature: ~17s first build.

## Debugging Unknown Grammars

When you don't know the node kinds a grammar produces, add a temporary test that dumps the tree:

```rust
#[test]
fn debug_tree() {
    let code = r#"your code here"#;
    let lang = get_language("ts").unwrap();
    let tree = parse(code.as_bytes(), lang).unwrap();
    fn dump(node: &tree_sitter::Node, source: &str, depth: usize) {
        eprintln!("{}{} [{},{}]-[{},{}]",
            "  ".repeat(depth),
            node.kind(),
            node.start_position().row, node.start_position().column,
            node.end_position().row, node.end_position().column);
        let mut c = node.walk();
        if c.goto_first_child() {
            loop {
                dump(&c.node(), source, depth + 1);
                if !c.goto_next_sibling() { break; }
            }
        }
    }
    dump(&tree.root_node(), code, 0);
}
```

Remove before committing. Do NOT compile in `/tmp` — use the project's own target directory.
