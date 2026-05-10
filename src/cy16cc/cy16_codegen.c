#include "chibicc.h"

static int label_count = 1;
static FILE *output;
static Obj *current_fn;

static void gen_expr(Node *node);
static void gen_stmt(Node *node);

// Pushes the given register to the stack
static void push(char *reg) {
  fprintf(output, "    mov [--r15], %s\n", reg);
}

// Pops the stack to the given register
static void pop(char *reg) {
  fprintf(output, "    mov %s, [r15++]\n", reg);
}

static bool is_param_obj(Obj *fn, Obj *var) {
  for (Obj *param = fn->params; param; param = param->next) {
    if (param == var)
      return true;
  }
  return false;
}

static bool const_int_node(Node *node, long *value) {
  while (node && node->kind == ND_CAST)
    node = node->lhs;
  if (!node || node->kind != ND_NUM)
    return false;
  *value = node->val;
  return true;
}

static bool const_mul_node(Node *node, long *value) {
  long lhs;
  long rhs;
  if (!node || node->kind != ND_MUL)
    return false;
  if (!const_int_node(node->lhs, &lhs) || !const_int_node(node->rhs, &rhs))
    return false;
  *value = lhs * rhs;
  return true;
}

static void gen_addr(Node *node) {
  switch (node->kind) {
  case ND_VAR:
    if (node->var->is_local) {
      if (node->var->offset >= 0) {
        error_tok(node->tok, "taking address of register-mapped parameter not supported");
      }
      fprintf(output, "    mov r0, r14\n");
      fprintf(output, "    sub r0, %d\n", -node->var->offset);
      push("r0");
    } else {
      fprintf(output, "    mov r0, _%s\n", node->var->name);
      push("r0");
    }
    return;
  case ND_DEREF:
    gen_expr(node->lhs);
    return;
  case ND_MEMBER:
    gen_addr(node->lhs);
    pop("r0");
    if (node->member->offset > 0) {
      fprintf(output, "    addi r0, %d\n", node->member->offset);
    }
    push("r0");
    return;
  default:
    error_tok(node->tok, "not an lvalue (kind %d)", node->kind);
  }
}

// Generate code for a given expression node.
static void gen_expr(Node *node) {
  switch (node->kind) {
  case ND_NULL_EXPR:
    return;
  case ND_NUM:
    fprintf(output, "    mov r0, %ld\n", node->val);
    push("r0");
    return;
  case ND_MEMZERO:
    if (!node->var || !node->var->is_local || node->var->offset >= 0) {
      error_tok(node->tok, "unsupported memzero target");
    }
    for (int i = 0; i < node->var->ty->size; i += 2) {
      fprintf(output, "    mov r8, r14\n");
      fprintf(output, "    sub r8, %d\n", -node->var->offset - i);
      fprintf(output, "    mov [r8], 0\n");
    }
    fprintf(output, "    mov r0, 0\n");
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
    if (node->var->ty->kind == TY_ARRAY) {
       // Array to pointer conversion: use address
       gen_addr(node);
       return;
    }
    if (node->var->is_local) {
      if (node->var->offset >= 0) {
        int reg = node->var->offset / 2;
        fprintf(output, "    mov r0, r%d\n", reg);
      } else {
        fprintf(output, "    mov r8, r14\n");
        fprintf(output, "    sub r8, %d\n", -node->var->offset);
        fprintf(output, "    mov r0, [r8]\n");
      }
      push("r0");
    } else {
      fprintf(output, "    mov r0, [_%s]\n", node->var->name);
      push("r0");
    }
    return;
  case ND_MEMBER: {
    gen_addr(node);
    pop("r8");
    fprintf(output, "    mov r0, [r8]\n");
    push("r0");
    return;
  }
  case ND_ADDR:
    gen_addr(node->lhs);
    return;
  case ND_DEREF:
    gen_expr(node->lhs);
    pop("r8");
    fprintf(output, "    mov r0, [r8]\n");
    push("r0");
    return;
  case ND_ASSIGN:
    if (node->lhs->kind == ND_VAR && node->lhs->var->is_local && node->lhs->var->offset >= 0) {
      gen_expr(node->rhs);
      pop("r0");
      int reg = node->lhs->var->offset / 2;
      fprintf(output, "    mov r%d, r0\n", reg);
      push("r0");
    } else {
      gen_addr(node->lhs);
      gen_expr(node->rhs);
      pop("r0");
      pop("r8");
      fprintf(output, "    mov [r8], r0\n");
      push("r0");
    }
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
    
    if (node->lhs->kind == ND_VAR) {
        fprintf(output, "    call _%s\n", node->lhs->var->name);
    } else {
        gen_expr(node->lhs);
        pop("r8");
        fprintf(output, "    call [r8]\n");
    }
    push("r0");
    return;
  }
  case ND_CAST:
    gen_expr(node->lhs);
    return;
  case ND_COMMA:
    gen_expr(node->lhs);
    if (node->lhs->kind != ND_NULL_EXPR)
      pop("r0");
    gen_expr(node->rhs);
    return;
  case ND_NOT: {
    int c = label_count++;
    gen_expr(node->lhs);
    pop("r0");
    fprintf(output, "    cmp r0, 0\n");
    fprintf(output, "    jz L_true_%d\n", c);
    fprintf(output, "    mov r0, 0\n");
    fprintf(output, "    jmp L_done_%d\n", c);
    fprintf(output, "L_true_%d:\n", c);
    fprintf(output, "    mov r0, 1\n");
    fprintf(output, "L_done_%d:\n", c);
    push("r0");
    return;
  }
  case ND_BITNOT:
    gen_expr(node->lhs);
    pop("r0");
    fprintf(output, "    xor r0, 0xffff\n");
    push("r0");
    return;
  case ND_COND: {
    int c = label_count++;
    gen_expr(node->cond);
    pop("r0");
    fprintf(output, "    cmp r0, 0\n");
    fprintf(output, "    jz L_else_%d\n", c);
    gen_expr(node->then);
    fprintf(output, "    jmp L_done_%d\n", c);
    fprintf(output, "L_else_%d:\n", c);
    gen_expr(node->els);
    fprintf(output, "L_done_%d:\n", c);
    return;
  }
  case ND_ADD:
  case ND_SUB:
  case ND_MUL:
  case ND_BITAND:
  case ND_BITOR:
  case ND_BITXOR:
  case ND_SHL:
  case ND_SHR:
  case ND_LT:
  case ND_LE:
  case ND_EQ:
  case ND_NE:
    if (node->kind == ND_MUL) {
      long folded;
      if (const_mul_node(node, &folded)) {
        fprintf(output, "    mov r0, %ld\n", folded);
        push("r0");
        return;
      }
    }

    gen_expr(node->lhs);
    gen_expr(node->rhs);
    pop("r1");
    pop("r0");
    
    if (node->kind == ND_ADD) {
      fprintf(output, "    add r0, r1\n");
    } else if (node->kind == ND_SUB) {
      fprintf(output, "    sub r0, r1\n");
    } else if (node->kind == ND_MUL) {
      long n;
      if (const_int_node(node->rhs, &n)) {
        /* r0 already contains lhs. */
      } else if (const_int_node(node->lhs, &n)) {
        fprintf(output, "    mov r0, r1\n");
      } else {
        error_tok(node->tok, "dynamic MUL not supported");
      }
      if (n == 0) {
        fprintf(output, "    mov r0, 0\n");
      } else if (n == 1) {
        /* r0 already contains lhs. */
      } else if (n == 2) {
        fprintf(output, "    shl r0, 1\n");
      } else if (n == 4) {
        fprintf(output, "    shl r0, 2\n");
      } else if (n > 1 && n <= 16) {
        fprintf(output, "    mov r2, r0\n");
        for (long i = 1; i < n; i++) {
          fprintf(output, "    add r0, r2\n");
        }
      } else {
        error_tok(node->tok, "constant MUL out of CY16 v0 range");
      }
    } else if (node->kind == ND_BITAND) {
      fprintf(output, "    and r0, r1\n");
    } else if (node->kind == ND_BITOR) {
      fprintf(output, "    or r0, r1\n");
    } else if (node->kind == ND_BITXOR) {
      fprintf(output, "    xor r0, r1\n");
    } else if (node->kind == ND_SHL) {
      // RHS must be constant for now?
      if (node->rhs->kind == ND_NUM) {
          fprintf(output, "    shl r0, %ld\n", node->rhs->val);
      } else {
          error_tok(node->tok, "dynamic SHL not supported");
      }
    } else if (node->kind == ND_SHR) {
      if (node->rhs->kind == ND_NUM) {
          fprintf(output, "    shr r0, %ld\n", node->rhs->val);
      } else {
          error_tok(node->tok, "dynamic SHR not supported");
      }
    } else if (node->kind == ND_LT) {
      int c = label_count++;
      fprintf(output, "    cmp r0, r1\n");
      fprintf(output, "    jc L_true_%d\n", c);
      fprintf(output, "    mov r0, 0\n");
      fprintf(output, "    jmp L_done_%d\n", c);
      fprintf(output, "L_true_%d:\n", c);
      fprintf(output, "    mov r0, 1\n");
      fprintf(output, "L_done_%d:\n", c);
    } else if (node->kind == ND_LE) {
      int c = label_count++;
      fprintf(output, "    cmp r1, r0\n");
      fprintf(output, "    jc L_false_%d\n", c);
      fprintf(output, "    mov r0, 1\n");
      fprintf(output, "    jmp L_done_%d\n", c);
      fprintf(output, "L_false_%d:\n", c);
      fprintf(output, "    mov r0, 0\n");
      fprintf(output, "L_done_%d:\n", c);
    } else if (node->kind == ND_EQ) {
      int c = label_count++;
      fprintf(output, "    cmp r0, r1\n");
      fprintf(output, "    jz L_true_%d\n", c);
      fprintf(output, "    mov r0, 0\n");
      fprintf(output, "    jmp L_done_%d\n", c);
      fprintf(output, "L_true_%d:\n", c);
      fprintf(output, "    mov r0, 1\n");
      fprintf(output, "L_done_%d:\n", c);
    } else if (node->kind == ND_NE) {
      int c = label_count++;
      fprintf(output, "    cmp r0, r1\n");
      fprintf(output, "    jnz L_true_%d\n", c);
      fprintf(output, "    mov r0, 0\n");
      fprintf(output, "    jmp L_done_%d\n", c);
      fprintf(output, "L_true_%d:\n", c);
      fprintf(output, "    mov r0, 1\n");
      fprintf(output, "L_done_%d:\n", c);
    }
    push("r0");
    return;
  case ND_LOGAND: {
    int c = label_count++;
    gen_expr(node->lhs);
    pop("r0");
    fprintf(output, "    cmp r0, 0\n");
    fprintf(output, "    jz L_false_%d\n", c);
    gen_expr(node->rhs);
    pop("r0");
    fprintf(output, "    cmp r0, 0\n");
    fprintf(output, "    jz L_false_%d\n", c);
    fprintf(output, "    mov r0, 1\n");
    fprintf(output, "    jmp L_done_%d\n", c);
    fprintf(output, "L_false_%d:\n", c);
    fprintf(output, "    mov r0, 0\n");
    fprintf(output, "L_done_%d:\n", c);
    push("r0");
    return;
  }
  case ND_LOGOR: {
    int c = label_count++;
    gen_expr(node->lhs);
    pop("r0");
    fprintf(output, "    cmp r0, 0\n");
    fprintf(output, "    jnz L_true_%d\n", c);
    gen_expr(node->rhs);
    pop("r0");
    fprintf(output, "    cmp r0, 0\n");
    fprintf(output, "    jnz L_true_%d\n", c);
    fprintf(output, "    mov r0, 0\n");
    fprintf(output, "    jmp L_done_%d\n", c);
    fprintf(output, "L_true_%d:\n", c);
    fprintf(output, "    mov r0, 1\n");
    fprintf(output, "L_done_%d:\n", c);
    push("r0");
    return;
  }
  case ND_DIV:
  case ND_MOD:
    error_tok(node->tok, "DIV/MOD not yet implemented for CY16");
    return;
  default:
    error_tok(node->tok, "invalid expression (kind %d)", node->kind);
  }
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
    if (node->lhs) {
      gen_expr(node->lhs);
      if (node->lhs->kind != ND_NULL_EXPR)
        pop("r0"); 
    }
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
  default:
    error_tok(node->tok, "invalid statement (kind %d)", node->kind);
  }
}

static void assign_lvar_offsets(Obj *prog) {
  for (Obj *fn = prog; fn; fn = fn->next) {
    if (!fn->is_function) continue;
    
    int gp = 0;
    for (Obj *var = fn->params; var; var = var->next) {
      if (gp < 8) {
        var->offset = gp * 2;
        gp++;
      } else {
        error_tok(var->tok, "too many parameters for CY16 v0");
      }
    }
    
    int offset = 0;
    for (Obj *var = fn->locals; var; var = var->next) {
      if (is_param_obj(fn, var))
        continue;
      offset += var->ty->size;
      offset = align_to(offset, var->ty->align);
      var->offset = -offset;
    }
    fn->stack_size = align_to(offset, 2);
  }
}

void codegen(Obj *prog, FILE *out) {
  output = out;
  assign_lvar_offsets(prog);

  for (Obj *fn = prog; fn; fn = fn->next) {
    if (fn->is_function) {
      if (!fn->is_definition) continue;

      current_fn = fn;
      fprintf(output, ".global _%s\n", fn->name);
      fprintf(output, "_%s:\n", fn->name);
      
      push("r14");
      fprintf(output, "    mov r14, r15\n");
      if (fn->stack_size > 0) {
        fprintf(output, "    sub r15, %d\n", fn->stack_size);
      }
      
      gen_stmt(fn->body);
      
      fprintf(output, "L_return_%s:\n", fn->name);
      fprintf(output, "    mov r15, r14\n");
      pop("r14");
      fprintf(output, "    ret\n");
      fprintf(output, "\n");
    } else {
        if (!strncmp(fn->name, ".L", 2)) continue;

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
          for (int i = 0; i < fn->ty->size; i+=2) {
              fprintf(output, "    .word 0\n");
          }
        }
    }
  }
}

int align_to(int n, int align) {
  return (n + align - 1) / align * align;
}
