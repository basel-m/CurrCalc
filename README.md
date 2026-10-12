# Currency Calculator

A small, fast currency calculator for Windows, in the spirit of the Windows 11 calculator.
Type amounts in different currencies and get the total in the currency you pick.

```
10SAR + 15USD + 27JOD   ->   55.75 USD
100 USD to SAR          ->   375.00 SAR   (one-off conversion)
$15 + €5 + 20 JOD       ->   works with symbols too
```

## Features
- Live result as you type, with a breakdown of each part and optional totals in other currencies
- Searchable output-currency picker with your 5 most recent currencies on top
- Currency list panel (**Alt+P**) with codes, names, rates and a daily up/down indicator
- History with rate dates, copy options (right-click) and delete
- Pin (always on top), dark/light/auto theme, remembers window size and position
- Works offline using the last downloaded rates

## Run
Requires Python 3.9+ on Windows (standard library only, nothing to install).
Double-click `currency_calc.pyw`.

## Build a standalone .exe
Double-click `build_exe.bat`. The app is created at `dist\CurrencyCalc.exe`.

## Rates
Rates come from [open.er-api.com](https://open.er-api.com), with a backup from
[fawazahmed0/currency-api](https://github.com/fawazahmed0/exchange-api). They are mid-market rates,
so they will be slightly better than what a bank or exchange office charges.

## Your data
Settings, history and cached rates are stored in `%APPDATA%\CurrencyCalc` (not in this folder).

## Version
See the version history at the top of `currency_calc.pyw`. Current: **1.6.6**
