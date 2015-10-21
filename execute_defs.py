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

standard_tokens = [t_trade_price, t_l_en, t_l_ex, t_s_en, t_s_ex, t_l, t_s]
type1_signal_tokens = [t_l_en, t_s_en]
type2_signal_tokens = [t_l, t_s]

all_tokens = standard_tokens + [t_high, t_low]


class SignalError(Exception):
    pass


class SignalMixingNotAllowed(SignalError):
    pass


def format_field(token, symbol=None):
    if symbol is None:
        return token
    else:
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
