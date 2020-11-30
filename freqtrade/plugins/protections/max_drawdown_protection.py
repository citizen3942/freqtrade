
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

import pandas as pd

from freqtrade.data.btanalysis import calculate_max_drawdown
from freqtrade.persistence import Trade
from freqtrade.plugins.protections import IProtection, ProtectionReturn


logger = logging.getLogger(__name__)


class MaxDrawdown(IProtection):

    has_global_stop: bool = True
    has_local_stop: bool = False

    def __init__(self, config: Dict[str, Any], protection_config: Dict[str, Any]) -> None:
        super().__init__(config, protection_config)

        self._lookback_period = protection_config.get('lookback_period', 60)
        self._trade_limit = protection_config.get('trade_limit', 1)
        self._max_allowed_drawdown = protection_config.get('max_allowed_drawdown', 0.0)
        # TODO: Implement checks to limit max_drawdown to sensible values

    def short_desc(self) -> str:
        """
        Short method description - used for startup-messages
        """
        return (f"{self.name} - Max drawdown protection, stop trading if drawdown is > "
                f"{self._max_allowed_drawdown} within {self._lookback_period} minutes.")

    def _reason(self, drawdown: float) -> str:
        """
        LockReason to use
        """
        return (f'{drawdown} > {self._max_allowed_drawdown} in {self._lookback_period} min, '
                f'locking for {self._stop_duration} min.')

    def _max_drawdown(self, date_now: datetime, pair: str) -> ProtectionReturn:
        """
        Evaluate recent trades for drawdown ...
        """
        look_back_until = date_now - timedelta(minutes=self._lookback_period)
        filters = [
            Trade.is_open.is_(False),
            Trade.close_date > look_back_until,
        ]
        if pair:
            filters.append(Trade.pair == pair)
        trades = Trade.get_trades(filters).all()

        trades_df = pd.DataFrame(trades)

        if len(trades) < self._trade_limit:
            # Not enough trades in the relevant period
            return False, None, None

        # Drawdown is always positive
        drawdown, _, _ = calculate_max_drawdown(trades_df)

        if drawdown > self._max_allowed_drawdown:
            self.log_once(
                f"Trading for {pair} stopped due to {drawdown:.2f} < {self._max_allowed_drawdown} "
                f"within {self._lookback_period} minutes.", logger.info)
            until = self.calculate_lock_end(trades, self._stop_duration)

            return True, until, self._reason(drawdown)

        return False, None, None

    def global_stop(self, date_now: datetime) -> ProtectionReturn:
        """
        Stops trading (position entering) for all pairs
        This must evaluate to true for the whole period of the "cooldown period".
        :return: Tuple of [bool, until, reason].
            If true, all pairs will be locked with <reason> until <until>
        """
        return self._max_drawdown(date_now)

    def stop_per_pair(self, pair: str, date_now: datetime) -> ProtectionReturn:
        """
        Stops trading (position entering) for this pair
        This must evaluate to true for the whole period of the "cooldown period".
        :return: Tuple of [bool, until, reason].
            If true, this pair will be locked with <reason> until <until>
        """
        return False, None, None
