from collections import defaultdict

t_high = 'high'
t_low = 'low'
t_trade_price = 'trade_price'

t_l = 'long'
t_s = 'short'
t_l_en = 'long_entry'
t_s_en = 'short_entry'
t_l_ex = 'long_exit'
t_s_ex = 'short_exit'

t_l_en_s = 'long_entry_stop_price'
t_s_en_s = 'short_entry_stop_price'
t_l_ex_s = 'long_exit_stop_price'
t_s_ex_s = 'short_exit_stop_price'

t_l_en_l = 'long_entry_limit_price'
t_s_en_l = 'short_entry_limit_price'
t_l_ex_l = 'long_exit_limit_price'
t_s_ex_l = 'short_exit_limit_price'

standard_tokens = [t_trade_price, t_l_en, t_l_ex, t_s_en, t_s_ex, t_l, t_s]
conditional_column_tokens = [t_l_en_s, t_l_en_l, t_l_ex_s, t_l_en_l, t_s_en_s, t_s_en_l, t_s_ex_s, t_s_ex_l]
type1_signal_tokens = [t_l_en, t_s_en]
type2_signal_tokens = [t_l, t_s]

all_tokens = conditional_column_tokens + standard_tokens + [t_high, t_low]


class SignalError(Exception):
    pass


class SignalMixingNotAllowed(SignalError):
    pass


def format_multiasset_field(symbol, token):
    return symbol + '_' + token


def parse_signals_dataframe(signals, tokens):
    fields = defaultdict(dict)
    cols = []

    single_asset_mode = False
    multi_asset_mode = False

    for column in list(signals):
        for token in tokens:
            if column == token:
                if multi_asset_mode:
                    raise SignalMixingNotAllowed()
                cols.append(column)
                single_asset_mode = True
            elif column.endswith('_' + token):
                if single_asset_mode:
                    raise SignalMixingNotAllowed()
                fields[column.replace('_' + token, '')][column] = token
                multi_asset_mode = True

    if single_asset_mode:
        return signals[cols]
    elif multi_asset_mode:
        return {symbol: {col_new: signals[col_old] for col_old, col_new in colmap.items()}
                for symbol, colmap in fields.items()}
    else:
        raise SignalError()
