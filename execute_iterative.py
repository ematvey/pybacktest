tok_high = 'high'
tok_low = 'low'

tok_lens = 'long_entry_stop_price'
tok_lenl = 'long_entry_limit_price'
tok_lexs = 'long_exit_stop_price'
tok_lexl = 'long_exit_limit_price'
tok_sens = 'short_entry_stop_price'
tok_senl = 'short_entry_limit_price'
tok_sexs = 'short_exit_stop_price'
tok_sexl = 'short_exit_limit_price'

conditional_column_tokens = [tok_lens, tok_lenl, tok_lexs, tok_lenl, tok_sens, tok_senl, tok_sexs, tok_sexl]


def conditional_signals(signals):
    for f in conditional_column_tokens:
        for column in signals:
            if column.endswith(f):
                return True
    return False


def iterative_execute(data, signals):
    raise NotImplementedError('strategy requires iterative execution which is not implented yet')
