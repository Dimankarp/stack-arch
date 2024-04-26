class InvalidIntLiteralError(Exception):
    def __init__(self, lit: int):
        super().__init__(f"Literal {lit} doesn't fit into 32bit signed integer format")


class ExpectedStringLiteralError(Exception):
    def __init__(self, token):
        super().__init__(f"No string literal provided after: {token.val} | (ln:{token.line}, wrd num:{token.num})")


class SallotQueryError(Exception):
    def __init__(self, token):
        super().__init__(f"Coudn't parse sallot query: {token.val} | (ln:{token.line}, wrd num:{token.num})")


class NestedWordError(Exception):
    def __init__(self, token):
        super().__init__(
            f"Nested word definition is forbidden, nested word definition: {token.val} | (ln:{token.line}, wrd num:{token.num})"
        )


class WordEndError(Exception):
    def __init__(self, token):
        super().__init__(
            f'Failed to end word definition at: {token.val} | (ln:{token.line}, wrd num:{token.num})| Check for opened ":", conditionals and loops'
        )


class BareConditionalError(Exception):
    def __init__(self, token):
        super().__init__(
            f"Conditionals are allowed only in word definitions: {token.val} | (ln:{token.line}, wrd num:{token.num})"
        )


class IfElseTreeError(Exception):
    def __init__(self, token):
        super().__init__(
            f'Failed to complete if-else-then tree: {token.val} | (ln:{token.line}, wrd num:{token.num})| Check for opened "if" '
        )


class BareBeginUntilError(Exception):
    def __init__(self, token):
        super().__init__(
            f"Begin-until is allowed only in word definitions: {token.val} | (ln:{token.line}, wrd num:{token.num})"
        )


class BeginUntilTreeError(Exception):
    def __init__(self, token):
        super().__init__(
            f'Failed to complete begin-until tree: {token.val} | (ln:{token.line}, wrd num:{token.num})| Check for opened "begin" '
        )


class BareDoLooplError(Exception):
    def __init__(self, token):
        super().__init__(
            f"Do-loop is allowed only in word definitions: {token.val} | (ln:{token.line}, wrd num:{token.num})"
        )


class LoopVarError(Exception):
    def __init__(self, token):
        super().__init__(
            f'Failed to insert iterating var: {token.val} | (ln:{token.line}, wrd num:{token.num})| Check for opened "do" '
        )


class DoLoopTreeError(Exception):
    def __init__(self, token):
        super().__init__(
            f'Failed to complete do-loop tree:  {token.val} | (ln:{token.line}, wrd num:{token.num})| Check for opened "do" '
        )


class UnknownWordError(Exception):
    def __init__(self, token):
        super().__init__(f"Unrecognized word: {token.val} | (ln:{token.line}, wrd num:{token.num})")


class UnclosedWordsError(Exception):
    def __init__(self, token_val):
        super().__init__(f"Some tokens weren't closed. Most recent opened: {token_val}")
