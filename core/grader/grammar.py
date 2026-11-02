"""LALR(1) grammar for the answer syntax (docs/card-format.md, "Answer types").

Terminals come from our own tokenizer (core/grader/tokens.py), which has already
resolved words (FUNC, VAR, CONST, ...), absolute-value bars and vector brackets, and
checked where implicit multiplication may happen. Repetition is written with `*` so
long sums and products stay flat (no deep recursion in the tree).

Kept in Python (not a .lark file) so the frozen .app needs no extra data files.
"""

GRAMMAR = r"""
%declare NUMBER VAR CONST FUNC DNE NONE OR AND UNION
%declare LPAREN RPAREN LBRACK RBRACK LBRACE RBRACE ABS_OPEN ABS_CLOSE LANGLE RANGLE
%declare COMMA SEMI PLUS MINUS STAR SLASH CARET EQ LT LE GT GE NE DEGREE

start: alternative (SEMI alternative)*
alternative: item (COMMA item)*

?item: disj
     | setexpr
     | vector
     | matrix
     | DNE                                   -> dne

?disj: conj (OR conj)*
?conj: chain (AND chain)*
?chain: sum (relop sum)*
relop: EQ | LT | LE | GT | GE | NE

?setexpr: setatom (UNION setatom)*
?setatom: bracketed
        | setlit
        | NONE                               -> none
bracketed: LPAREN sum (COMMA sum)+ close
         | LBRACK sum (COMMA sum)+ close
close: RPAREN | RBRACK
setlit: LBRACE [sum (COMMA sum)*] RBRACE
vector: LANGLE sum (COMMA sum)* RANGLE
matrix: LBRACK row (COMMA row)* RBRACK
row: LBRACK sum (COMMA sum)* RBRACK

sum: signed (addop signed)*
addop: PLUS | MINUS
?signed: MINUS signed                        -> neg
       | PLUS signed                         -> pos
       | product
product: power (mulop signed_power | power)*
mulop: STAR | SLASH
?signed_power: MINUS signed_power            -> neg
             | PLUS signed_power             -> pos
             | power
?power: postfix
      | postfix CARET exponent               -> pow
?exponent: MINUS exponent                    -> neg
         | PLUS exponent                     -> pos
         | power
?postfix: primary
        | primary DEGREE                     -> degree
?primary: NUMBER                             -> number
        | VAR                                -> var
        | CONST                              -> const
        | FUNC LPAREN sum (COMMA sum)* RPAREN -> call
        | FUNC ABS_OPEN sum ABS_CLOSE        -> call_abs
        | LPAREN sum RPAREN                  -> group
        | ABS_OPEN sum ABS_CLOSE             -> abs
"""
