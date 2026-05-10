#include "chibicc.h"

static int label_count = 1;
static FILE *output;
static Obj *current_fn;

static void gen_expr(Node *node);
static void gen_stmt(Node *node);

// The original x86-64 chibicc codegen evaluates everything onto the stack.
// The CY16 python prototype evaluates everything using a stack pointer `r15`
// but leaves the top-of-stack equivalent in a given register or pops it.
// Let's mimic the x86-64 style adapted for CY16.

// Pushes the given register to the stack
static void push(char *reg) {
  fprintf(output, "    mov [--r15], %s\n", reg);
}

// Pops the stack to the given register
static void pop(char *reg) {
  fprintf(output, "    mov %s, [r15++]\n", reg);
}

static void gen_addr(Node *node) {
  switch (node->kind) {
  case ND_VAR:
    if (node->var->is_local) {
      // For local variables, normally they are offset from frame pointer.
      // The python prototype mapped them to r0, r1, etc.
      // If we just map parameters to registers in CY16, taking the address of a register is invalid.
      // But let's assume we map parameters to offsets from a frame pointer (r14) if needed.
      // Actually, if it's just tests, maybe we don't need address of local variables yet.
      error_tok(node->tok, "not an lvalue / taking address of local not supported yet in simple CY16 codegen");
    } else {
      fprintf(output, "    mov r0, _%s\n", node->var->name); // wait, `mov r0, _sym` is not in ISA. 
      // ISA says: `mov rN, imm` or `mov rN, [addr]`
      // Labels are basically immediates. `mov r0, _%s` is valid assembler if it evaluates to an immediate.
      // BUT `mov [addr], imm` doesn't exist? Wait, `mov [addr], imm` DOES exist. `mov rN, imm` exists.
      fprintf(output, "    mov r0, _%s\n", node->var->name);
      push("r0");
    }
    return;
  case ND_DEREF:
    gen_expr(node->lhs);
    return;
  default:
    error_tok(node->tok, "not an lvalue");
  }
}

// Generate code for a given expression node. Result is left in `r0`.
static void gen_expr(Node *node) {
  switch (node->kind) {
  case ND_NUM:
    fprintf(output, "    mov r0, %ld\n", node->val);
    push("r0");
    return;
  case ND_NEG:
    gen_expr(node->lhs);
    pop("r0");
    fprintf(output, "    mov r1, r0\n");
    fprintf(output, "    mov r0, 0\n");
    fprintf(output, "    sub r0, r1\n");
    push("r0");
    return;
  case ND_VAR:
    if (node->var->is_local) {
      // Map locals to param registers if they are parameters (offset = param idx)
      // Actually, we can just say r0, r1, r2, r3
      int reg = node->var->offset / 8;
      fprintf(output, "    mov r0, r%d\n", reg);
      push("r0");
    } else {
      fprintf(output, "    mov r0, [_%s]\n", node->var->name);
      push("r0");
    }
    return;
  case ND_ASSIGN:
    gen_expr(node->rhs);
    if (node->lhs->kind == ND_VAR && node->lhs->var->is_local) {
      pop("r0");
      int reg = node->lhs->var->offset / 8;
      fprintf(output, "    mov r%d, r0\n", reg);
      push("r0");
    } else if (node->lhs->kind == ND_VAR && !node->lhs->var->is_local) {
      pop("r0");
      fprintf(output, "    mov [_%s], r0\n", node->lhs->var->name);
      push("r0");
    } else if (node->lhs->kind == ND_DEREF) {
      gen_expr(node->lhs->lhs); // evaluate pointer to stack
      pop("r8"); // pointer
      pop("r0"); // value
      fprintf(output, "    mov [r8], r0\n");
      push("r0");
    }
    return;
  case ND_DEREF:
    gen_expr(node->lhs);
    pop("r8");
    fprintf(output, "    mov r0, [r8]\n");
    push("r0");
    return;
  case ND_FUNCALL: {
    int nargs = 0;
    for (Node *arg = node->args; arg; arg = arg->next) {
      gen_expr(arg);
      nargs++;
    }
    for (int i = nargs - 1; i >= 0; i--) {
      pop(format("r%d", i));
    }
    
    if (node->lhs && node->lhs->kind == ND_VAR) {
        fprintf(output, "    call _%s\n", node->lhs->var->name);
    } else {
        // Fallback for function pointers or similar
        fprintf(output, "    call _%s\n", node->func_ty->name->str);
    }
    push("r0");
    return;
  }
  case ND_CAST:
    gen_expr(node->lhs);
    return;
  case ND_ADD:
  case ND_SUB:
  case ND_LT:
  case ND_LE:
  case ND_EQ:
  case ND_NE:
    gen_expr(node->lhs);
    gen_expr(node->rhs);
    pop("r1");
    pop("r0");
    
    if (node->kind == ND_ADD) {
      fprintf(output, "    add r0, r1\n");
    } else if (node->kind == ND_SUB) {
      fprintf(output, "    sub r0, r1\n");
    } else if (node->kind == ND_LT) {
      fprintf(output, "    cmp r0, r1\n");
      fprintf(output, "    jc L_%d\n", label_count);
      fprintf(output, "    mov r0, 0\n");
      fprintf(output, "    jmp L_%d\n", label_count+1);
      fprintf(output, "L_%d:\n", label_count++);
      fprintf(output, "    mov r0, 1\n");
      fprintf(output, "L_%d:\n", label_count++);
    } else if (node->kind == ND_LE) {
      fprintf(output, "    cmp r1, r0\n");
      fprintf(output, "    jc L_%d\n", label_count); // if r1 < r0 (so r0 > r1, false)
      fprintf(output, "    mov r0, 1\n");
      fprintf(output, "    jmp L_%d\n", label_count+1);
      fprintf(output, "L_%d:\n", label_count++);
      fprintf(output, "    mov r0, 0\n");
      fprintf(output, ".L%d:\n", label_count++);
    } else if (node->kind == ND_EQ) {
      fprintf(output, "    cmp r0, r1\n");
      fprintf(output, "    jz .L%d\n", label_count);
      fprintf(output, "    mov r0, 0\n");
      fprintf(output, "    jmp .L%d\n", label_count+1);
      fprintf(output, ".L%d:\n", label_count++);
      fprintf(output, "    mov r0, 1\n");
      fprintf(output, ".L%d:\n", label_count++);
    } else if (node->kind == ND_NE) {
      fprintf(output, "    cmp r0, r1\n");
      fprintf(output, "    jz .L%d\n", label_count);
      fprintf(output, "    mov r0, 1\n");
      fprintf(output, "    jmp .L%d\n", label_count+1);
      fprintf(output, ".L%d:\n", label_count++);
      fprintf(output, "    mov r0, 0\n");
      fprintf(output, ".L%d:\n", label_count++);
    }
    push("r0");
    return;
  }
  
  error_tok(node->tok, "invalid expression");
}

static void gen_stmt(Node *node) {
  switch (node->kind) {
  case ND_BLOCK:
    for (Node *n = node->body; n; n = n->next)
      gen_stmt(n);
    return;
  case ND_RETURN:
    if (node->lhs) {
      gen_expr(node->lhs);
      pop("r0");
    }
    fprintf(output, "    jmp L_return_%s\n", current_fn->name);
    return;
  case ND_EXPR_STMT:
    gen_expr(node->lhs);
    pop("r0"); // discard result
    return;
  case ND_IF: {
    int c = label_count++;
    gen_expr(node->cond);
    pop("r0");
    fprintf(output, "    cmp r0, 0\n");
    if (node->els) {
      fprintf(output, "    jz L_else_%d\n", c);
      gen_stmt(node->then);
      fprintf(output, "    jmp L_end_%d\n", c);
      fprintf(output, "L_else_%d:\n", c);
      gen_stmt(node->els);
      fprintf(output, "L_end_%d:\n", c);
    } else {
      fprintf(output, "    jz L_end_%d\n", c);
      gen_stmt(node->then);
      fprintf(output, "L_end_%d:\n", c);
    }
    return;
  }
  case ND_FOR: {
    int c = label_count++;
    if (node->init)
      gen_stmt(node->init);
    fprintf(output, "L_begin_%d:\n", c);
    if (node->cond) {
      gen_expr(node->cond);
      pop("r0");
      fprintf(output, "    cmp r0, 0\n");
      fprintf(output, "    jz L_end_%d\n", c);
    }
    gen_stmt(node->then);
    if (node->inc) {
      gen_expr(node->inc);
      pop("r0");
    }
    fprintf(output, "    jmp L_begin_%d\n", c);
    fprintf(output, "L_end_%d:\n", c);
    return;
  }
  }
  
  error_tok(node->tok, "invalid statement");
}

void codegen(Obj *prog, FILE *out) {
  output = out;

  for (Obj *fn = prog; fn; fn = fn->next) {
    if (fn->is_function) {
      if (!fn->is_definition) continue;

      current_fn = fn;
      fprintf(output, ".global _%s\n", fn->name);
      fprintf(output, "_%s:\n", fn->name);
      
      int param_idx = 0;
      for (Obj *var = fn->params; var; var = var->next) {
        var->offset = param_idx * 8; 
        param_idx++;
      }
      
      gen_stmt(fn->body);
      
      fprintf(output, "L_return_%s:\n", fn->name);
      fprintf(output, "    ret\n");
      fprintf(output, "\n");
    } else {
        // Global variables
        if (!strncmp(fn->name, ".L", 2)) continue;
        if (fn->is_tentative) continue;

        fprintf(output, ".global _%s\n", fn->name);
        fprintf(output, "_%s:\n", fn->name);
        if (fn->init_data) {
          for (int i = 0; i < fn->ty->size; i++) {
             if (i % 2 == 0 && i + 1 < fn->ty->size) {
                 fprintf(output, "    .word %d\n", (fn->init_data[i] & 0xFF) | ((fn->init_data[i+1] & 0xFF) << 8));
                 i++;
             } else {
                 fprintf(output, "    .byte %d\n", fn->init_data[i]);
             }
          }
        } else {
          fprintf(output, "    .word 0\n"); // Just a placeholder word
        }
    }
  }
}

int align_to(int n, int align) {
  return (n + align - 1) / align * align;
}
