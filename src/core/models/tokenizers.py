

class Tokenizer:
    def count_tokens(self, s: str) -> int:
        raise NotImplementedError("Not implemented")


class TokenizerSimplified(Tokenizer):
    def count_tokens(self, s: str) -> int:
        if not len(s):
            return 0
        return int(len(s) / 4.)


def resolve_tokenizer(tok_name: str) -> Tokenizer:
    if tok_name == "simplified":
        return TokenizerSimplified()
    else:
        raise ValueError(f"tokenizer {tok_name} does not exist")
