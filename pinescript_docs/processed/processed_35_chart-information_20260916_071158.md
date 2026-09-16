## Introduction
Scripts can retrieve multiple types of information about the current chart and its dataset by using a subset of built-in variables. The chart data that scripts can access using these variables includes the following:
  * The available prices and volume
  * The chart’s timeframe
  * The dataset’s session information
      * The chart’s type and color


The following sections on this page list the variables that can access chart information, along with examples demonstrating how to use them. To learn more about all the built-in variables available in Pine Script®, refer to the Built-ins page in this manual and the “Variables” section of our Reference Manual. 
NoteSeveral variables described on this page behave differently in _data requests_. For most of these variables, if a script uses them in the `expression` arguments of `request.*()` calls, or if the script is an indicator that includes a `timeframe` argument in its declaration statement, they represent information from the _requested dataset_ rather than the current chart. For example, if a request.security() call includes `"NASDAQ:AAPL"` as its `symbol` argument, the value of the syminfo.prefix variable is `"NASDAQ"` inside that request’s context, regardless of the symbol used by the current chart. Likewise, the close value inside the request refers to the share price for NASDAQ:AAPL stock. See the Other timeframes and data page to learn more.

## Prices and volume
Most chart datasets include _OHLCV_ (open, high, low, close, and volume) values for each available bar. The chart displays the _final_ values for each _closed_ bar, and the _developing_ values for an _open realtime bar_. See the section The basics in the Execution model page to learn more about this behavior.
The variables that store final or developing OHLCV data for the current bar are as follows:
          

Pine Script also includes multiple variables that store values _derived_ from available OHLC data, including the following:
        

Note
If a bar contains only a _single_ price rather than complete OHLC prices, each of these price-based variables stores that value. If no volume data is available for a bar, the value of the volume variable is na.
  

Some chart types do not _display_ OHLC prices, but their datasets still _contain_ those prices. For example, a line chart displays only one price per bar. However, the variables that access bar prices still use the available OHLC values from the underlying dataset.
  

On _non-standard_ charts, such as Heikin Ashi or Renko, variables that access price data store the chart’s _synthetic_ prices, not the instrument’s _actual_ prices. Therefore, logic that uses these variables can yield different results on these charts.
On tick charts that use the “1T” timeframe, scripts can also use the bid and ask variables to access the current _bid and ask_ prices. The _bid_ is the _highest_ price that an active buyer is willing to pay for the instrument at its current value, and the _ask_ is the _lowest_ price that an active seller is willing to accept at the current value. On timeframes higher than “1T”, the value of these variables is na.
All of these price and volume variables are of the “series float” qualified type, because they store floating-point values that can vary from bar to bar. Scripts can use the [`[]` history-referencing operator] to retrieve the past values of these variables from previous bars. For example, the expression `close[1]` retrieves the _previous bar’s_ closing price. Multiple built-in functions also access past values internally. For instance, the expression `ta.change(ohlc4, 20)` is equivalent to `ohlc4 - ohlc4[20]`; both expressions calculate the difference between the current ohlc4 value and the value from _20 bars back_.
The following example uses the prices and volume of current and previous bars on the chart to calculate a condition for a dynamic background color. The script colors the chart’s background green only if the current values of the volume and close variables are greater than the previous values, and the current close value is greater than its 10-bar moving average. The script also plots the moving average for visual reference:
!image
Pine Script®
Copied
`//@version=6  
indicator("Price and volume variables demo", overlay = true, behind_chart = false)  
  
//@variable The 10-bar moving average of the `close` series.  
float ma = ta.sma(close, 10)  
  
//@variable Is `true` if the current volume is greater than the previous bar's volume, and `false` otherwise.   
bool risingVolume = volume > volume[1]  
//@variable Is `true` if the current price is greater than the closing price of the previous bar, and `false` otherwise.   
bool risingPrice = close > close[1]  
//@variable Is `true` if the current price is above the current `ma` value, and `false` otherwise.   
bool closeAboveMA = close > ma  
  
// Plot the `ma` series on the chart.   
plot(ma, "10-bar MA", linewidth = 3)  
// Highlight the background in green when all three conditions are true.  
bgcolor(risingVolume and risingPrice and closeAboveMA ? #4caf5080 : na, title = "Condition highlight")  
`

## Chart timeframe
Scripts can retrieve the _timeframe_ of the current chart by using the timeframe.period or timeframe.main_period variable. Both variables hold a “simple string” value representing the analyzed timeframe:
  * The value of the timeframe.period variable represents the timeframe of a specific context. If used outside the `expression` argument of a `request.*()` call, the value represents the _chart’s timeframe_ , or the script’s _main timeframe_ if the script is an indicator whose declaration statement includes a `timeframe` argument. When used in the `expression` argument of a `request.*()` call, the value represents the timeframe of the _requested dataset_.
  * The value of the timeframe.main_period variable _always_ represents the chart’s timeframe or the script’s main timeframe, even if the script uses it inside a `request.*()` call. This behavior is often useful for nested requests that require information from the chart’s timeframe in their logic.


The timeframe strings stored by these variables contain a number representing a _quantity (multiplier)_ followed by a single letter representing the _time unit_. For all intraday timeframes that Pine expresses in _minutes_ , the timeframe string contains a multiplier _without_ a unit postfix. For example, `"1D"` represents the one-day timeframe, `"5"` represents the five-minute timeframe, `"60"` represents the one-hour (60-minute) timeframe, and `"3M"` represents the three-month timeframe. See the Timeframe string specifications section of the Timeframes page to learn more.
Multiple built-in functions feature a `timeframe` parameter that accepts a valid timeframe string. Scripts can pass the timeframe.period or timeframe.main_period variable to this parameter to use the chart’s timeframe in the calculations.
For example, the following script uses the timeframe.period variable in calls to the `time()` and `time_close()` functions to retrieve the UNIX timestamps of the current bar’s opening time and the previous bar’s closing time, then measures the difference between the two timestamps to identify time gaps in the chart’s bars. It also uses the variable in a call to timeframe.in_seconds() to retrieve the typical number of seconds represented by the timeframe, then uses the result to express the time difference as an approximate number of bars. Each time that the script detects a gap, it displays formatted text containing the gap’s size in minutes and bars, the timeframe.period value, and the number of bars elapsed since the previous gap in a label at the current bar’s high:
!image
Pine Script®
Copied
`//@version=6  
indicator("`timeframe.period` demo", overlay = true, behind_chart = false)  
  
//@variable The previous bar's closing UNIX timestamp.  
int prevCloseTime = time_close(timeframe = timeframe.period, timeframe_bars_back = 1)  
//@variable The current bar's opening UNIX timestamp.  
int currOpenTime = time(timeframe = timeframe.period)  
  
//@variable The number of seconds elapsed between the `prevCloseTime` and `currOpenTime` timestamps.  
int timeDiff = (currOpenTime - prevCloseTime) / 1000  
//@variable The approximate span of the time difference in bars.  
int gapBarLength = int(timeDiff / timeframe.in_seconds(timeframe.period))  
//@variable Is `true` if the difference is greater than zero.  
bool hasGap = timeDiff > 0  
//@variable The number of bars since the `hasGap` value was last `true`.   
int barsSinceLastGap = ta.barssince(hasGap)  
  
// If a time gap occurs, display the gap in minutes, the current timeframe, and the bars since the previous gap  
// in a label at the current bar's high.  
if hasGap  
    label.new(  
        bar_index, high,   
        text = str.format(  
            "{0}-minute gap (~{1} bars) on ''{2}'' timeframe\nBars since previous gap: {3}",   
            timeDiff / 60, gapBarLength, timeframe.period, barsSinceLastGap[1] + 1  
        )  
    )  
`
Note that:
  * Programmers can also use an _empty string_ (`""`) as a `timeframe` argument to specify the same timeframe as timeframe.period. For instance, our example script yields the same results if we use `""` instead of the variable in the time(), time_close(), and timeframe.in_seconds() calls.


Scripts can use the timeframe.multiplier variable to retrieve a “simple int” value representing the _multiplier_ of the timeframe referenced by timeframe.period. For example, if the timeframe is “2D”, the timeframe.multiplier value is `2`. If the timeframe is “30S”, the variable’s value is `30`.
The following `timeframe.*` variables store “simple bool” values to indicate the _unit_ of the timeframe referenced by timeframe.period:
                

The example below uses these variables to construct a custom representation of the chart’s timeframe. On the first bar, the script uses multiple `timeframe.is*` variables in a switch statement to retrieve a string representing the chart timeframe’s unit, then creates a formatted string using the result and the value of timeframe.multiplier. It displays the final text in a single-cell table in the chart’s top-right corner:
!image
Pine Script®
Copied
`//@version=6  
indicator("Timeframe multiplier and unit variables demo", overlay = true, behind_chart = false)  
  
//@variable References a single-cell `table` object that displays the chart's timeframe in the top-right corner.  
var table displayTable = table.new(position.top_right, 1, 1, color.blue)  
  
if barstate.isfirst  
    //@variable A string that describes the unit of the chart's timeframe.  
    string unitsStr = switch  
        timeframe.isticks   => "tick"  
        timeframe.isseconds => "second"  
        timeframe.isminutes => "minute"  
        timeframe.isdaily   => "day"  
        timeframe.isweekly  => "week"  
        => "month"  
    //@variable A formatted string that contains the timeframe's multiplier and unit descriptor.  
    string displayStr = str.format(  
        "Chart timeframe: {0,number,#} {1}{2}",   
        timeframe.multiplier, unitsStr, timeframe.multiplier > 1 ? "s" : ""  
    )  
    // Initialize the table's cell to display the text from the `displayStr` value.   
    displayTable.cell(0, 0, displayStr, text_color = color.white, text_size = 24)  
`
Refer to the Timeframes page to learn more about the `timeframe.*` built-ins and how to use them.

## Session information
Pine Script includes multiple built-in variables that can retrieve information about an intraday dataset’s _session_ , which refers to the days and the times of day in which trading data is available. These variables represent session information for the current chart’s dataset, or for a requested dataset if the script uses them in the `expression` argument of a `request.*()` function call.
Scripts can access the named session for the current chart’s dataset by using the syminfo.session variable. The variable holds a “simple string” value representing the session’s name. In most cases, the string matches the value of either of the following `session.*` constants by default:
    

The syminfo.session variable can also hold _other_ unique strings for specific subsessions defined by the exchange or data provider. For instance, the value is `"us_regular"` on a CME futures chart that uses the RTH session, and `"24h"` on an equities chart that includes _overnight (24-hour)_ sessions. Refer to the Retrieving named sessions section of the Sessions page to learn more about named session strings.
Programmers can use the string from this variable to create session-specific logic in their scripts, or pass the string to the `session` parameter of the ticker.new() or ticker.modify() functions to create ticker identifiers for requesting data using the same session as the chart. See the Custom contexts section of the Other timeframes and data page for more information about these `ticker.*()` functions.
Additional variables in the `session` namespace hold “series bool” values that indicate the current market state or track the first and last bars in named sessions:
              

The following example demonstrates the behavior of these variables. The script below calculates and plots the total volume for each subsession on an intraday chart that includes extended or overnight sessions. The script declares four persistent variables to store the total volume for regular, pre-market, post-market, and overnight hours. Then, inside the if structure, it uses session.ismarket, session.ispremarket, and session.ispostmarket as conditions for resetting or incrementing the value of each variable based on the current session state. The script also uses one of the `session.isfirstbar*` or `session.islastbar*` variables, depending on the selected inputs, as a condition to color the background of specific session bars. Additionally, the script checks the value of the syminfo.session variable to confirm that these calculations are compatible with the chart. It raises a custom _runtime error_ if the value is not `"extended"` or `"24h"`, indicating that the chart is day-based or does not use the “Extended” or “24 hour” session setting:
!image
Pine Script®
Copied
`//@version=6  
indicator("`syminfo.session` and `session.*` demo", format = format.volume)  
  
// Create inputs for highlighting the first or last bar in a given session type.  
string firstLastInput  = input.string("First", "Highlight", ["First", "Last"], inline = "0")  
string regularExtendInput = input.string(  
    "Regular Session", "Bar In ", ["Regular Session", "Extended/Overnight Hours"], inline = "0"  
)  
  
// Raise an error if the current chart does not use an "Extended" or "24 hour" session.  
if not (syminfo.session == session.extended or syminfo.session == "24h")  
    runtime.error("Open an intraday chart with an 'Extended' or '24 hour' session to use this script.")  
  
// Declare persistent variables to store the total volume for regular, pre-market, post-market, and overnight hours.  
var float regularTotal    = 0.0  
var float premarketTotal  = 0.0  
var float postmarketTotal = 0.0  
var float overnightTotal  = 0.0  
  
// For each session, accumulate the current session's total and reset the previous session's total to 0.  
if session.ismarket  
    regularTotal += volume  
    premarketTotal := 0.0  
else if session.ispremarket  
    premarketTotal += volume  
    postmarketTotal := 0.0  
    overnightTotal := 0.0  
else if session.ispostmarket  
    postmarketTotal += volume  
    regularTotal := 0.0  
else  
    overnightTotal += volume  
    postmarketTotal := 0.0  
  
//@variable Is `true` for the first or last bar in the specified session type, and `false` for all others.   
bool highlightBar = if firstLastInput == "First"  
    regularExtendInput == "Regular Session" ? session.isfirstbar_regular : session.isfirstbar  
else  
    regularExtendInput == "Regular Session" ? session.islastbar_regular : session.islastbar  
  
// Plot the total volume for each session.   
plot(regularTotal    == 0 ? na : regularTotal,    "Regular total volume",     #ff623b, style = plot.style_areabr)  
plot(premarketTotal  == 0 ? na : premarketTotal,  "Pre-market total volume",  #ff9800, style = plot.style_areabr)  
plot(postmarketTotal == 0 ? na : postmarketTotal, "Post-market total volume", #2962ff, style = plot.style_areabr)  
plot(overnightTotal  == 0 ? na : overnightTotal,  "Overnight total volume",   #d500f9, style = plot.style_areabr)  
  
// Highlight the background of the specified first/last bar in gray.  
bgcolor(highlightBar ? #787b8680 : na, title = "First/Last bar highlight")  
`
Refer to the Sessions page to learn more about market sessions and the session-related built-ins.

## Symbol information
The built-in variables in the `syminfo` namespace hold essential information about the chart’s symbol and the underlying instrument. Most of these variables, excluding syminfo.main_tickerid, can also represent information relating to a requested dataset if a script uses them as the `expression` argument in a `request.*()` function call. Most `syminfo.*` variables have the “simple” type qualifier, because their values do not change after the first bar. However, the variables relating to analyst recommendations and targets have the “series” qualifier, because they store dynamic data that can change over time.
The available `syminfo.*` variables include the following:
                                                                                

The example script below displays a table containing a simple summary of symbol and instrument information from the chart. On the first bar, the script creates two “string” arrays using the array.from function. The first array contains titles for the table’s first column. The second array contains corresponding strings from multiple `syminfo.*` variables for the second column. The script iterates through the arrays and populates the cells on each table row within a for loop:
!image
Pine Script®
Copied
`//@version=6  
indicator("`syminfo.*` variables demo", overlay = true, behind_chart = false)  
  
if barstate.isfirst  
    //@variable References a `table` object that displays symbol and instrument information on the chart.  
    table displayTable = table.new(position.middle_right, 2, 9, border_color = chart.fg_color, border_width = 1)  
    //@variable References an array of "string" titles for the table's first column.  
    array<string> titles = array.from(  
        "Ticker ID", "Symbol", "Prefix", "Type", "Description", "ISIN",   
        "Currency", "Tick size", "Point value"  
    )  
    //@variable References an array of "string" representations of `syminfo.*` values for the second column.  
    array<string> values = array.from(  
        syminfo.tickerid, syminfo.ticker, syminfo.prefix, syminfo.type, syminfo.description, syminfo.isin,   
        syminfo.currency, str.tostring(syminfo.mintick), str.tostring(syminfo.pointvalue)  
    )  
    // Loop through the arrays and populate the rows with the corresponding `titles` and `values` elements.   
    for i = 0 to 8  
        displayTable.cell(0, i, titles.get(i), text_color = chart.fg_color)  
        displayTable.cell(1, i, values.get(i), text_color = chart.fg_color)  
`
Note that:
  * The script initializes and populates the table only on the _first_ bar because the values of the `syminfo.*` variables used in the code do not change from bar to bar. After the script creates the table and sets its cells on the first bar, the table’s output persists on the right side of the chart.
  * The script uses the chart.fg_color variable to set the color of the table’s borders and text. The variable’s value changes based on the color of the chart’s _background_. See the Chart type and color section below for more information.

## Time series information
Two built-in variables store information about the _bar indices_ in the time series for the current chart, or for a requested dataset if used in the `expression` argument of a `request.*()` function call:
    

Several variables in the `barstate` namespace hold “series bool” values to indicate the _states_ of each bar in the chart’s dataset or a requested dataset. These variables include the following:
              

Refer to the Bar states page to learn more about these variables and how they work. For detailed information about how scripts execute across historical and realtime bars, and how they manage data in the time series based on bar states, refer to the Execution model page.
The following example calculates a volume-weighted average price (VWAP) over periods spanning a specified number of bars. The script resets the VWAP calculation on each bar whose bar_index value is divisible by the specified period. For instance, with the default input value of 100, the calculation resets on bar 0, 100, 200, and so on. The script plots the VWAP series and highlights the background of each bar on which the reset occurs. Additionally, the script uses the bar_index, last_bar_index, and barstate.ishistory variables to calculate the total number of historical bars, realtime bars, and completed periods, then displays the results in a single-cell table on the last bar:
!image
Pine Script®
Copied
`//@version=6  
indicator("`*bar_index` and `barstate.*` demo", overlay = true, behind_chart = false)  
  
//@variable The total number of bars in each VWAP calculation.  
int periodInput = input.int(100, "VWAP period", 2)  
  
//@variable Is `true` once every `periodInput` bars, starting from bar 0, and `false` otherwise.   
bool resetVWAP = bar_index % periodInput == 0  
//@variable The VWAP for the current period. The calculation resets each time the specified number of bars elapses.  
float vwap = ta.vwap(hlc3, resetVWAP)  
  
// This `if` structure's scope executes on the last bar.  
// The condition `bar_index == last_bar_index` is equivalent to `barstate.islast`.  
if bar_index == last_bar_index  
    //@variable References a single-cell table that displays bar and period information in the top-right corner.  
    var table infoTable = table.new(position.top_right, 1, 1)  
    //@variable The initial total bars if the last bar is historical, and one less than the total otherwise.  
    var int historicalBars = barstate.ishistory ? bar_index + 1 : bar_index  
    //@variable A formatted string containing bar and VWAP period information.  
    string displayText = str.format(  
        "Historical bars: {0}\nRealtime bars: {1}\nVWAP period: {2} bars\nComplete periods on chart: {3}",   
        historicalBars, bar_index + 1 - historicalBars, periodInput, int(bar_index / periodInput)  
    )  
    // Display the text from the `displayText` string in the table's cell.  
    infoTable.cell(0, 0, displayText, text_color = #000000, bgcolor = #2196f3)  
  
// Plot the `vwap` series and highlight the background on each calculation reset.  
plot(vwap, "Periodic VWAP", linewidth = 3)  
bgcolor(resetVWAP ? #ff98004d : na, title = "VWAP reset highlight")  
`
Note that:
  * On the first bar where the bar_index and last_bar_index values are equal, the script checks the value of the barstate.ishistory variable to determine whether that bar is historical. If the value is `true`, the total number of historical bars is one greater than the bar index on that bar. Otherwise, the number of historical bars equals the bar index. As new bars become available, the script counts the number of realtime bars by subtracting the historical total from the value of `bar_index + 1`.
  * The script counts the total number of completed VWAP periods by dividing the latest bar_index value by the input period, then rounding the result down to the nearest integer.


Pine Script also features several built-in variables that access _time_ information for the bars on the chart or a requested dataset:
  * The time and time_close variables hold UNIX timestamps representing the current bar’s opening and closing times, respectively.
  * The last_bar_time variable stores a UNIX timestamp representing the opening time of the last available bar.
  * The time_tradingday variable holds a UNIX timestamp representing the starting time of the trading day to which the current bar belongs.
  * The timenow variable stores the UNIX timestamp of the script’s latest execution.
  * The year, month, weekofyear, dayofmonth, dayofweek, hour, minute, and second variables store calendar-based values derived from the current bar’s opening time. The values are expressed in the exchange time zone.
  * The chart.left_visible_bar_time and chart.right_visible_bar_time variables store UNIX timestamps representing the opening times of the leftmost and rightmost visible chart bars.


Refer to the Time page for detailed information about these variables and examples of how they work.

## Chart type and color
Multiple built-in variables in the `chart` namespace hold “simple bool” values to indicate the type of chart on which the script runs. These variables can also indicate a requested chart dataset’s type when used in the `expression` argument of a `request.*()` function call:
              

These `chart.is_*` variables are typically useful when a script’s logic must respond differently on non-standard charts. For example, the following script demonstrates a simple strategy that places market orders to enter trades based on the crossing of two moving averages. On a non-standard chart, these orders can generate _misleading_ results, because Pine’s broker emulator fills them at the chart’s _calculated_ prices rather than using the instrument’s actual prices. To prevent such results, the script allows orders only on standard chart types by using chart.is_standard in the conditions that control the strategy.entry() commands. As shown below, if the script runs on a non-standard chart, it does not generate any orders or display performance data in the strategy report:
!image
Pine Script®
Copied
`//@version=6  
strategy("`chart.is_standard` demo", overlay = true, behind_chart = false)  
  
// Calculate two moving averages for the cross signal.  
float ma1 = ta.sma(close, 10)  
float ma2 = ta.sma(close, 20)  
  
if chart.is_standard  
    // This logic executes only on standard charts, preventing misleading trade data on non-standard charts.   
  
    // Close any short position and open a new long position if the first MA crosses over the second MA.  
    if ta.crossover(ma1, ma2)  
        strategy.entry("Buy", strategy.long)  
    // Close any long position and open a new short position if the first MA crosses under the second MA.  
    if ta.crossunder(ma1, ma2)  
        strategy.entry("Sell", strategy.short)  
  
// Plot the moving averages on the chart.  
plot(ma1, "Fast MA", color.orange, 2)  
plot(ma2, "Slow MA", color.blue, 3)  
  
// Color the background translucent red if the chart is not a standard type.  
bgcolor(not chart.is_standard ? color.new(color.red, 60) : na, title = "Non-standard chart highlight")  
`
Note that:
  * An alternative way to avoid misleading trade prices on _Heikin Ashi_ charts is to include `fill_orders_on_standard_ohlc = true` in the strategy() declaration statement. This argument configures the broker emulator to fill orders using _standard_ chart prices by default. See the Strategies page to learn more about strategy scripts.


The `chart` namespace also features the following variables that store “input color” values based on the background color defined in the chart’s settings:
    

The following script creates a single-cell table to indicate whether the chart’s background is light or dark, based on the value of chart.fg_color. If the value is `#0f0f0f`, the table’s text states that the background is considered light. Otherwise, it states that the background is considered dark. The script colors the table’s background using the foreground color, and it sets the text color using the value of chart.bg_color. The script also sets the table’s frame color using the middle value of a gradient from the background color to the foreground color:
!image
Pine Script®
Copied
`//@version=6  
indicator("`chart.bg_color` and `chart.fg_color` demo")  
  
if barstate.isfirst  
    //@variable The color from the midpoint of a gradient using the chart's background and foreground colors.  
    color middleColor = color.from_gradient(0.5, 0, 1, chart.bg_color, chart.fg_color)  
    //@variable References a table with `chart.fg_color` as the background color and `middleColor` as the frame color.  
    table displayTable = table.new(position.middle_center, 1, 1, chart.fg_color, middleColor, 2)  
  
    //@variable Is `true` if the chart's foreground color is `#0f0f0f`, indicating a light background.  
    bool isLight = chart.fg_color == #0f0f0f  
    //@variable A string indicating whether the chart's background is considered light or dark.  
    string displayText = "The chart's background is considered " + (isLight ? "light." : "dark.")  
    // Initialize the table's cell to display the string's text colored using the chart's background color.   
    displayTable.cell(0, 0, displayText, text_color = chart.bg_color, text_size = 30)  
`
 Previous Bar states    Next Inputs