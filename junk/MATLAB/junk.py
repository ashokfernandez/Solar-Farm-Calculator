import PyExchangeRates
CURRENCY_EXCHANGE = PyExchangeRates.Exchange('843ce8fdc22c47779fb3040c2ba9a586')
a = CURRENCY_EXCHANGE.withdraw(100, 'USD')
type(a)
